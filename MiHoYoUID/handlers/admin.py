import json

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import add_history, can_use_plugin, get_recent_history_lines
from ..config import MiaoConfig
from ..panel_renderer import render_setting_card
from ..settings import build_default_user_cfg, merge_user_cfg
from ..store import (bind_uid, get_user_cfg, reset_user_cfg, set_user_cfg,
                     unbind_uid)

sv_admin = SV("GsCoreMiao设置")


def _normalize_bool(v: str):
    v = v.strip().lower()
    if v in {"开", "开启", "on", "true", "1", "是"}:
        return True
    if v in {"关", "关闭", "off", "false", "0", "否"}:
        return False
    return None


def _schema_desc() -> str:
    cfg = MiaoConfig.get_config("AllowedPanelServers").data
    return "|".join(cfg)


def _cmd_prefix() -> str:
    return str(MiaoConfig.get_config("CommandPrefix").data or "喵喵").strip() or "喵喵"


def _normalize_key(raw: str) -> str:
    raw = (raw or "").strip()
    alias = {
        "服务": "面板服务",
        "面板": "面板图",
        "组队伤害": "组队",
        "逗号分组": "逗号",
        "数字分组": "逗号",
        "星级显示": "星级",
    }
    return alias.get(raw, raw)


def _uid_list_text(user_cfg: dict, game: str = "gs") -> str:
    key = "sr_uid_list" if game == "sr" else "uid_list"
    cur_key = "sr_uid" if game == "sr" else "uid"
    current = str(user_cfg.get(cur_key) or "")
    values = [str(x) for x in user_cfg.get(key, []) if str(x).strip()]
    if current and current not in values:
        values.insert(0, current)
    if not values:
        return "暂无历史 UID"
    return "\n".join(f"{idx}. {uid}{'（当前）' if uid == current else ''}" for idx, uid in enumerate(values, start=1))


def _uid_list_lines(user_cfg: dict, game: str = "gs") -> list[str]:
    text = _uid_list_text(user_cfg, game)
    return text.splitlines() if text else []


def _uid_values(user_cfg: dict, game: str = "gs") -> list[str]:
    key = "sr_uid_list" if game == "sr" else "uid_list"
    cur_key = "sr_uid" if game == "sr" else "uid"
    current = str(user_cfg.get(cur_key) or "").strip()
    values = [str(x).strip() for x in user_cfg.get(key, []) if str(x).strip()]
    if current and current not in values:
        values.insert(0, current)
    return list(dict.fromkeys(values))


async def _switch_uid(bot: Bot, ev: Event, value: str, game: str = "gs"):
    is_sr = game == "sr"
    user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    values = _uid_values(user_cfg, game)
    title = "崩铁" if is_sr else "原神"
    prefix = _cmd_prefix()
    if not value:
        if not values:
            return await bot.send(f"当前没有可切换的{title} UID，请先绑定：{prefix}{title}设置uid <UID>")
        if len(values) == 1:
            return await bot.send(f"当前只有一个{title} UID：{values[0]}（当前），无需切换。")
        return await bot.send(f"【{title} UID 列表】\n{_uid_list_text(user_cfg, game)}\n\n请使用：{prefix}{title}设置uid 切换 <UID>")
    if not value.isdigit() or len(value) not in {9, 10}:
        return await bot.send(f"请填写正确 UID，例如：{prefix}{title}设置uid 切换 {values[0] if values else '100000001'}")
    await bind_uid(ev.user_id, ev.bot_id, value, game=game)
    await add_history(ev, f"{title}UID切换", value)
    note = "" if value in values else "（已新增到历史 UID）"
    return await bot.send(f"已切换{title} UID：{value}{note}")


@sv_admin.on_regex(r"^#?原神设置\s*(?P<key>[^\s]+)?\s*(?P<value>.*)$", block=True)
async def miao_setting(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableMiaoSetting").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    key = (ev.regex_dict or {}).get("key", "")
    value = ((ev.regex_dict or {}).get("value", "") or "").strip()
    key = _normalize_key(key)

    if not key:
        user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
        prefix = _cmd_prefix()
        panel_server = user_cfg.get("panel_server", "auto")
        uid = user_cfg.get("uid") or "未绑定"
        custom_splash = user_cfg.get("custom_splash", True)
        team_calc = user_cfg.get("team_calc", False)
        show_star = user_cfg.get("show_star", False)
        comma_group = user_cfg.get("comma_group", 3)
        stats = [("绑定 UID", uid), ("面板服务", panel_server), ("面板图", "开启" if custom_splash else "关闭"), ("组队伤害", "开启" if team_calc else "关闭"), ("星级显示", "开启" if show_star else "关闭"), ("数字分组", comma_group)]
        commands = [
            f"{prefix}原神设置面板服务 <{_schema_desc()}>",
            f"{prefix}原神设置uid <UID|列表|切换 UID|解绑>",
            f"{prefix}原神设置面板图 <开启|关闭>",
            f"{prefix}原神设置组队 <开启|关闭>",
            f"{prefix}原神设置星级 <开启|关闭>",
            f"{prefix}原神设置逗号 <2-8>",
            f"{prefix}原神设置历史 / 导出 / 重置",
        ]
        try:
            return await bot.send(await render_setting_card("喵喵原神设置", "原神面板、伤害与显示偏好", stats, commands, _uid_list_lines(user_cfg), "gs"))
        except Exception:
            return await bot.send("【喵喵原神设置】\n" + "\n".join(f"{k}: {v}" for k, v in stats))

    if key == "历史":
        lines = await get_recent_history_lines(ev)
        if not lines:
            return await bot.send("暂无设置历史记录")
        return await bot.send("【喵喵原神设置历史】\n" + "\n".join(lines[:20]))

    if key == "导出":
        if not MiaoConfig.get_config("EnableSettingExport").data:
            return await bot.send("设置导出功能已关闭")
        user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
        text = json.dumps(user_cfg, ensure_ascii=False, indent=2)
        await add_history(ev, "设置导出", "ok")
        return await bot.send(f"【喵喵原神设置导出】\n{text}")

    if key == "重置":
        if not MiaoConfig.get_config("EnableSettingReset").data:
            return await bot.send("设置重置功能已关闭")
        await reset_user_cfg(ev.user_id, ev.bot_id)
        default_cfg = build_default_user_cfg()
        await add_history(ev, "设置重置", json.dumps(default_cfg, ensure_ascii=False))
        return await bot.send("已重置为默认设置")

    if key == "面板服务":
        allowed = set(MiaoConfig.get_config("AllowedPanelServers").data)
        if value not in allowed:
            return await bot.send(f"无效服务：{value}\n可选：{_schema_desc()}")
        await set_user_cfg(ev.user_id, ev.bot_id, {"panel_server": value})
        await add_history(ev, "面板服务", value)
        return await bot.send(f"已设置面板服务为：{value}")

    if key.lower() == "uid":
        if value in {"列表", "list", "ls"}:
            user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
            return await bot.send("【原神 UID 列表】\n" + _uid_list_text(user_cfg))
        if value.startswith(("切换", "选择", "使用")):
            value = value.replace("切换", "", 1).replace("选择", "", 1).replace("使用", "", 1).strip()
            return await _switch_uid(bot, ev, value)
        if value in {"", "解绑", "删除", "unset", "clear"}:
            await unbind_uid(ev.user_id, ev.bot_id)
            await add_history(ev, "UID解绑", "ok")
            return await bot.send("已解绑 UID")
        if not value.isdigit() or len(value) not in {9, 10}:
            return await bot.send(f"请填写正确 UID，例如：{_cmd_prefix()}原神设置uid 100000001")
        await bind_uid(ev.user_id, ev.bot_id, value)
        await add_history(ev, "UID绑定", value)
        prefix = _cmd_prefix()
        return await bot.send(f"已绑定 UID：{value}\n之后可直接使用：{prefix}原神面板 / {prefix}原神雷神面板")

    if key == "面板图":
        b = _normalize_bool(value)
        if b is None:
            return await bot.send("请填写：开启 或 关闭")
        await set_user_cfg(ev.user_id, ev.bot_id, {"custom_splash": b})
        await add_history(ev, "面板图", "开启" if b else "关闭")
        return await bot.send(f"已{'开启' if b else '关闭'}面板图")

    if key == "组队":
        b = _normalize_bool(value)
        if b is None:
            return await bot.send("请填写：开启 或 关闭")
        await set_user_cfg(ev.user_id, ev.bot_id, {"team_calc": b})
        await add_history(ev, "组队伤害", "开启" if b else "关闭")
        return await bot.send(f"已{'开启' if b else '关闭'}组队伤害")

    if key == "星级":
        b = _normalize_bool(value)
        if b is None:
            return await bot.send("请填写：开启 或 关闭")
        await set_user_cfg(ev.user_id, ev.bot_id, {"show_star": b})
        await add_history(ev, "星级显示", "开启" if b else "关闭")
        return await bot.send(f"已{'开启' if b else '关闭'}星级显示")

    if key == "逗号":
        try:
            n = int(value)
        except Exception:
            return await bot.send(f"请填写数字，例如：{_cmd_prefix()}原神设置逗号 3")
        max_group = int(MiaoConfig.get_config("MaxCommaGroup").data)
        if n < 2 or n > max_group:
            return await bot.send(f"数字分组范围应为 2-{max_group}")
        await set_user_cfg(ev.user_id, ev.bot_id, {"comma_group": n})
        await add_history(ev, "数字分组", str(n))
        return await bot.send(f"已设置数字分组为：{n}")

    await bot.send(f"暂不支持该设置项，请发送 {_cmd_prefix()}原神设置 查看帮助")


@sv_admin.on_regex(r"^#?崩铁设置\s*(?P<key>[^\s]+)?\s*(?P<value>.*)$", block=True)
async def miao_sr_setting(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableMiaoSetting").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    key = _normalize_key((ev.regex_dict or {}).get("key", ""))
    value = ((ev.regex_dict or {}).get("value", "") or "").strip()
    prefix = _cmd_prefix()
    if not key:
        user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
        stats = [("绑定 UID", user_cfg.get("sr_uid") or "未绑定"), ("面板服务", user_cfg.get("panel_server", "auto")), ("米游社登录", "已保存" if user_cfg.get("mys_cookie") else "未登录"), ("UID 历史", len(_uid_values(user_cfg, "sr")))]
        commands = [
            f"{prefix}崩铁设置uid <UID|列表|切换 UID|解绑>",
            f"{prefix}崩铁设置面板服务 <auto|miao|mys|mihomo|avocado|enkahsr>",
            f"{prefix}崩铁mys刷新面板",
            f"{prefix}查看登录 / {prefix}签到",
        ]
        try:
            return await bot.send(await render_setting_card("喵喵崩铁设置", "星穹铁道面板与米游社数据设置", stats, commands, _uid_list_lines(user_cfg, "sr"), "sr"))
        except Exception:
            return await bot.send("【喵喵崩铁设置】\n" + "\n".join(f"{k}: {v}" for k, v in stats))

    if key == "面板服务":
        allowed = {"auto", "miao", "mihomo", "avocado", "enkahsr", "mys"}
        if value not in allowed:
            return await bot.send(f"无效服务：{value}\n可选：auto|miao|mihomo|avocado|enkahsr|mys")
        await set_user_cfg(ev.user_id, ev.bot_id, {"panel_server": value})
        await add_history(ev, "崩铁面板服务", value)
        return await bot.send(f"已设置崩铁面板服务为：{value}")

    if key.lower() == "uid":
        if value in {"列表", "list", "ls"}:
            user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
            return await bot.send("【崩铁 UID 列表】\n" + _uid_list_text(user_cfg, "sr"))
        if value.startswith(("切换", "选择", "使用")):
            value = value.replace("切换", "", 1).replace("选择", "", 1).replace("使用", "", 1).strip()
            return await _switch_uid(bot, ev, value, "sr")
        if value in {"", "解绑", "删除", "unset", "clear"}:
            await unbind_uid(ev.user_id, ev.bot_id, game="sr")
            await add_history(ev, "崩铁UID解绑", "ok")
            return await bot.send("已解绑崩铁 UID")
        if not value.isdigit() or len(value) not in {9, 10}:
            return await bot.send(f"请填写正确 UID，例如：{prefix}崩铁设置uid 800000001")
        await bind_uid(ev.user_id, ev.bot_id, value, game="sr")
        await add_history(ev, "崩铁UID绑定", value)
        return await bot.send(f"已绑定崩铁 UID：{value}\n之后可直接使用：{prefix}崩铁面板 / {prefix}崩铁黄泉面板")

    await bot.send(f"暂不支持该设置项，请发送 {prefix}崩铁设置 查看帮助")
