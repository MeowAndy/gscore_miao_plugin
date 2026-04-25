from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..mys_service import (daily_sign, daily_sign_starrail, fetch_sign_info,
                           fetch_starrail_roles, fetch_starrail_sign_info,
                           normalize_cookie, qrcode_login_cookie,
                           validate_cookie)
from ..settings import merge_user_cfg
from ..store import (bind_mys_cookie, get_user_cfg, set_user_cfg,
                     unbind_mys_cookie)

sv_login = SV("GsCoreMiao登录签到")


def _role_uid(role: dict) -> str:
    return str(role.get("game_uid") or role.get("uid") or "")


def _role_name(role: dict) -> str:
    return str(role.get("nickname") or role.get("name") or "旅行者")


def _role_region(role: dict) -> str:
    return str(role.get("region_name") or role.get("region") or "")


def _pick_role_uid(roles: list[dict], uid: str = "") -> str:
    if uid:
        for role in roles:
            if _role_uid(role) == uid:
                return uid
        return ""
    return _role_uid(roles[0]) if roles else ""


def _role_uids(roles: list[dict], uid: str = "") -> list[str]:
    uids: list[str] = []
    for role in roles:
        role_uid = _role_uid(role)
        if not role_uid or role_uid in uids:
            continue
        if uid and role_uid != uid:
            continue
        uids.append(role_uid)
    return uids


def _mask_cookie(cookie: str) -> str:
    if len(cookie) <= 16:
        return "已保存"
    return f"{cookie[:8]}...{cookie[-8:]}"


async def run_daily_sign_for_cfg(cfg: dict, specified_uid: str = "") -> tuple[list[str], list[str]]:
    cookie = str(cfg.get("mys_cookie") or "")
    if not cookie:
        return [], ["当前未登录"]
    specified_uid = (specified_uid or "").strip()
    default_uid = str(cfg.get("uid") or "").strip()
    gs_roles = cfg.get("mys_roles") or []
    sr_roles = cfg.get("mys_sr_roles") or []
    if not sr_roles:
        try:
            sr_roles = await fetch_starrail_roles(cookie)
        except Exception:
            sr_roles = []

    gs_uids = _role_uids(gs_roles, specified_uid)
    if not specified_uid and not gs_uids and default_uid:
        picked_uid = _pick_role_uid(gs_roles, default_uid)
        if picked_uid:
            gs_uids = [picked_uid]
    sr_uids = _role_uids(sr_roles, specified_uid)
    sections: list[str] = []
    errors: list[str] = []

    for gs_uid in gs_uids:
        try:
            before = await fetch_sign_info(cookie, gs_uid)
            signed = bool(before.get("is_sign"))
            raw = await daily_sign(cookie, gs_uid) if not signed else {"message": "OK", "retcode": -5003}
            after = await fetch_sign_info(cookie, gs_uid)
            total = after.get("total_sign_day") or before.get("total_sign_day") or "?"
            today = after.get("today") or before.get("today") or ""
            status = "今日已签到" if signed or raw.get("retcode") == -5003 else "签到成功"
            sections.append(
                "【原神签到】\n"
                f"🆔 UID：{gs_uid}\n"
                f"✅ 状态：{status}\n"
                f"📅 累计签到：{total} 天\n"
                f"🕒 日期：{today}"
            )
        except Exception as e:
            errors.append(f"原神 {gs_uid}：{e}")

    for sr_uid in sr_uids:
        try:
            before = await fetch_starrail_sign_info(cookie, sr_uid)
            signed = bool(before.get("is_sign"))
            raw = await daily_sign_starrail(cookie, sr_uid) if not signed else {"message": "OK", "retcode": -5003}
            after = await fetch_starrail_sign_info(cookie, sr_uid)
            total = after.get("total_sign_day") or before.get("total_sign_day") or "?"
            today = after.get("today") or before.get("today") or ""
            status = "今日已签到" if signed or raw.get("retcode") == -5003 else "签到成功"
            sections.append(
                "【崩铁签到】\n"
                f"🆔 UID：{sr_uid}\n"
                f"✅ 状态：{status}\n"
                f"📅 累计签到：{total} 天\n"
                f"🕒 日期：{today}"
            )
        except Exception as e:
            errors.append(f"崩铁 {sr_uid}：{e}")
    return sections, errors


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
        return await bot.send(f"登录失败：{e}\n请确认 Cookie 未过期且已绑定原神或崩铁账号。")
    try:
        sr_roles = await fetch_starrail_roles(cookie)
    except Exception:
        sr_roles = []
    await bind_mys_cookie(ev.user_id, ev.bot_id, cookie, roles, sr_roles)
    lines = ["【喵喵登录成功】", f"已保存米游社 Cookie：{_mask_cookie(cookie)}", "绑定角色："]
    for idx, role in enumerate(roles[:8], start=1):
        lines.append(f"原神{idx}. {_role_name(role)} UID {_role_uid(role)} {_role_region(role)}")
    for idx, role in enumerate(sr_roles[:8], start=1):
        lines.append(f"崩铁{idx}. {_role_name(role)} UID {_role_uid(role)} {_role_region(role)}")
    lines.append("之后可使用：喵喵签到 / 喵喵查看登录 / 喵喵删除登录")
    await bot.send("\n".join(lines))


@sv_login.on_fullmatch(("查看登录", "我的登录", "登录信息"), block=True)
async def send_login_info(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    cfg = await get_user_cfg(ev.user_id, ev.bot_id)
    cookie = str(cfg.get("mys_cookie") or "")
    roles = cfg.get("mys_roles") or []
    sr_roles = cfg.get("mys_sr_roles") or []
    if not cookie:
        return await bot.send("当前未登录。请私聊发送：喵喵登录 <米游社Cookie>")
    lines = ["【喵喵登录信息】", f"Cookie：{_mask_cookie(cookie)}", f"默认 UID：{cfg.get('uid') or '-'}"]
    if roles:
        lines.append("绑定原神角色：")
        for idx, role in enumerate(roles[:8], start=1):
            lines.append(f"{idx}. {_role_name(role)} UID {_role_uid(role)} {_role_region(role)}")
    if sr_roles:
        lines.append("绑定崩铁角色：")
        for idx, role in enumerate(sr_roles[:8], start=1):
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
    cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    if not str(cfg.get("mys_cookie") or ""):
        return await bot.send("当前未登录，无法签到。请私聊发送：喵喵登录 <米游社Cookie>")
    specified_uid = ((ev.regex_dict or {}).get("uid") or "").strip()
    sections, errors = await run_daily_sign_for_cfg(cfg, specified_uid)

    if sections:
        return await bot.send("\n\n".join(sections))
    if errors:
        return await bot.send("签到失败：" + "；".join(errors))
    await bot.send("没有找到可签到的原神或崩铁 UID，请重新登录或使用：喵喵签到 <UID>")


@sv_login.on_fullmatch(("开启自动签到", "启用自动签到"), block=True)
async def send_enable_auto_sign(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnableAutoDailySign").data:
        return await bot.send("自动签到功能已在网页配置中关闭")
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    cfg = await get_user_cfg(ev.user_id, ev.bot_id)
    if not str(cfg.get("mys_cookie") or ""):
        return await bot.send("当前未登录，无法开启自动签到。请先私聊发送：喵喵登录 <米游社Cookie>")
    await set_user_cfg(ev.user_id, ev.bot_id, {"auto_daily_sign": True})
    sign_time = MiaoConfig.get_config("AutoDailySignTime").data or ["8", "0"]
    hour = str(sign_time[0]).zfill(2) if len(sign_time) > 0 else "08"
    minute = str(sign_time[1]).zfill(2) if len(sign_time) > 1 else "00"
    await bot.send(f"已开启自动签到，将于每天 {hour}:{minute} 自动执行")


@sv_login.on_fullmatch(("关闭自动签到", "停用自动签到"), block=True)
async def send_disable_auto_sign(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    await set_user_cfg(ev.user_id, ev.bot_id, {"auto_daily_sign": False})
    await bot.send("已关闭自动签到")