from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..help_data import HELP_GROUPS, STAR_RAIL_HELP_GROUPS
from ..panel_renderer import render_help_image, render_panel_image
from ..panel_service import query_panel, render_panel_text
from ..settings import merge_user_cfg
from ..store import get_user_cfg
from ..version import PLUGIN_VERSION

sv_help = SV("GsCoreMiao帮助")


def _cmd_prefix() -> str:
    return str(MiaoConfig.get_config("CommandPrefix").data or "喵喵").strip() or "喵喵"


def _help_groups_for_display(source_groups, setting_export: bool, setting_reset: bool):
    prefix = _cmd_prefix()
    groups = []
    for group in source_groups:
        items = []
        for item in group["items"]:
            cmd = item["cmd"].replace("{prefix}", prefix)
            if (not setting_export) and ("设置导出" in cmd):
                continue
            if (not setting_reset) and ("设置重置" in cmd):
                continue
            items.append({"cmd": cmd, "desc": item["desc"]})
        groups.append({"group": group["group"], "items": items})
    return groups


@sv_help.on_fullmatch(("帮助", "菜单"), block=True)
async def send_help_hint(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableHelp").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    prefix = _cmd_prefix()
    await bot.send(
        "请指定游戏帮助：\n"
        f"{prefix}原神帮助\n"
        f"{prefix}崩铁帮助"
    )


@sv_help.on_fullmatch(("原神帮助", "原神菜单"), block=True)
async def send_help(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableHelp").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    title = MiaoConfig.get_config("HelpTitle").data
    subtitle = MiaoConfig.get_config("HelpSubTitle").data
    setting_export = MiaoConfig.get_config("EnableSettingExport").data
    setting_reset = MiaoConfig.get_config("EnableSettingReset").data
    groups = _help_groups_for_display(HELP_GROUPS, bool(setting_export), bool(setting_reset))

    if str(MiaoConfig.get_config("HelpRenderMode").data or "image") == "image":
        try:
            return await bot.send(await render_help_image(str(title), str(subtitle), groups, _cmd_prefix()))
        except Exception as e:
            lines = [f"帮助图片渲染失败，已回退文本：{e}", ""]
    else:
        lines = []

    lines.extend([f"{title}", f"{subtitle}", ""])
    idx = 1
    for group in groups:
        lines.append(f"【{group['group']}】")
        for item in group["items"]:
            cmd = item["cmd"]
            lines.append(f"{idx}) {cmd} - {item['desc']}")
            idx += 1
        lines.append("")
    msg = "\n".join(lines).strip()
    await bot.send(msg)


@sv_help.on_fullmatch(("崩铁帮助", "崩铁菜单"), block=True)
async def send_starrail_help(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableHelp").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    title = "喵喵崩铁帮助（GsCore）"
    subtitle = "崩坏：星穹铁道功能导航 · 基于 miao-plugin StarRail 命令梳理"
    groups = _help_groups_for_display(STAR_RAIL_HELP_GROUPS, True, True)

    if str(MiaoConfig.get_config("HelpRenderMode").data or "image") == "image":
        try:
            return await bot.send(await render_help_image(str(title), str(subtitle), groups, _cmd_prefix()))
        except Exception as e:
            lines = [f"帮助图片渲染失败，已回退文本：{e}", ""]
    else:
        lines = []

    lines.extend([f"{title}", f"{subtitle}", ""])
    idx = 1
    for group in groups:
        lines.append(f"【{group['group']}】")
        for item in group["items"]:
            cmd = item["cmd"]
            lines.append(f"{idx}) {cmd} - {item['desc']}")
            idx += 1
        lines.append("")
    msg = "\n".join(lines).strip()
    await bot.send(msg)


@sv_help.on_fullmatch(("原神版本",), block=True)
async def send_version(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableVersion").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    await bot.send(f"MiHoYoUID v{PLUGIN_VERSION}")


@sv_help.on_regex(r"^原神(面板|角色面板)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_panel(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePanelQuery").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    uid = ((ev.regex_dict or {}).get("uid") or "").strip() or str(user_cfg.get("uid") or "").strip()
    if not uid:
        return await bot.send("请携带 UID，例如：喵喵原神面板 100000001\n也可先绑定：喵喵原神设置uid 100000001")
    source = str(user_cfg.get("panel_server") or "auto")
    result, errors = await query_panel(uid, source)
    if result is None:
        detail = "\n".join(errors[:5]) if errors else "无可用数据源"
        return await bot.send(
            "面板数据查询失败。\n"
            f"当前服务：{source}\n"
            f"失败原因：\n{detail}\n\n"
                "请在网页控制台配置 Miao/Enka/米游社等数据源，或使用：喵喵原神设置面板服务 auto"
        )

    render_mode = str(MiaoConfig.get_config("PanelRenderMode").data or "image")
    use_image = render_mode == "image" and bool(user_cfg.get("custom_splash", True))
    if use_image:
        try:
            return await bot.send(await render_panel_image(result))
        except Exception as e:
            return await bot.send(f"图片面板渲染失败，已回退文本摘要：{e}\n\n{render_panel_text(result)}")

    await bot.send(render_panel_text(result))
