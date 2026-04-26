from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .alias_data import CHARACTER_ALIASES
from .wiki_service import get_char_wiki_data

WEEK_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
MATERIAL_DAYS = {
    "自由": [0, 3, 6], "抗争": [1, 4, 6], "诗文": [2, 5, 6],
    "繁荣": [0, 3, 6], "勤劳": [1, 4, 6], "黄金": [2, 5, 6],
    "浮世": [0, 3, 6], "风雅": [1, 4, 6], "天光": [2, 5, 6],
    "诤言": [0, 3, 6], "巧思": [1, 4, 6], "笃行": [2, 5, 6],
    "公平": [0, 3, 6], "正义": [1, 4, 6], "秩序": [2, 5, 6],
    "角逐": [0, 3, 6], "焚燔": [1, 4, 6], "纷争": [2, 5, 6],
}


def target_weekday(query: str = "") -> int:
    text = query or ""
    today = datetime.now()
    if "周天" in text or "星期天" in text:
        return 6
    if "明" in text:
        return (today + timedelta(days=1)).weekday()
    if "后" in text:
        return (today + timedelta(days=2)).weekday()
    for idx, word in enumerate(WEEK_CN):
        if word in text or word[-1] in text and "周" in text:
            return idx
    return today.weekday()


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
    rows = [{"material": key, "characters": value[:18], "count": len(value)} for key, value in sorted(groups.items())]
    return {
        "weekday": weekday,
        "weekday_name": WEEK_CN[weekday],
        "query": query,
        "all_open": weekday == 6,
        "rows": rows,
        "unknown_count": len(unknown),
        "message": "周日全部天赋素材均开放" if weekday == 6 else "按角色天赋书聚合",
    }