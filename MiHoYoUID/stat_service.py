from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

from .config import MiaoConfig
from .path import MAIN_PATH

STAT_CACHE_DIR = MAIN_PATH / "cache" / "stat"
STAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_VERSION = 5
COMMON_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
ABYSS_RANK_NAMES = {"S+", "S", "A", "B", "C"}

URLS = {
    "cons": "https://api.lelaer.com/ys/getRoleAvg.php?star=all&lang=zh-Hans",
    "cons_dist": "https://api.lelaer.com/ys/getRoleAvg.php?star=all&lang=zh-Hans",
    "cons5": "https://api.lelaer.com/ys/getRoleAvg.php?star=all&lang=zh-Hans",
    "abyss": "https://api.yshelper.com/ys/getAbyssRank.php?star=all&role=all&lang=zh-Hans",
    "abyss_use": "https://api.yshelper.com/ys/getAbyssRank.php?star=all&role=all&lang=zh-Hans",
    "abyss_own": "https://api.yshelper.com/ys/getAbyssRank.php?star=all&role=all&lang=zh-Hans",
    "abyss_summary": "https://api.yshelper.com/ys/getAbyssRank.php?star=all&role=all&lang=zh-Hans",
    "hard": "https://api.lelaer.com/ys/getAbyssRank2.php?star=all&role=all&lang=zh-Hans",
    "hard_use": "https://api.lelaer.com/ys/getAbyssRank2.php?star=all&role=all&lang=zh-Hans",
    "hard_own": "https://api.lelaer.com/ys/getAbyssRank2.php?star=all&role=all&lang=zh-Hans",
    "hard_summary": "https://api.lelaer.com/ys/getAbyssRank2.php?star=all&role=all&lang=zh-Hans",
    "team": "https://api.yshelper.com/ys/getAbyssRank.php?star=all&role=all&lang=zh-Hans",
    "role_combat": "",
}


def _timeout() -> float:
    return float(MiaoConfig.get_config("PanelRequestTimeout").data or 15)


def _cache_path(kind: str) -> Path:
    return STAT_CACHE_DIR / f"{kind}.json"


def _read_cache(kind: str, ttl: int = 3600) -> Dict[str, Any] | None:
    path = _cache_path(kind)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(data.get("ts") or 0) <= ttl:
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else data
            if isinstance(payload, dict) and payload.get("cache_version") == CACHE_VERSION:
                return payload
    except Exception:
        return None
    return None


def _write_cache(kind: str, payload: Dict[str, Any]) -> None:
    try:
        _cache_path(kind).write_text(json.dumps({"ts": time.time(), "payload": payload}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        return


def _unwrap(raw: Any) -> Any:
    if isinstance(raw, dict):
        for key in ("data", "list", "result"):
            value = raw.get(key)
            if isinstance(value, (dict, list)):
                return value
    return raw


def _loads_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


async def _fetch_json(client: httpx.AsyncClient, url: str) -> Any:
    resp = await client.get(url, headers={"User-Agent": COMMON_UA})
    resp.raise_for_status()
    return _loads_json(resp.text)


async def _fetch_cons_stat(client: httpx.AsyncClient) -> Dict[str, Any]:
    lelaer: Dict[str, Any] = {}
    lelaer_error = ""
    try:
        lelaer_raw = await _fetch_json(client, URLS["cons"])
        lelaer = lelaer_raw if isinstance(lelaer_raw, dict) else {}
    except Exception as e:
        lelaer_error = str(e)
    try:
        abyss_raw = await _fetch_json(client, URLS["abyss"])
        abyss = abyss_raw if isinstance(abyss_raw, dict) else {}
    except Exception as e:
        if lelaer_error:
            raise RuntimeError(f"Lelaer: {lelaer_error}; Yshelper: {e}") from e
        abyss = {}
    result = lelaer.get("result") if isinstance(lelaer.get("result"), list) else []
    has_list = abyss.get("has_list") if isinstance(abyss.get("has_list"), list) else []
    if not result and not has_list:
        msg = lelaer_error or "接口未返回 result/has_list"
        raise RuntimeError(msg)
    return {
        "result": result,
        "has_list": has_list,
        "last_update": lelaer.get("last_update") or abyss.get("last_update") or "",
        "top_own": abyss.get("top_own") or 0,
        "lelaer_error": lelaer_error,
    }


async def fetch_stat(kind: str, force: bool = False) -> Dict[str, Any]:
    kind = kind if kind in URLS else "abyss"
    if kind == "role_combat":
        return build_stat_placeholder(
            kind,
            "幻想真境剧诗数据在 miao-plugin 中为米游社 CK 个人数据接口，需要绑定 Cookie 后调用；当前仅公开深渊/幽境统计接口可直接展示。",
        )
    cached = None if force else _read_cache(kind)
    if cached:
        cached["cached"] = True
        return cached
    try:
        async with httpx.AsyncClient(timeout=_timeout(), follow_redirects=True) as client:
            raw = await _fetch_cons_stat(client) if kind in {"cons", "cons_dist", "cons5"} else await _fetch_json(client, URLS[kind])
    except Exception:
        cached = _read_cache(kind, ttl=86400 * 14)
        if cached:
            cached["cached"] = True
            return cached
        raise
    payload = {"kind": kind, "url": URLS[kind], "raw": raw if kind in {"cons", "cons_dist", "cons5"} else _unwrap(raw), "cached": False, "updated": int(time.time()), "cache_version": CACHE_VERSION}
    _write_cache(kind, payload)
    return payload


def _as_rows(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        for key in ("list", "data", "rank", "result", "avatars", "roles"):
            rows = value.get(key)
            if isinstance(rows, list):
                return [x for x in rows if isinstance(x, dict)]
        rows = []
        for key, item in value.items():
            if isinstance(item, dict):
                row = dict(item)
                row.setdefault("name", key)
                rows.append(row)
        return rows
    return []


def _score_value(value: Any) -> float:
    try:
        return float(str(value).strip().strip("%"))
    except (TypeError, ValueError):
        return 0.0


def _fmt_percent(value: Any) -> str:
    score = _score_value(value)
    return f"{score:.2f}%" if score else "-"


def _ratio_percent(value: Any) -> str:
    try:
        score = float(value) * 100
    except (TypeError, ValueError):
        return "-"
    return f"{score:.2f}%" if score else "-"


def _clean_name(value: Any) -> str:
    return "".join(str(value or "").split())


def _first_number(*values: Any) -> float:
    for value in values:
        try:
            if value in (None, "", "-"):
                continue
            return float(str(value).strip().strip("%"))
        except (TypeError, ValueError):
            continue
    return 0.0


def _extract_rank_groups(raw: Any) -> List[Dict[str, Any]]:
    result = raw.get("result") if isinstance(raw, dict) else []
    if not isinstance(result, list):
        return []
    groups: List[Dict[str, Any]] = []
    for block in result:
        if not isinstance(block, list):
            continue
        candidate = [x for x in block if isinstance(x, dict) and isinstance(x.get("list"), list)]
        if candidate and any(str(x.get("rank_name") or "") in ABYSS_RANK_NAMES for x in candidate):
            groups = candidate
            break
    return groups


def _normalize_abyss_rank_rows(payload: Dict[str, Any], limit: int, metric: str = "use_rate") -> Dict[str, Any]:
    raw = payload.get("raw")
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for group in _extract_rank_groups(raw):
        rank_name = str(group.get("rank_name") or "")
        for item in group.get("list") or []:
            if not isinstance(item, dict):
                continue
            name = _clean_name(item.get("name") or item.get("role") or item.get("title"))
            if not name or name in seen:
                continue
            seen.add(name)
            score = _first_number(item.get(metric), item.get("use_rate"))
            use_rate = _first_number(item.get("use_rate"))
            own_rate = _first_number(item.get("own_rate"))
            use = item.get("use") or item.get("count") or ""
            own = item.get("own") or ""
            detail_parts = [f"评级 {rank_name}" if rank_name else ""]
            if metric != "use_rate" and use_rate:
                detail_parts.append(f"使用率 {use_rate:.1f}%")
            if own_rate:
                detail_parts.append(f"持有率 {own_rate:.1f}%")
            if use not in (None, ""):
                detail_parts.append(f"出场 {use}")
            if own not in (None, ""):
                detail_parts.append(f"持有 {own}")
            out.append({
                "rank": len(out) + 1,
                "name": name,
                "rate": f"{score:.1f}%",
                "count": use,
                "cons": " · ".join(x for x in detail_parts if x),
                "score": score,
                "raw": item,
            })
    out.sort(key=lambda x: x["score"], reverse=True)
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return {**payload, "rows": out[:limit], "total_rows": len(out), "game": "gs"}


def _avatar_name_map(raw: Any) -> Dict[str, str]:
    rows = raw.get("has_list") if isinstance(raw, dict) else []
    ret: Dict[str, str] = {}
    if not isinstance(rows, list):
        return ret
    for item in rows:
        if not isinstance(item, dict):
            continue
        avatar = str(item.get("avatar") or "")
        name = _clean_name(item.get("name"))
        if avatar and name:
            ret[avatar] = name
    return ret


def _extract_team_rows(raw: Any) -> List[Dict[str, Any]]:
    result = raw.get("result") if isinstance(raw, dict) else []
    if not isinstance(result, list):
        return []
    for block in result:
        if not isinstance(block, list) or not block:
            continue
        first = block[0]
        if isinstance(first, dict) and isinstance(first.get("role"), list):
            return [x for x in block if isinstance(x, dict)]
    return []


def _normalize_team_rows(payload: Dict[str, Any], limit: int) -> Dict[str, Any]:
    raw = payload.get("raw")
    avatar_names = _avatar_name_map(raw)
    out: List[Dict[str, Any]] = []
    for idx, item in enumerate(_extract_team_rows(raw), start=1):
        names: List[str] = []
        for role in item.get("role") or []:
            if not isinstance(role, dict):
                continue
            name = _clean_name(role.get("name"))
            avatar = str(role.get("avatar") or "")
            names.append(name or avatar_names.get(avatar) or "未知角色")
        if not names:
            continue
        score = _first_number(item.get("attend_rate"), item.get("use_rate"), item.get("has_rate"))
        up = item.get("up_use_num") or item.get("up_use") or 0
        down = item.get("down_use_num") or item.get("down_use") or 0
        detail = f"上半 {up} · 下半 {down}"
        use_rate = _first_number(item.get("use_rate"))
        if use_rate:
            detail += f" · 使用率 {use_rate:.1f}%"
        has_rate = _first_number(item.get("has_rate"))
        if has_rate:
            detail += f" · 持有率 {has_rate:.1f}%"
        out.append({
            "rank": idx,
            "name": " / ".join(names),
            "rate": f"{score:.1f}%",
            "count": item.get("use") or "",
            "cons": detail,
            "score": score,
            "raw": item,
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return {**payload, "rows": out[:limit], "total_rows": len(out), "game": "gs"}


def _normalize_overview_rows(payload: Dict[str, Any], limit: int, name: str) -> Dict[str, Any]:
    raw = payload.get("raw") if isinstance(payload.get("raw"), dict) else {}
    rank_groups = _extract_rank_groups(raw)
    rank_summary = " / ".join(
        f"{group.get('rank_name')}级 {len(group.get('list') or [])}人"
        for group in rank_groups
        if group.get("rank_name")
    )
    role_count = sum(len(group.get("list") or []) for group in rank_groups)
    team_count = len(_extract_team_rows(raw))
    top_roles = []
    for group in rank_groups:
        for item in group.get("list") or []:
            if isinstance(item, dict) and item.get("name"):
                top_roles.append(f"{_clean_name(item.get('name'))} {_first_number(item.get('use_rate')):.1f}%")
            if len(top_roles) >= 5:
                break
        if len(top_roles) >= 5:
            break
    items = [
        ("有效样本", raw.get("top_own"), raw.get("tips")),
        ("满星率", raw.get("star36_rate"), "star36_rate"),
        ("一次满星率", raw.get("star36_once_rate"), "star36_once_rate"),
        ("平均重开次数", raw.get("restart_times_avg"), "restart_times_avg"),
        ("难度指数", raw.get("nandu"), "nandu"),
        ("角色统计", role_count, rank_summary),
        ("配队统计", team_count, "公开配队方案数量"),
        ("热门角色", len(top_roles), " / ".join(top_roles)),
        ("更新时间", raw.get("last_update"), raw.get("tips2") or name),
    ]
    rows: List[Dict[str, Any]] = []
    for idx, (row_name, value, detail) in enumerate(items, start=1):
        if value in (None, ""):
            continue
        rate = f"{_first_number(value):.1f}%" if "率" in row_name else str(value)
        rows.append({"rank": idx, "name": row_name, "rate": rate, "count": "", "cons": detail or name, "score": len(items) - idx, "raw": raw})
    if not rows and raw.get("tips"):
        rows.append({"rank": 1, "name": name, "rate": "-", "count": "", "cons": raw.get("tips"), "score": 1, "raw": raw})
    return {**payload, "rows": rows[:limit], "total_rows": len(rows), "game": "gs"}


def _normalize_cons_rows(payload: Dict[str, Any], limit: int, mode: str = "hold", con_num: int = -1) -> Dict[str, Any]:
    raw = payload.get("raw")
    has_rows = raw.get("has_list") if isinstance(raw, dict) else []
    has_map = {}
    if isinstance(has_rows, list):
        for item in has_rows:
            if isinstance(item, dict) and item.get("name"):
                has_map[_clean_name(item.get("name"))] = item.get("own_rate")

    rows = _as_rows(raw)
    if not rows and isinstance(has_rows, list):
        rows = [x for x in has_rows if isinstance(x, dict)]
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        name = row.get("role") or row.get("name") or row.get("title") or row.get("cn") or f"第{idx}项"
        name = _clean_name(name)
        if name.startswith(("http://", "https://")):
            name = f"第{idx}项"
        own_rate = row.get("own_rate") or row.get("holdingRate") or has_map.get(_clean_name(name))
        cons_values = []
        for con_idx in range(7):
            raw_value = row.get(f"c{con_idx}")
            try:
                value = float(raw_value or 0) / 100
            except (TypeError, ValueError):
                value = 0.0
            if mode == "hold":
                try:
                    value *= float(own_rate or 0) / 100
                except (TypeError, ValueError):
                    value = 0.0
            cons_values.append({"id": con_idx, "value": value, "rate": _ratio_percent(value)})
        avg_cons = row.get("avg_class") or row.get("avgCons") or row.get("cons") or ""
        count = row.get("role_sum") or row.get("count") or row.get("total") or ""
        score = cons_values[con_num]["value"] * 100 if 0 <= con_num <= 6 else _score_value(own_rate)
        if mode == "cons":
            rate = cons_values[con_num]["rate"] if 0 <= con_num <= 6 else _fmt_percent(own_rate)
            cons = " / ".join(item["rate"] for item in cons_values)
        else:
            rate = _fmt_percent(own_rate)
            cons = avg_cons
        out.append({"rank": idx, "name": name, "rate": rate, "count": count, "cons": cons, "cons_values": cons_values, "mode": mode, "con_num": con_num, "score": score, "raw": row})
    out.sort(key=lambda x: x["score"], reverse=True)
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return {**payload, "rows": out[:limit], "total_rows": len(out)}


def normalize_stat_rows(payload: Dict[str, Any], limit: int = 24) -> Dict[str, Any]:
    kind = payload.get("kind") or "abyss"
    if kind == "cons":
        return _normalize_cons_rows(payload, limit, "hold")
    if kind == "cons_dist":
        return _normalize_cons_rows(payload, limit, "cons")
    if kind == "cons5":
        return _normalize_cons_rows(payload, limit, "cons", 5)
    if kind in {"abyss", "abyss_use", "hard", "hard_use"}:
        return _normalize_abyss_rank_rows(payload, limit, "use_rate")
    if kind in {"abyss_own", "hard_own"}:
        return _normalize_abyss_rank_rows(payload, limit, "use_rate")
    if kind == "team":
        return _normalize_team_rows(payload, limit)
    if kind == "abyss_summary":
        return _normalize_overview_rows(payload, limit, "深渊数据")
    if kind == "hard_summary":
        return _normalize_overview_rows(payload, limit, "幽境危战数据")
    raw = payload.get("raw")
    rows = _as_rows(raw)
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        name = row.get("name") or row.get("avatar") or row.get("role") or row.get("title") or row.get("cn") or row.get("key") or f"第{idx}项"
        rate = row.get("rate") or row.get("value") or row.get("avg") or row.get("percent") or row.get("use") or row.get("usage") or row.get("持有率") or row.get("出场率")
        count = row.get("count") or row.get("total") or row.get("num") or row.get("sample") or ""
        cons = row.get("cons") or row.get("命座") or row.get("life") or ""
        score = _score_value(rate)
        out.append({"rank": idx, "name": str(name), "rate": rate, "count": count, "cons": cons, "score": score, "raw": row})
    out.sort(key=lambda x: x["score"], reverse=True)
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return {**payload, "rows": out[:limit], "total_rows": len(out)}


def build_stat_placeholder(kind: str, message: str) -> Dict[str, Any]:
    return {"kind": kind, "rows": [], "total_rows": 0, "message": message, "cached": False}