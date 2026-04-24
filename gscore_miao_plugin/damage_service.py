from __future__ import annotations

from typing import Any, Dict, List

from .panel_models import PanelResult


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def estimate_character_damage(char: Dict[str, Any]) -> Dict[str, float]:
    props = char.get("fight_props") or {}
    atk = _num(props.get("攻击力"), 1000)
    crit = _num(props.get("暴击率"), 5) / 100
    crit_dmg = _num(props.get("暴击伤害"), 50) / 100
    mastery = _num(props.get("元素精通"), 0)
    recharge = _num(props.get("充能效率"), 100)
    skill_levels = char.get("skill_levels") or []
    talent_factor = 1 + sum(_num(x, 1) for x in skill_levels[:3]) / 30
    crit_expect = 1 + min(max(crit, 0), 1) * max(crit_dmg, 0)
    reaction_bonus = 1 + mastery / (mastery + 1400) * 2.78 if mastery > 0 else 1
    recharge_bonus = 1 + max(recharge - 100, 0) / 1000
    normal = atk * 1.2 * talent_factor * crit_expect
    skill = atk * 2.4 * talent_factor * crit_expect * reaction_bonus
    burst = atk * 4.0 * talent_factor * crit_expect * reaction_bonus * recharge_bonus
    return {
        "normal": round(normal),
        "skill": round(skill),
        "burst": round(burst),
        "expect": round((normal + skill + burst) / 3),
    }


def render_damage_text(result: PanelResult, character_query: str = "") -> str:
    characters: List[Dict[str, Any]] = result.characters or []
    if character_query:
        q = character_query.lower()
        characters = [
            c for c in characters
            if q in str(c.get("name") or c.get("avatar_name") or c.get("avatar_id") or "").lower()
        ] or characters[:1]

    lines = ["【喵喵伤害估算】", f"UID：{result.uid}", f"数据源：{result.source}"]
    if not characters:
        lines.append("当前数据源没有返回可计算的角色详情。建议使用 Enka 且公开角色展柜。")
        return "\n".join(lines)

    for index, char in enumerate(characters[:8], start=1):
        name = char.get("name") or char.get("avatar_name") or f"角色ID {char.get('avatar_id') or '?'}"
        dmg = estimate_character_damage(char)
        lines.append(
            f"{index}. {name}：普攻 {dmg['normal']} / 战技 {dmg['skill']} / 爆发 {dmg['burst']} / 期望 {dmg['expect']}"
        )
    lines.append("当前为首版通用估算，不等同深度配队轴伤；后续会逐角色迁移 miao-plugin 计算模板。")
    return "\n".join(lines)