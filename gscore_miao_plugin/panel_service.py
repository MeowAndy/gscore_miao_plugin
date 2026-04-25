from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .config import MiaoConfig
from .panel_models import PanelResult, PanelSourceError
from .panel_sources import get_source_order, get_source_with_context


def _avatar_count(result: PanelResult) -> int:
    avatars = result.avatars or []
    return len(avatars)


def _render_characters(result: PanelResult) -> List[str]:
    characters = result.characters or []
    if not characters:
        return []

    lines = ["", "角色详情："]
    for index, char in enumerate(characters[:8], start=1):
        avatar_id = char.get("avatar_id") or "未知角色"
        level = char.get("level") or "?"
        cons = char.get("constellation")
        friendship = char.get("friendship")
        skill_levels = "/".join([str(x) for x in char.get("skill_levels") or []]) or "-"
        weapon = char.get("weapon") or {}
        weapon_name = weapon.get("name") or "未知武器"
        weapon_level = weapon.get("level") or "?"
        reliq_count = len(char.get("reliquaries") or [])
        fight_props = char.get("fight_props") or {}
        crit = fight_props.get("暴击率")
        crit_dmg = fight_props.get("暴击伤害")
        recharge = fight_props.get("充能效率")

        summary = f"{index}. ID {avatar_id} Lv.{level}"
        if cons is not None:
            summary += f" C{cons}"
        if friendship:
            summary += f" 好感{friendship}"
        summary += f" | 天赋 {skill_levels}"
        summary += f" | 武器 {weapon_name} Lv.{weapon_level}"
        summary += f" | 圣遗物 {reliq_count}/5"
        if crit is not None and crit_dmg is not None:
            summary += f" | 双暴 {crit}%/{crit_dmg}%"
        if recharge is not None:
            summary += f" | 充能 {recharge}%"
        lines.append(summary)

    if len(characters) > 8:
        lines.append(f"……其余 {len(characters) - 8} 个角色已省略")
    return lines


def render_panel_text(result: PanelResult) -> str:
    lines = [
        "【喵喵面板】",
        f"UID：{result.uid}",
        f"数据源：{result.source}",
    ]
    if result.nickname:
        lines.append(f"昵称：{result.nickname}")
    if result.level is not None:
        lines.append(f"等级：{result.level}")
    if result.signature:
        lines.append(f"签名：{result.signature}")
    lines.append(f"公开角色数：{_avatar_count(result)}")
    lines.extend(_render_characters(result))
    return "\n".join(lines)


async def query_panel(uid: str, user_source: str, user_cfg: Dict[str, Any] | None = None) -> Tuple[PanelResult | None, List[str]]:
    errors: List[str] = []
    fallback = bool(MiaoConfig.get_config("EnablePanelFallback").data)
    user_cfg = user_cfg or {}

    for source_name in get_source_order(user_source):
        try:
            return await get_source_with_context(source_name, user_cfg).fetch(uid), errors
        except PanelSourceError as e:
            errors.append(f"{e.source}: {e.message}")
            if not fallback:
                break
        except Exception as e:
            errors.append(f"{source_name}: {e}")
            if not fallback:
                break

    return None, errors
