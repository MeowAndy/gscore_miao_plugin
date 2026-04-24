from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..mys_service import (daily_sign, fetch_sign_info, normalize_cookie,
                           qrcode_login_cookie, validate_cookie)
from ..store import bind_mys_cookie, get_user_cfg, unbind_mys_cookie

sv_login = SV("GsCoreMiao登录签到")


def _role_uid(role: dict) -> str:
    return str(role.get("game_uid") or role.get("uid") or "")


def _role_name(role: dict) -> str:
    return str(role.get("nickname") or role.get("name") or "旅行者")


def _role_region(role: dict) -> str:
    return str(role.get("region_name") or role.get("region") or "")


def _mask_cookie(cookie: str) -> str:
    if len(cookie) <= 16:
        return "已保存"
    return f"{cookie[:8]}...{cookie[-8:]}"


@sv_login.on_regex(r"^(登录|绑定cookie|绑定Cookie|绑定米游社)\s*(?P<cookie>.*)$", block=True)
async def send_login(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableMysLogin").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    raw = ((ev.regex_dict or {}).get("cookie") or "").strip()
    if not raw:
        if not MiaoConfig.get_config("EnableMysQrLogin").data:
            return await bot.send(
                "【喵喵登录】\n"
                "扫码登录未开启，请私聊发送米游社 Cookie，例如：\n"
                "喵喵登录 cookie_token=xxx; account_id=xxx; ltuid=xxx; ltoken=xxx\n\n"
                f"教程：{MiaoConfig.get_config('LoginHelpUrl').data}"
            )
        try:
            await bot.send("正在创建米游社扫码登录二维码，请稍等...")
            cookie = await qrcode_login_cookie(bot, ev)
        except Exception as e:
            return await bot.send(f"扫码登录失败：{e}\n也可以使用：喵喵登录 <米游社Cookie>")
    else:
        cookie = normalize_cookie(raw)
    if "=" not in cookie:
        return await bot.send("Cookie 格式不正确，请发送 key=value; key=value 格式。")
    try:
        roles = await validate_cookie(cookie)
    except Exception as e:
        return await bot.send(f"登录失败：{e}\n请确认 Cookie 未过期且已绑定原神账号。")
    await bind_mys_cookie(ev.user_id, ev.bot_id, cookie, roles)
    lines = ["【喵喵登录成功】", f"已保存米游社 Cookie：{_mask_cookie(cookie)}", "绑定角色："]
    for idx, role in enumerate(roles[:8], start=1):
        lines.append(f"{idx}. {_role_name(role)} UID {_role_uid(role)} {_role_region(role)}")
    lines.append("之后可使用：喵喵签到 / 喵喵查看登录 / 喵喵删除登录")
    await bot.send("\n".join(lines))


@sv_login.on_fullmatch(("查看登录", "我的登录", "登录信息"), block=True)
async def send_login_info(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    cfg = await get_user_cfg(ev.user_id, ev.bot_id)
    cookie = str(cfg.get("mys_cookie") or "")
    roles = cfg.get("mys_roles") or []
    if not cookie:
        return await bot.send("当前未登录。请私聊发送：喵喵登录 <米游社Cookie>")
    lines = ["【喵喵登录信息】", f"Cookie：{_mask_cookie(cookie)}", f"默认 UID：{cfg.get('uid') or '-'}"]
    if roles:
        lines.append("绑定角色：")
        for idx, role in enumerate(roles[:8], start=1):
            lines.append(f"{idx}. {_role_name(role)} UID {_role_uid(role)} {_role_region(role)}")
    await bot.send("\n".join(lines))


@sv_login.on_fullmatch(("删除登录", "退出登录", "解绑cookie", "解绑Cookie"), block=True)
async def send_delete_login(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    await unbind_mys_cookie(ev.user_id, ev.bot_id)
    await bot.send("已删除本地保存的米游社 Cookie。")


@sv_login.on_regex(r"^(签到|米游社签到|原神签到)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_daily_sign(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableDailySign").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    cfg = await get_user_cfg(ev.user_id, ev.bot_id)
    cookie = str(cfg.get("mys_cookie") or "")
    if not cookie:
        return await bot.send("当前未登录，无法签到。请私聊发送：喵喵登录 <米游社Cookie>")
    uid = ((ev.regex_dict or {}).get("uid") or "").strip() or str(cfg.get("uid") or "").strip()
    if not uid:
        roles = cfg.get("mys_roles") or []
        uid = _role_uid(roles[0]) if roles else ""
    if not uid:
        return await bot.send("没有找到可签到 UID，请重新登录或使用：喵喵签到 <UID>")
    try:
        before = await fetch_sign_info(cookie, uid)
        signed = bool(before.get("is_sign"))
        raw = await daily_sign(cookie, uid) if not signed else {"message": "OK", "retcode": -5003}
        after = await fetch_sign_info(cookie, uid)
    except Exception as e:
        return await bot.send(f"签到失败：{e}")
    total = after.get("total_sign_day") or before.get("total_sign_day") or "?"
    today = after.get("today") or before.get("today") or ""
    status = "今日已签到" if signed or raw.get("retcode") == -5003 else "签到成功"
    await bot.send(
        "【原神签到】\n"
        f"🆔 UID：{uid}\n"
        f"✅ 状态：{status}\n"
        f"📅 累计签到：{total} 天\n"
        f"🕒 日期：{today}"
    )