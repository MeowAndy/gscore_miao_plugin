import re

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..alias_data import render_alias_text, resolve_alias
from ..artifact_service import render_artifact_text
from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..damage_service import render_damage_text
from ..panel_cache import clear_cached_panel
from ..panel_renderer import (render_artifact_image,
                              render_artifact_list_image, render_panel_image,
                              render_panel_list_image,
                              render_single_panel_image)
from ..panel_service import query_panel, render_panel_text
from ..settings import merge_user_cfg
from ..store import get_user_cfg

sv_feature = SV("GsCoreMiao扩展功能")


def _is_unknown_character_error(error: Exception) -> bool:
    return str(error).startswith("角色名称好像打错啦：")


async def _query_user_panel(bot: Bot, ev: Event, uid: str, source_override: str = "", allow_fallback: bool | None = None):
    user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    source = source_override or str(user_cfg.get("panel_server") or "auto")
    result, errors = await query_panel(uid, source, user_cfg, allow_fallback=allow_fallback)
    if result is None:
        detail = "\n".join(errors[:5]) if errors else "无可用数据源"
        await bot.send(f"面板数据查询失败。\n当前服务：{source}\n失败原因：\n{detail}")
    return result


async def _uid_from_event(ev: Event, uid: str) -> str:
    if uid:
        return uid
    user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    roles = user_cfg.get("mys_roles") or []
    if isinstance(roles, list):
        for role in roles:
            if isinstance(role, dict):
                role_uid = str(role.get("game_uid") or role.get("uid") or "").strip()
                if role_uid:
                    return role_uid
    default_uid = str(user_cfg.get("uid") or "").strip()
    if default_uid:
        return default_uid
    return ""


def _resolve_name(raw_name: str) -> str:
    name = (raw_name or "").strip()
    return resolve_alias(name) or name


def _extract_uid_from_text(text: str) -> str:
    match = re.search(r"\b(\d{9,10})\b", text or "")
    return match.group(1) if match else ""


async def _send_artifact_list(bot: Bot, ev: Event, uid: str) -> None:
    if not MiaoConfig.get_config("EnableArtifactScore").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, uid)
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神圣遗物列表 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    result = await _query_user_panel(bot, ev, uid)
    if result:
        try:
            await bot.send(await render_artifact_list_image(result))
        except Exception as e:
            await bot.send(f"圣遗物列表图渲染失败，已回退文本评分：{e}\n\n{render_artifact_text(result)}")


@sv_feature.on_regex(r"^原神(角色别名|别名)\s*(?P<name>.*)$", block=True)
async def send_alias(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableAliasQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    name = ((ev.regex_dict or {}).get("name") or "").strip()
    await bot.send(render_alias_text(name))


@sv_feature.on_regex(
    r"^原神(?!(?:(?:米游社|mys)(?:全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新)|更新面板|刷新面板|全部面板更新|重载面板|删除面板|解绑UID|解绑uid|角色面板图|面板图|面板列表|面板角色列表|角色列表|面板|角色面板|角色卡片|圣遗物列表|遗物列表|圣遗物评分|遗物评分|伤害计算|伤害估算)(?:\s|$))(?P<name>.+?)\s*(?P<mode>面板|面版|详情|详细|圣遗物|遗器|伤害)\s*(?P<uid>\d{9,10})?$",
    block=True,
)
async def send_miao_style_profile(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    data = ev.regex_dict or {}
    name = _resolve_name(data.get("name") or "")
    mode = (data.get("mode") or "").strip()
    if mode in {"圣遗物", "遗器"} and name.startswith(("列表", "评分列表")):
        uid_in_name = _extract_uid_from_text(name)
        return await _send_artifact_list(bot, ev, uid_in_name or (data.get("uid") or "").strip())
    uid = await _uid_from_event(ev, (data.get("uid") or "").strip())
    if not uid:
        return await bot.send(f"请携带 UID，例如：喵喵原神{name}{mode} 100000001\n也可先绑定：喵喵原神设置uid 100000001")

    result = await _query_user_panel(bot, ev, uid)
    if not result:
        return

    if mode in {"圣遗物", "遗器"}:
        if not MiaoConfig.get_config("EnableArtifactScore").data:
            return
        try:
            return await bot.send(await render_artifact_image(result, name))
        except Exception as e:
            return await bot.send(f"圣遗物详情图渲染失败，已回退文本评分：{e}\n\n{render_artifact_text(result, name)}")

    if mode == "伤害":
        if not MiaoConfig.get_config("EnableDamageCalc").data:
            return
        return await bot.send(render_damage_text(result, name))

    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    try:
        return await bot.send(await render_single_panel_image(result, name))
    except Exception as e:
        if _is_unknown_character_error(e):
            return await bot.send(str(e))
        return await bot.send(f"图片面板渲染失败，已回退文本摘要：{e}\n\n{render_panel_text(result)}")


@sv_feature.on_regex(r"^原神(圣遗物列表|遗物列表)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_artifact_list(bot: Bot, ev: Event):
    await _send_artifact_list(bot, ev, ((ev.regex_dict or {}).get("uid") or "").strip())


@sv_feature.on_regex(r"^原神(圣遗物评分|遗物评分|圣遗物)\s*(?P<uid>\d{9,10})?\s*(?P<name>.*)$", block=True)
async def send_artifact(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableArtifactScore").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    uid = await _uid_from_event(ev, uid)
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神圣遗物评分 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    name = _resolve_name((ev.regex_dict or {}).get("name") or "")
    result = await _query_user_panel(bot, ev, uid)
    if result:
        if name:
            try:
                return await bot.send(await render_artifact_image(result, name))
            except Exception as e:
                return await bot.send(f"圣遗物详情图渲染失败，已回退文本评分：{e}\n\n{render_artifact_text(result, name)}")
        await bot.send(render_artifact_text(result, name))


@sv_feature.on_regex(r"^原神(伤害计算|伤害估算|伤害)\s*(?P<uid>\d{9,10})?\s*(?P<name>.*)$", block=True)
async def send_damage(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableDamageCalc").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    uid = await _uid_from_event(ev, uid)
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神伤害计算 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    name = _resolve_name((ev.regex_dict or {}).get("name") or "")
    result = await _query_user_panel(bot, ev, uid)
    if result:
        await bot.send(render_damage_text(result, name))


@sv_feature.on_regex(r"^原神(角色面板图|面板图)\s*(?P<uid>\d{9,10})?\s*(?P<name>.*)$", block=True)
async def send_single_panel(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    uid = await _uid_from_event(ev, uid)
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神面板图 100000001 雷神\n也可先绑定：喵喵原神设置uid 100000001")
    name = _resolve_name((ev.regex_dict or {}).get("name") or "")
    result = await _query_user_panel(bot, ev, uid)
    if result:
        try:
            await bot.send(await render_single_panel_image(result, name))
        except Exception as e:
            await bot.send(f"图片面板渲染失败，已回退文本摘要：{e}\n\n{render_panel_text(result)}")


@sv_feature.on_regex(r"^原神(面板列表|面板角色列表|角色列表)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_panel_list(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip())
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神面板列表 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    result = await _query_user_panel(bot, ev, uid)
    if result:
        try:
            await bot.send(await render_panel_image(result))
        except Exception as e:
            await bot.send(f"面板列表图渲染失败，已回退文本摘要：{e}\n\n{render_panel_text(result)}")


@sv_feature.on_regex(r"^原神(更新面板|刷新面板|全部面板更新|重载面板)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_panel_update(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip())
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神更新面板 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    clear_cached_panel(uid)
    result = await _query_user_panel(bot, ev, uid)
    if result:
        try:
            await bot.send(await render_panel_list_image(result, updated=True))
        except Exception as e:
            await bot.send(f"面板已刷新：{uid}\n数据源：{result.source}\n角色数：{len(result.characters or result.avatars or [])}\n列表图渲染失败：{e}")


@sv_feature.on_regex(r"^原神(米游社|mys)(全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_mys_panel_update(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip())
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神米游社更新面板 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    clear_cached_panel(uid)
    result = await _query_user_panel(bot, ev, uid, source_override="mys", allow_fallback=False)
    if result:
        try:
            await bot.send(await render_panel_list_image(result, updated=True))
        except Exception as e:
            await bot.send(f"米游社面板已刷新：{uid}\n角色数：{len(result.characters or result.avatars or [])}\n列表图渲染失败：{e}")


@sv_feature.on_regex(r"^原神(删除面板|解绑UID|解绑uid)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_panel_delete(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    from ..store import unbind_uid

    await unbind_uid(ev.user_id, ev.bot_id)
    await bot.send("已删除本地绑定 UID。第三方面板源缓存暂不支持远程删除。")