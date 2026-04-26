from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .alias_data import CHARACTER_ALIASES
from .wiki_service import get_char_wiki_data

WEEK_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
CITY_NAMES = ["蒙德", "璃月", "稻妻", "须弥", "枫丹", "纳塔", "挪德卡莱"]
TALENT_DAILY = {
    1: ["自由", "繁荣", "浮世", "诤言", "公平", "角逐", "月光"],
    2: ["抗争", "勤劳", "风雅", "巧思", "正义", "焚燔", "乐园"],
    3: ["诗文", "黄金", "天光", "笃行", "秩序", "纷争", "浪迹"],
}
WEAPON_DAILY = {
    1: ["高塔孤王", "孤云寒林", "远海夷地", "谧林涓露", "悠古弦音", "贡祭炽心", "奇巧秘器"],
    2: ["凛风奔狼", "雾海云间", "鸣神御灵", "绿洲花园", "纯圣露滴", "谵妄圣主", "长夜燧火"],
    3: ["狮牙斗士", "漆黑陨铁", "今昔剧画", "烈日威权", "无垢之海", "神合秘烟", "终北遗嗣"],
}
MATERIAL_DAYS = {
    name: [group - 1, group + 2, 6]
    for group, names in TALENT_DAILY.items()
    for name in names
}
TALENT_ICON_LEVELS = ("教导", "指引", "哲学")


def target_weekday(query: str = "") -> int:
    text = query or ""
    today = datetime.now()
    if today.hour < 4:
        today -= timedelta(days=1)
    if "周天" in text or "星期天" in text:
        return 6
    if "明" in text:
        return (today + timedelta(days=1)).weekday()
    if "后" in text:
        return (today + timedelta(days=2)).weekday()
    digit = re.search(r"周([1-7])", text)
    if digit:
        return int(digit.group(1)) - 1
    for idx, word in enumerate(WEEK_CN):
        if word in text or word[-1] in text and "周" in text:
            return idx
    return today.weekday()


def _daily_group(weekday: int) -> int:
    return weekday % 3 + 1


def _talent_icons(name: str) -> List[str]:
    return [f"meta-gs/material/talent/「{name}」的{level}.webp" for level in TALENT_ICON_LEVELS]


def _weapon_icon_prefix(name: str) -> str:
    return f"meta-gs/material/weapon/{name}"


def _build_public_rows(weekday: int, groups: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    if weekday == 6:
        return []
    group_ids = (_daily_group(weekday),)
    rows: List[Dict[str, Any]] = []
    for type_name, data in (("talent", TALENT_DAILY), ("weapon", WEAPON_DAILY)):
        for group in group_ids:
            for idx, material in enumerate(data[group]):
                row: Dict[str, Any] = {
                    "type": type_name,
                    "group": group,
                    "material": material,
                    "city": CITY_NAMES[idx] if idx < len(CITY_NAMES) else "提瓦特",
                    "characters": groups.get(material, [])[:18],
                    "count": len(groups.get(material, [])),
                }
                if type_name == "talent":
                    row["icons"] = _talent_icons(material)
                else:
                    row["icon_prefix"] = _weapon_icon_prefix(material)
                    row["icons"] = []
                rows.append(row)
    return rows


def _material_text(data: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("talent", "talentMat", "talent_material", "materials", "mat", "素材"):
        value = data.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(x) for x in value)
        elif isinstance(value, dict):
            parts.extend(str(x) for x in value.values())
    return " ".join(parts)


def _match_book(text: str) -> str:
    for name in MATERIAL_DAYS:
        if name in text:
            return name
    match = re.search(r"(自由|抗争|诗文|繁荣|勤劳|黄金|浮世|风雅|天光|诤言|巧思|笃行|公平|正义|秩序|角逐|焚燔|纷争)", text)
    return match.group(1) if match else "未知"


def build_today_material(query: str = "") -> Dict[str, Any]:
    weekday = target_weekday(query)
    groups: Dict[str, List[str]] = defaultdict(list)
    unknown: List[str] = []
    for name in sorted(CHARACTER_ALIASES.keys()):
        try:
            data = get_char_wiki_data(name, "gs") or {}
        except Exception:
            data = {}
        book = _match_book(_material_text(data))
        if book == "未知":
            unknown.append(name)
            continue
        if weekday in MATERIAL_DAYS.get(book, []):
            groups[book].append(name)
    rows = _build_public_rows(weekday, groups)
    return {
        "weekday": weekday,
        "weekday_name": WEEK_CN[weekday],
        "query": query,
        "all_open": weekday == 6,
        "rows": rows,
        "unknown_count": len(unknown),
        "message": "周日全部天赋/武器素材均开放" if weekday == 6 else "按 miao-plugin 每日材料轮换展示",
    }