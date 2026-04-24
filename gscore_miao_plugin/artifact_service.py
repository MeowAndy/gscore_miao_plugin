from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .panel_models import PanelResult

MAIN_PROP_WEIGHT = 1.0
CRIT_RATE_WEIGHT = 2.0
CRIT_DMG_WEIGHT = 1.0
ATK_PERCENT_WEIGHT = 1.3
ER_WEIGHT = 1.1
EM_WEIGHT = 0.35


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _prop_score(prop_id: Any) -> float:
    prop = str(prop_id or "").upper()
    if "CRITICAL" in prop or "CRIT" in prop:
        if "HURT" in prop or "DMG" in prop:
            return 7.8 * CRIT_DMG_WEIGHT
        return 3.9 * CRIT_RATE_WEIGHT
    if "ATTACK_PERCENT" in prop or "ATK_PERCENT" in prop:
        return 5.8 * ATK_PERCENT_WEIGHT
    if "CHARGE" in prop or "RECHARGE" in prop:
        return 6.5 * ER_WEIGHT
    if "MASTERY" in prop or "ELEMENT_MASTERY" in prop:
        return 19.8 * EM_WEIGHT
    if "DAMAGE" in prop or "ADD_HURT" in prop:
        return 7.0 * MAIN_PROP_WEIGHT
    return 2.5


def score_reliquary(reliq: Dict[str, Any]) -> float:
    score = 0.0
    score += _prop_score(reliq.get("main_prop")) * 0.35
    for prop in reliq.get("sub_props") or []:
        if isinstance(prop, dict):
            score += _as_float(prop.get("score"), _prop_score(prop.get("appendPropId") or prop.get("prop_id")))
        else:
            score += _prop_score(prop)
    rarity = _as_float(reliq.get("rarity"), 5)
    level = _as_float(reliq.get("level"), 1)
    score *= 1 + max(rarity - 4, 0) * 0.05
    score *= min(max(level, 1), 21) / 21
    return round(score, 1)


def character_artifact_score(char: Dict[str, Any]) -> Tuple[float, List[float]]:
    scores = [score_reliquary(x) for x in char.get("reliquaries") or [] if isinstance(x, dict)]
    return round(sum(scores), 1), scores


def artifact_rank(score: float) -> str:
    if score >= 220:
        return "ACE"
    if score >= 180:
        return "SS"
    if score >= 140:
        return "S"
    if score >= 100:
        return "A"
    if score >= 60:
        return "B"
    return "C"


def render_artifact_text(result: PanelResult, character_query: str = "") -> str:
    characters = result.characters or []
    if character_query:
        q = character_query.lower()
        characters = [
            c for c in characters
            if q in str(c.get("name") or c.get("avatar_name") or c.get("avatar_id") or "").lower()
        ] or characters[:1]

    lines = ["【喵喵圣遗物评分】", f"UID：{result.uid}", f"数据源：{result.source}"]
    if not characters:
        lines.append("当前数据源没有返回圣遗物详情。建议使用 Enka 且公开角色展柜。")
        return "\n".join(lines)

    for index, char in enumerate(characters[:8], start=1):
        name = char.get("name") or char.get("avatar_name") or f"角色ID {char.get('avatar_id') or '?'}"
        total, scores = character_artifact_score(char)
        detail = " / ".join(str(x) for x in scores) if scores else "无圣遗物"
        lines.append(f"{index}. {name}：{total} 分 [{artifact_rank(total)}] | {detail}")
    lines.append("评分为首版启发式算法，后续会继续按 miao-plugin 权重细化。")
    return "\n".join(lines)