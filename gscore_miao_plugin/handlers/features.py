from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..alias_data import render_alias_text, resolve_alias
from ..artifact_service import render_artifact_text
from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..damage_service import render_damage_text
from ..panel_renderer import render_single_panel_image
from ..panel_service import query_panel
from ..settings import merge_user_cfg
from ..store import get_user_cfg

sv_feature = SV("GsCoreMiao扩展功能")


async def _query_user_panel(bot: Bot, ev: Event, uid: str):
    user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    source = str(user_cfg.get("panel_server") or "auto")
    result, errors = await query_panel(uid, source)
    if result is None:
        detail = "\n".join(errors[:5]) if errors else "无可用数据源"
        await bot.send(f"面板数据查询失败。\n当前服务：{source}\n失败原因：\n{detail}")
    return result


@sv_feature.on_regex(r"^(角色别名|别名)\s*(?P<name>.*)$", block=True)
async def send_alias(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableAliasQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    name = ((ev.regex_dict or {}).get("name") or "").strip()
    await bot.send(render_alias_text(name))


@sv_feature.on_regex(r"^(圣遗物评分|遗物评分|圣遗物)\s*(?P<uid>\d{9,10})?\s*(?P<name>.*)$", block=True)
async def send_artifact(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableArtifactScore").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵圣遗物评分 100000001")
    name = resolve_alias(((ev.regex_dict or {}).get("name") or "").strip()) or ((ev.regex_dict or {}).get("name") or "").strip()
    result = await _query_user_panel(bot, ev, uid)
    if result:
        await bot.send(render_artifact_text(result, name))


@sv_feature.on_regex(r"^(伤害计算|伤害估算|伤害)\s*(?P<uid>\d{9,10})?\s*(?P<name>.*)$", block=True)
async def send_damage(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableDamageCalc").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵伤害计算 100000001")
    name = resolve_alias(((ev.regex_dict or {}).get("name") or "").strip()) or ((ev.regex_dict or {}).get("name") or "").strip()
    result = await _query_user_panel(bot, ev, uid)
    if result:
        await bot.send(render_damage_text(result, name))


@sv_feature.on_regex(r"^(角色面板图|面板图)\s*(?P<uid>\d{9,10})?\s*(?P<name>.*)$", block=True)
async def send_single_panel(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵面板图 100000001 雷神")
    name = resolve_alias(((ev.regex_dict or {}).get("name") or "").strip()) or ((ev.regex_dict or {}).get("name") or "").strip()
    result = await _query_user_panel(bot, ev, uid)
    if result:
        await bot.send(await render_single_panel_image(result, name))