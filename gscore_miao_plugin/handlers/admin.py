import json

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import add_history, can_use_plugin, get_recent_history_lines
from ..config import MiaoConfig
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


@sv_admin.on_regex(r"^#?设置\s*(?P<key>[^\s]+)?\s*(?P<value>.*)$", block=True)
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
        panel_server = user_cfg.get("panel_server", "auto")
        uid = user_cfg.get("uid") or "未绑定"
        custom_splash = user_cfg.get("custom_splash", True)
        team_calc = user_cfg.get("team_calc", False)
        show_star = user_cfg.get("show_star", False)
        comma_group = user_cfg.get("comma_group", 3)
        return await bot.send(
            "【喵喵设置】\n"
            f"绑定UID: {uid}\n"
            f"面板服务: {panel_server}\n"
            f"面板图: {'开启' if custom_splash else '关闭'}\n"
            f"组队伤害: {'开启' if team_calc else '关闭'}\n"
            f"星级显示: {'开启' if show_star else '关闭'}\n"
            f"数字分组: {comma_group}\n\n"
            "可用：\n"
            f"喵喵设置面板服务 <{_schema_desc()}>\n"
            "喵喵设置uid <UID>\n"
            "喵喵设置面板图 <开启|关闭>\n"
            "喵喵设置组队 <开启|关闭>\n"
            "喵喵设置星级 <开启|关闭>\n"
            "喵喵设置逗号 <2-8>\n"
            "喵喵设置历史\n"
            "喵喵设置导出\n"
            "喵喵设置重置"
        )

    if key == "历史":
        lines = await get_recent_history_lines(ev)
        if not lines:
            return await bot.send("暂无设置历史记录")
        return await bot.send("【喵喵设置历史】\n" + "\n".join(lines[:20]))

    if key == "导出":
        if not MiaoConfig.get_config("EnableSettingExport").data:
            return await bot.send("设置导出功能已关闭")
        user_cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
        text = json.dumps(user_cfg, ensure_ascii=False, indent=2)
        await add_history(ev, "设置导出", "ok")
        return await bot.send(f"【喵喵设置导出】\n{text}")

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
        if value in {"", "解绑", "删除", "unset", "clear"}:
            await unbind_uid(ev.user_id, ev.bot_id)
            await add_history(ev, "UID解绑", "ok")
            return await bot.send("已解绑 UID")
        if not value.isdigit() or len(value) not in {9, 10}:
            return await bot.send("请填写正确 UID，例如：喵喵设置uid 100000001")
        await bind_uid(ev.user_id, ev.bot_id, value)
        await add_history(ev, "UID绑定", value)
        return await bot.send(f"已绑定 UID：{value}\n之后可直接使用：喵喵面板 / 喵喵雷神面板")

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
            return await bot.send("请填写数字，例如：喵喵设置逗号 3")
        max_group = int(MiaoConfig.get_config("MaxCommaGroup").data)
        if n < 2 or n > max_group:
            return await bot.send(f"数字分组范围应为 2-{max_group}")
        await set_user_cfg(ev.user_id, ev.bot_id, {"comma_group": n})
        await add_history(ev, "数字分组", str(n))
        return await bot.send(f"已设置数字分组为：{n}")

    await bot.send("暂不支持该设置项，请发送 #喵喵设置 查看帮助")
