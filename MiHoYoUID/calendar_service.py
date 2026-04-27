from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import httpx

from .config import MiaoConfig

_IGNORE_RE = re.compile(
    r"更新概览|游戏优化|优化说明|内容专题页|专题展示页|版本更新说明|调研|防沉迷|米游社|专项意见|"
    r"更新修复与优化|问卷调查|版本更新通知|更新时间说明|预下载功能|周边限时|周边上新|"
    r"角色演示|角色PV|版本PV|动画短片|bilibili|激励计划|调整说明|攻略征集|测试招募"
)


def _timeout() -> float:
    return float(MiaoConfig.get_config("PanelRequestTimeout").data or 15)


def _parse_time(text: Any) -> datetime | None:
    if isinstance(text, (int, float)):
        try:
            return datetime.fromtimestamp(int(text))
        except Exception:
            return None
    value = str(text or "").strip().replace("/", "-")
    if not value:
        return None
    for fmt, length in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(value[:length], fmt)
        except Exception:
            continue
    return None


def _date_range(days_before: int = 7, days_after: int = 13) -> Tuple[datetime, datetime]:
    now = datetime.now()
    start = datetime(now.year, now.month, now.day) - timedelta(days=days_before)
    end = datetime(now.year, now.month, now.day, 23, 59, 59) + timedelta(days=days_after)
    return start, end


def _headers() -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": "https://webstatic.mihoyo.com",
        "Referer": "https://webstatic.mihoyo.com/",
    }


def _flatten_announcements(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = raw.get("data") or {}
    result: List[Dict[str, Any]] = []
    for block in data.get("list") or []:
        for item in block.get("list") or []:
            if isinstance(item, dict):
                result.append(item)
    for pic_block in data.get("pic_list") or []:
        for item in pic_block.get("list") or []:
            if isinstance(item, dict):
                result.append(item)
        for type_block in pic_block.get("type_list") or []:
            for item in type_block.get("list") or []:
                if isinstance(item, dict):
                    result.append(item)
    return result


def _type_for_title(title: str, game: str) -> str:
    if game == "sr":
        if "流光定影" in title or "光锥" in title:
            return "光锥跃迁"
        if "活动跃迁" in title or "角色跃迁" in title:
            return "角色跃迁"
        if "无名勋礼" in title:
            return "无名勋礼"
        return "活动"
    if "概率UP" in title or "祈愿" in title:
        if any(word in title for word in ("单手剑", "双手剑", "长柄武器", "弓", "法器", "神铸赋形")):
            return "武器祈愿"
        return "角色祈愿"
    if "纪行" in title:
        return "纪行"
    return "活动"


def _clean_title(title: str) -> str:
    title = re.sub(r"<[^>]+>", "", title or "")
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _build_items(raw: Dict[str, Any], game: str, list_mode: bool) -> List[Dict[str, Any]]:
    start_range, end_range = _date_range()
    now = datetime.now()
    seen: set[str] = set()
    items: List[Dict[str, Any]] = []
    for ann in _flatten_announcements(raw):
        ann_id = str(ann.get("ann_id") or ann.get("id") or "")
        title = _clean_title(str(ann.get("title") or ""))
        if not title or ann_id in seen or _IGNORE_RE.search(title):
            continue
        seen.add(ann_id)
        start = _parse_time(ann.get("start_time"))
        end = _parse_time(ann.get("end_time"))
        if not start or not end or start > end_range or end < start_range:
            continue
        status = "进行中" if start <= now <= end else "未开始" if now < start else "已结束"
        if not list_mode and status == "已结束":
            continue
        item_type = _type_for_title(title, game)
        items.append(
            {
                "title": title,
                "type": item_type,
                "status": status,
                "start": start,
                "end": end,
                "left_days": max((end - now).days, 0),
            }
        )
    priority = {"角色跃迁": 0, "角色祈愿": 0, "光锥跃迁": 1, "武器祈愿": 1, "活动": 2, "纪行": 3, "无名勋礼": 3}
    items.sort(key=lambda x: (priority.get(str(x["type"]), 9), x["start"], x["end"]))
    return items


async def fetch_calendar(game: str = "sr", list_mode: bool = False) -> Dict[str, Any]:
    game = "gs" if game in {"gs", "genshin", "原神"} else "sr"
    if game == "gs":
        url = str(MiaoConfig.get_config("GenshinCalendarApiUrl").data or "").strip()
        params = {
            "game": "hk4e",
            "game_biz": "hk4e_cn",
            "lang": "zh-cn",
            "bundle_id": "hk4e_cn",
            "platform": "pc",
            "region": "cn_gf01",
            "level": "55",
            "uid": "100000000",
        }
    else:
        url = str(MiaoConfig.get_config("StarRailCalendarApiUrl").data or "").strip()
        params = {
            "game": "hkrpg",
            "game_biz": "hkrpg_cn",
            "lang": "zh-cn",
            "auth_appid": "announcement",
            "authkey_ver": "1",
            "bundle_id": "hkrpg_cn",
            "channel_id": "1",
            "level": "65",
            "platform": "pc",
            "region": "prod_gf_cn",
            "sdk_presentation_style": "fullscreen",
            "sdk_screen_transparent": "true",
            "sign_type": "2",
            "uid": "100000000",
        }
    async with httpx.AsyncClient(timeout=_timeout(), follow_redirects=True) as client:
        resp = await client.get(url, params=params, headers=_headers())
        resp.raise_for_status()
        raw = resp.json()
    if raw.get("retcode") not in (0, "0"):
        raise RuntimeError(str(raw.get("message") or raw.get("msg") or f"公告接口返回异常：{raw.get('retcode')}"))
    return {"game": game, "items": _build_items(raw, game, list_mode), "list_mode": list_mode}
