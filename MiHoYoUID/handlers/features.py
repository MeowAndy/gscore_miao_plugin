import re

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.sv import SV

from ..alias_data import render_alias_text, resolve_alias
from ..artifact_service import render_artifact_text
from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..damage_service import render_damage_text
from ..panel_cache import clear_cached_panel, set_latest_panel
from ..panel_renderer import (render_artifact_image,
                              render_artifact_list_image,
                              render_char_wiki_image, render_char_wiki_images,
                              render_damage_image, render_panel_image,
                              render_panel_list_image, render_rank_list_image,
                              render_single_panel_image,
                              render_training_stat_image)
from ..panel_service import query_panel, render_panel_text
from ..rank_service import (format_rank_detail, format_rank_list,
                            get_rank_rows, render_training_stat_text,
                            reset_group_rank, update_group_rank_records)
from ..settings import merge_user_cfg
from ..store import get_user_cfg
from ..wiki_service import render_char_wiki_text, wiki_image_payload

sv_feature = SV("GsCoreMiao扩展功能")


def _is_unknown_character_error(error: Exception) -> bool:
    return str(error).startswith("角色名称好像打错啦：")


async def _query_user_panel(bot: Bot, ev: Event, uid: str, source_override: str = "", allow_fallback: bool | None = None, game: str = "gs"):
    user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    source = source_override or str(user_cfg.get("panel_server") or "auto")
    result, errors = await query_panel(uid, source, user_cfg, allow_fallback=allow_fallback, game=game)
    if result is None:
        detail = "\n".join(errors[:5]) if errors else "无可用数据源"
        tip = "喵喵崩铁设置面板服务 auto" if game in {"sr", "starrail", "hkrpg"} else "喵喵原神设置面板服务 auto"
        await bot.send(f"面板数据查询失败。\n当前服务：{source}\n失败原因：\n{detail}")
        if source != "auto":
            await bot.send(f"可尝试切换自动数据源：{tip}")
    elif getattr(ev, "group_id", None) and (result.characters or []):
        await update_group_rank_records(result, str(ev.group_id), str(ev.user_id or ""))
    return result


async def _uid_from_event(ev: Event, uid: str, game: str = "gs") -> str:
    if uid:
        return uid
    user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    is_sr = game in {"sr", "starrail", "hkrpg"}
    default_uid = str(user_cfg.get("sr_uid" if is_sr else "uid") or "").strip()
    if default_uid:
        return default_uid
    roles = user_cfg.get("mys_sr_roles" if is_sr else "mys_roles") or []
    if isinstance(roles, list):
        for role in roles:
            if isinstance(role, dict):
                role_uid = str(role.get("game_uid") or role.get("uid") or "").strip()
                if role_uid:
                    return role_uid
    return ""


def _resolve_name(raw_name: str) -> str:
    name = (raw_name or "").strip()
    return resolve_alias(name) or name


def _resolve_name_for_game(raw_name: str, game: str = "gs") -> str:
    name = (raw_name or "").strip()
    return resolve_alias(name, game=game) or name


def _extract_uid_from_text(text: str) -> str:
    match = re.search(r"\b(\d{9,10})\b", text or "")
    return match.group(1) if match else ""


def _damage_query_name(name: str, extra: str = "") -> str:
    extra = re.sub(r"\b\d{9,10}\b", " ", extra or "")
    return re.sub(r"\s+", " ", f"{name or ''} {extra or ''}").strip()


def _remember_latest_panel(result) -> None:
    if result:
        set_latest_panel(result.uid, result, result.game)


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


@sv_feature.on_regex(r"^(原神|崩铁|星铁)?(?P<name>.+?)(?P<mode>天赋|技能|行迹|命座|命之座|星魂|资料|图鉴|材料|素材|养成)$", block=True)
async def send_char_wiki(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    text = getattr(ev, "raw_text", "") or ""
    game = "sr" if text.startswith(("崩铁", "星铁")) or "崩铁" in text or "星铁" in text else "gs"
    name = (data.get("name") or "").strip()
    for prefix in ("原神", "崩铁", "星铁"):
        if name.startswith(prefix):
            name = name[len(prefix):].strip()
    mode = (data.get("mode") or "资料").strip()
    payload, wiki_mode, wiki_game = wiki_image_payload(name, mode, game)
    if payload:
        try:
            wiki_images = await render_char_wiki_images(payload, wiki_mode, wiki_game)
            if len(wiki_images) == 1:
                return await bot.send(wiki_images[0])
            try:
                return await bot.send(MessageSegment.node(wiki_images))
            except Exception:
                for image in wiki_images:
                    await bot.send(image)
                return
        except Exception as e:
            return await bot.send(f"角色图鉴渲染失败，已回退文本：{e}\n\n{render_char_wiki_text(name, mode, game)}")
    await bot.send(render_char_wiki_text(name, mode, game))


@sv_feature.on_regex(
    r"^原神(?!(?:(?:米游社|mys)(?:全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新|刷新面板|面板刷新)|更新面板|刷新面板|面板刷新|全部面板更新|重载面板|删除面板|解绑UID|解绑uid|角色面板图|面板图|面板列表|面板角色列表|角色列表|面板|角色面板|角色卡片|圣遗物列表|遗物列表|圣遗物评分|遗物评分|伤害计算|伤害估算)(?:\s|$))(?P<name>.+?)\s*(?P<mode>面板|面版|详情|详细|圣遗物|遗器|伤害)\s*(?P<extra>.*?)(?P<uid>\d{9,10})?$",
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
    uid = await _uid_from_event(ev, (data.get("uid") or "").strip() or _extract_uid_from_text(data.get("extra") or ""))
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
        damage_name = _damage_query_name(name, data.get("extra") or "")
        try:
            return await bot.send(await render_damage_image(result, damage_name))
        except Exception as e:
            return await bot.send(f"伤害估算图渲染失败，已回退文本：{e}\n\n{render_damage_text(result, damage_name)}")

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


@sv_feature.on_regex(r"^崩铁(遗器列表|圣遗物列表)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_sr_artifact_list(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableArtifactScore").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip(), game="sr")
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵崩铁遗器列表 100000001\n也可先登录或绑定：喵喵登录 / 喵喵崩铁设置uid 100000001")
    result = await _query_user_panel(bot, ev, uid, game="sr")
    if result:
        try:
            await bot.send(await render_artifact_list_image(result))
        except Exception as e:
            await bot.send(f"遗器列表图渲染失败，已回退文本评分：{e}\n\n{render_artifact_text(result)}")


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
        try:
            await bot.send(await render_damage_image(result, name))
        except Exception as e:
            await bot.send(f"伤害估算图渲染失败，已回退文本：{e}\n\n{render_damage_text(result, name)}")


@sv_feature.on_regex(r"^原神(?P<name>.+?)伤害\s*(?P<extra>.*?)(?P<uid>\d{9,10})?$", block=True)
async def send_miao_style_damage(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableDamageCalc").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    name = _resolve_name(data.get("name") or "")
    damage_name = _damage_query_name(name, data.get("extra") or "")
    uid = await _uid_from_event(ev, (data.get("uid") or "").strip() or _extract_uid_from_text(data.get("extra") or ""))
    if not uid:
        return await bot.send(f"请携带 UID，例如：喵喵原神{name}伤害 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    result = await _query_user_panel(bot, ev, uid)
    if result:
        try:
            await bot.send(await render_damage_image(result, damage_name))
        except Exception as e:
            await bot.send(f"伤害估算图渲染失败，已回退文本：{e}\n\n{render_damage_text(result, damage_name)}")


@sv_feature.on_regex(r"^崩铁(伤害计算|伤害估算|伤害)\s*(?P<uid>\d{9,10})?\s*(?P<name>.*)$", block=True)
async def send_sr_damage(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableDamageCalc").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    uid = await _uid_from_event(ev, uid, game="sr")
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵崩铁伤害估算 800000001\n也可先登录或绑定：喵喵登录 / 喵喵崩铁设置uid 800000001")
    name = _resolve_name_for_game((ev.regex_dict or {}).get("name") or "", game="sr")
    result = await _query_user_panel(bot, ev, uid, game="sr")
    if result:
        try:
            await bot.send(await render_damage_image(result, name))
        except Exception as e:
            await bot.send(f"崩铁伤害估算图渲染失败，已回退文本：{e}\n\n{render_damage_text(result, name)}")


@sv_feature.on_regex(r"^崩铁(?P<name>.+?)伤害\s*(?P<extra>.*?)(?P<uid>\d{9,10})?$", block=True)
async def send_sr_miao_style_damage(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableDamageCalc").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    name = _resolve_name_for_game(data.get("name") or "", game="sr")
    damage_name = _damage_query_name(name, data.get("extra") or "")
    uid = await _uid_from_event(ev, (data.get("uid") or "").strip() or _extract_uid_from_text(data.get("extra") or ""), game="sr")
    if not uid:
        return await bot.send(f"请携带 UID，例如：喵喵崩铁{name}伤害 100000001\n也可先登录或绑定：喵喵登录 / 喵喵崩铁设置uid 100000001")
    result = await _query_user_panel(bot, ev, uid, game="sr")
    if result:
        try:
            await bot.send(await render_damage_image(result, damage_name))
        except Exception as e:
            await bot.send(f"崩铁伤害估算图渲染失败，已回退文本：{e}\n\n{render_damage_text(result, damage_name)}")


@sv_feature.on_regex(r"^崩铁(?P<name>.*?)(群内|群)?(?P<kind>最强|最高分|第一|最高|最牛|最多|排名|排行|排行榜|排行版)(榜)?$", block=True)
async def send_sr_group_rank_first(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    group_id = str(getattr(ev, "group_id", "") or "")
    if not group_id:
        return await bot.send("群排名只能在群聊中使用。")
    text = getattr(ev, "raw_text", "") or ""
    mode = _rank_mode(text)
    name = _resolve_name_for_game(_strip_rank_name(text, "sr"), game="sr")
    rows = await get_rank_rows(group_id, "sr", name, mode, limit=20)
    is_list = any(word in text for word in ("排名", "排行", "榜"))
    try:
        return await bot.send(await render_rank_list_image(rows if is_list else rows[:1], group_id, "sr", name or "全角色", mode))
    except Exception as e:
        if is_list:
            return await bot.send(f"排行图渲染失败，已回退文本：{e}\n\n{format_rank_list(rows, group_id, 'sr', name or '全角色', mode)}")
        return await bot.send(f"排行图渲染失败，已回退文本：{e}\n\n{format_rank_detail(rows[0] if rows else None, group_id, 'sr', name, mode)}")


@sv_feature.on_regex(
    r"^崩铁(?!(?:(?:米游社|mys)(?:全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新|刷新面板|面板刷新)|更新面板|刷新面板|面板刷新|全部面板更新|重载面板|删除面板|解绑UID|解绑uid|面板列表|面板角色列表|角色列表|面板角色|角色面板|面板|遗器列表|圣遗物列表|(?:面板|喵喵)?练度统计|抽卡记录|抽卡统计|抽奖记录|祈愿记录|祈愿统计|抽卡分析|角色池抽卡统计|光锥池抽卡统计|常驻池抽卡统计)(?:\s|$))(?!(?:.*(?:最强|最高分|第一|最高|最牛|最多|排名|排行|排行榜|排行版|榜))$)(?P<name>.+?)\s*(?P<mode>面板|面版|详情|详细|遗器|圣遗物|光锥|伤害)?\s*(?P<extra>.*?)(?P<uid>\d{9,10})?$",
    block=True,
)
async def send_sr_miao_style_profile(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    data = ev.regex_dict or {}
    name = _resolve_name_for_game(data.get("name") or "", game="sr")
    mode = (data.get("mode") or "面板").strip()
    uid = await _uid_from_event(ev, (data.get("uid") or "").strip() or _extract_uid_from_text(data.get("extra") or ""), game="sr")
    if not uid:
        return await bot.send(f"请携带 UID，例如：喵喵崩铁{name}{mode} 100000001\n也可先登录或绑定：喵喵登录 / 喵喵崩铁设置uid 100000001")

    result = await _query_user_panel(bot, ev, uid, game="sr")
    if not result:
        return

    if mode in {"遗器", "圣遗物"}:
        if not MiaoConfig.get_config("EnableArtifactScore").data:
            return
        try:
            return await bot.send(await render_artifact_image(result, name))
        except Exception as e:
            return await bot.send(f"遗器详情图渲染失败，已回退文本评分：{e}\n\n{render_artifact_text(result, name)}")

    if mode == "伤害":
        if not MiaoConfig.get_config("EnableDamageCalc").data:
            return
        damage_name = _damage_query_name(name, data.get("extra") or "")
        try:
            return await bot.send(await render_damage_image(result, damage_name))
        except Exception as e:
            return await bot.send(f"崩铁伤害估算图渲染失败，已回退文本：{e}\n\n{render_damage_text(result, damage_name)}")

    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    try:
        return await bot.send(await render_single_panel_image(result, name))
    except Exception as e:
        if _is_unknown_character_error(e):
            return await bot.send(str(e))
        return await bot.send(f"崩铁图片面板渲染失败，已回退文本摘要：{e}\n\n{render_panel_text(result)}")


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


@sv_feature.on_regex(r"^崩铁(面板|角色面板|面板角色|面板列表|面板角色列表|角色列表)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_sr_panel_list(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip(), game="sr")
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵崩铁面板 100000001\n也可先登录或绑定：喵喵登录 / 喵喵崩铁设置uid 100000001")
    result = await _query_user_panel(bot, ev, uid, game="sr")
    if result:
        try:
            await bot.send(await render_panel_image(result))
        except Exception as e:
            await bot.send(f"崩铁面板列表图渲染失败，已回退文本摘要：{e}\n\n{render_panel_text(result)}")


def _rank_mode(text: str) -> str:
    if "词条" in text:
        return "valid"
    if "双爆" in text or "双暴" in text:
        return "crit"
    if any(x in text for x in ("分", "圣遗物", "遗器", "评分", "ACE")):
        return "mark"
    return "dmg"


def _strip_rank_name(text: str, game: str = "gs") -> str:
    for token in ("原神", "崩铁", "星铁", "群内", "群", "排名", "排行", "排行榜", "排行版", "榜", "最强", "最高分", "第一", "最高", "最牛", "最多", "面板", "详情", "面版", "圣遗物", "遗器", "评分", "词条", "双爆", "双暴"):
        text = text.replace(token, "")
    return text.strip()


@sv_feature.on_regex(r"^(原神|崩铁|星铁)?(?P<name>.*?)(群内|群)?(?P<kind>最强|最高分|第一|最高|最牛|最多|排名|排行|排行榜|排行版)(榜)?$", block=True)
async def send_group_rank(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    group_id = str(getattr(ev, "group_id", "") or "")
    if not group_id:
        return await bot.send("群排名只能在群聊中使用。")
    text = getattr(ev, "raw_text", "") or ""
    game = "sr" if text.startswith(("崩铁", "星铁")) or "崩铁" in text or "星铁" in text else "gs"
    mode = _rank_mode(text)
    name = _resolve_name_for_game(_strip_rank_name(text, game), game=game)
    rows = await get_rank_rows(group_id, game, name, mode, limit=20)
    try:
        return await bot.send(await render_rank_list_image(rows[:1] if not any(word in text for word in ("排名", "排行", "榜")) else rows, group_id, game, name or "全角色", mode))
    except Exception as e:
        if any(word in text for word in ("排名", "排行", "榜")):
            return await bot.send(f"排行图渲染失败，已回退文本：{e}\n\n{format_rank_list(rows, group_id, game, name or '全角色', mode)}")
        return await bot.send(f"排行图渲染失败，已回退文本：{e}\n\n{format_rank_detail(rows[0] if rows else None, group_id, game, name, mode)}")


@sv_feature.on_regex(r"^(原神|崩铁|星铁)?(重置|重设)(?P<name>.*?)(排名|排行)$", block=True)
async def send_rank_reset(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    group_id = str(getattr(ev, "group_id", "") or "")
    if not group_id:
        return await bot.send("排名重置只能在群聊中使用。")
    text = getattr(ev, "raw_text", "") or ""
    game = "sr" if "崩铁" in text or "星铁" in text else "gs"
    raw_name = ((ev.regex_dict or {}).get("name") or "").strip()
    for token in ("群内", "群", "面板", "详情", "面版"):
        raw_name = raw_name.replace(token, "")
    name = _resolve_name_for_game(raw_name, game=game) if raw_name else ""
    removed = await reset_group_rank(group_id, game, name)
    await bot.send(f"已重置本群{' ' + name if name else '全部角色'}排名，共清理 {removed} 条记录。")


@sv_feature.on_regex(r"^(原神|崩铁|星铁)?(面板|喵喵)?练度统计\s*(?P<uid>\d{9,10})?$", block=True)
async def send_training_stat(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = getattr(ev, "raw_text", "") or ""
    game = "sr" if "崩铁" in text or "星铁" in text else "gs"
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip(), game=game)
    if not uid:
        return await bot.send("请携带 UID，或先绑定 UID。")
    result = await _query_user_panel(bot, ev, uid, game=game)
    if result:
        try:
            await bot.send(await render_training_stat_image(result))
        except Exception as e:
            await bot.send(f"练度统计图渲染失败，已回退文本：{e}\n\n{render_training_stat_text(result)}")


@sv_feature.on_regex(r"^原神(更新面板|刷新面板|全部面板更新|重载面板)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_panel_update(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip())
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神更新面板 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    cleared = clear_cached_panel(uid)
    result = await _query_user_panel(bot, ev, uid)
    if result:
        _remember_latest_panel(result)
        try:
            await bot.send(await render_panel_list_image(result, updated=True))
        except Exception as e:
            await bot.send(f"面板已刷新：{uid}\n本地缓存清理：{cleared} 条\n数据源：{result.source}\n角色数：{len(result.characters or result.avatars or [])}\n列表图渲染失败：{e}")


@sv_feature.on_regex(r"^崩铁(更新面板|刷新面板|全部面板更新|重载面板)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_sr_panel_update(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip(), game="sr")
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵崩铁更新面板 100000001\n也可先登录或绑定：喵喵登录 / 喵喵崩铁设置uid 100000001")
    cleared = clear_cached_panel(uid)
    result = await _query_user_panel(bot, ev, uid, game="sr")
    if result:
        _remember_latest_panel(result)
        try:
            await bot.send(await render_panel_list_image(result, updated=True))
        except Exception as e:
            await bot.send(f"崩铁面板已刷新：{uid}\n本地缓存清理：{cleared} 条\n数据源：{result.source}\n角色数：{len(result.characters or result.avatars or [])}\n列表图渲染失败：{e}")


@sv_feature.on_regex(r"^原神(米游社|mys)(全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新|刷新面板|面板刷新)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_mys_panel_update(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip())
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神米游社更新面板 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    cleared = clear_cached_panel(uid)
    result = await _query_user_panel(bot, ev, uid, source_override="mys", allow_fallback=False)
    if result:
        _remember_latest_panel(result)
        try:
            await bot.send(await render_panel_list_image(result, updated=True))
        except Exception as e:
            await bot.send(f"米游社面板已刷新：{uid}\n本地缓存清理：{cleared} 条\n角色数：{len(result.characters or result.avatars or [])}\n列表图渲染失败：{e}")


@sv_feature.on_regex(r"^崩铁(米游社|mys)(全部面板更新|更新全部面板|获取游戏角色详情|更新面板|面板更新|刷新面板|面板刷新)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_sr_mys_panel_update(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip(), game="sr")
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵崩铁米游社更新面板 100000001\n也可先登录或绑定：喵喵登录 / 喵喵崩铁设置uid 100000001")
    cleared = clear_cached_panel(uid)
    result = await _query_user_panel(bot, ev, uid, source_override="mys", allow_fallback=False, game="sr")
    if result:
        _remember_latest_panel(result)
        try:
            await bot.send(await render_panel_list_image(result, updated=True))
        except Exception as e:
            await bot.send(f"崩铁米游社面板已刷新：{uid}\n本地缓存清理：{cleared} 条\n角色数：{len(result.characters or result.avatars or [])}\n列表图渲染失败：{e}")


@sv_feature.on_regex(r"^原神(删除面板|解绑UID|解绑uid)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_panel_delete(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    from ..store import unbind_uid

    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip())
    cleared = clear_cached_panel(uid) if uid else 0
    await unbind_uid(ev.user_id, ev.bot_id)
    await bot.send(f"已删除本地绑定 UID，并清理本地面板缓存 {cleared} 条。第三方面板源缓存暂不支持远程删除。")


@sv_feature.on_regex(r"^崩铁(删除面板|解绑UID|解绑uid)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_sr_panel_delete(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    from ..store import unbind_uid

    uid = await _uid_from_event(ev, ((ev.regex_dict or {}).get("uid") or "").strip(), game="sr")
    cleared = clear_cached_panel(uid) if uid else 0
    await unbind_uid(ev.user_id, ev.bot_id, game="sr")
    await bot.send(f"已删除本地绑定的崩铁 UID，并清理本地面板缓存 {cleared} 条。第三方面板源缓存暂不支持远程删除。")