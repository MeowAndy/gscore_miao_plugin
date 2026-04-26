from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .config import MiaoConfig
from .panel_cache import get_latest_panel
from .panel_models import PanelResult, PanelSourceError
from .panel_sources import get_source_order, get_source_with_context


def _source_label(source: str) -> str:
    labels = {
        "miao": "Miao-Api",
        "enka": "Enka-Api",
        "mys": "米游社",
        "mgg": "MiniGG-Api",
        "hutao": "Hutao",
        "mihomo": "Mihomo",
        "avocado": "Avocado",
        "enkahsr": "EnkaHSR",
    }
    return labels.get(str(source or "").lower(), source or "未知")


def format_panel_query_errors(errors: List[str], source_order: List[str], game: str = "gs") -> str:
    if not errors:
        return "无可用数据源"
    lines = []
    if source_order:
        lines.append("已尝试：" + " -> ".join(_source_label(x) for x in source_order))
    for item in errors[:6]:
        lines.append(f"- {item}")
    if len(errors) > 6:
        lines.append(f"……其余 {len(errors) - 6} 个错误已省略")
    lines.append("建议：确认 UID 正确、游戏内展柜/角色详情已公开，并尝试切换面板服务为 auto。")
    if game == "sr":
        lines.append("星铁源推荐顺序：Mihomo / Avocado / EnkaHSR；米游社入口需要可用 Cookie。")
    else:
        lines.append("原神源推荐顺序：米游社 / Miao / Enka；Enka 需要公开展柜并等待缓存。")
    return "\n".join(lines)


def _avatar_count(result: PanelResult) -> int:
    avatars = result.avatars or []
    return len(avatars)


def _render_characters(result: PanelResult) -> List[str]:
    characters = result.characters or []
    if not characters:
        return []

    is_sr = result.game == "sr"
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
        summary += f" | {'行迹' if is_sr else '天赋'} {skill_levels}"
        summary += f" | {'光锥' if is_sr else '武器'} {weapon_name} Lv.{weapon_level}"
        summary += f" | {'遗器' if is_sr else '圣遗物'} {reliq_count}/{6 if is_sr else 5}"
        if crit is not None and crit_dmg is not None:
            summary += f" | 双暴 {crit}%/{crit_dmg}%"
        if recharge is not None:
            summary += f" | 充能 {recharge}%"
        lines.append(summary)

    if len(characters) > 8:
        lines.append(f"……其余 {len(characters) - 8} 个角色已省略")
    return lines


def render_panel_text(result: PanelResult) -> str:
    is_sr = result.game == "sr"
    lines = [
        "【喵喵崩铁面板】" if is_sr else "【喵喵原神面板】",
        f"UID：{result.uid}",
        f"数据源：{_source_label(result.source)}",
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


async def query_panel(
    uid: str,
    user_source: str,
    user_cfg: Dict[str, Any] | None = None,
    allow_fallback: bool | None = None,
    game: str = "gs",
) -> Tuple[PanelResult | None, List[str]]:
    errors: List[str] = []
    fallback = bool(MiaoConfig.get_config("EnablePanelFallback").data) if allow_fallback is None else allow_fallback
    user_cfg = user_cfg or {}
    game = "sr" if game in {"sr", "starrail", "hkrpg"} else "gs"
    source_order = get_source_order(user_source, game)
    if allow_fallback is False and user_source and user_source != "auto":
        source_order = [user_source]
    if not source_order:
        return None, [f"未启用或不支持该面板服务：{user_source or 'auto'}"]

    if (user_source or "auto") == "auto":
        latest = get_latest_panel(uid, game)
        if latest:
            return latest, errors

    for source_name in source_order:
        try:
            return await get_source_with_context(source_name, user_cfg, game).fetch(uid), errors
        except PanelSourceError as e:
            errors.append(f"{e.source}: {e.message}")
            if not fallback:
                break
        except Exception as e:
            errors.append(f"{source_name}: {e}")
            if not fallback:
                break

    return None, [format_panel_query_errors(errors, source_order, game)]
