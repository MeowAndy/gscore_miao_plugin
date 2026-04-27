from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..mys_service import fetch_hard_challenge, fetch_role_combat
from ..panel_renderer import render_stat_images
from ..stat_service import (build_stat_placeholder, fetch_stat,
                            normalize_stat_rows)
from ..store import get_user_cfg

sv_stat = SV("GsCoreMiao统计")

STAT_COMMANDS = (
    "原神角色持有率",
    "角色命座统计",
    "角色5命统计",
    "深渊出场率",
    "深渊使用率",
    "深渊组队",
    "深渊配队",
    "深渊配对",
    "深渊数据",
    "幻想真境剧诗数据",
    "幻想真境数据",
    "幽境危战出场率",
    "幽境危战使用率",
    "幽境危战数据",
)

SR_OWNERSHIP_COMMANDS = (
    "崩铁角色持有率",
    "星铁角色持有率",
)

STAT_PREFIXES = ("喵喵", "miao", "MM")
PREFIXED_STAT_COMMANDS = tuple(f"{prefix}{cmd}" for prefix in STAT_PREFIXES for cmd in STAT_COMMANDS)
PREFIXED_SR_OWNERSHIP_COMMANDS = tuple(f"{prefix}{cmd}" for prefix in STAT_PREFIXES for cmd in SR_OWNERSHIP_COMMANDS)
STAT_COMMAND_PATTERN = "|".join(STAT_COMMANDS + PREFIXED_STAT_COMMANDS)
ABYSS_PCT_PATTERN = r"(?:喵喵|miao|MM)?(?:深渊|幽境|危战|幽境危战)(?:第?.{1,3}层)?(?:角色)?(?:出场|使用)(?:率|统计)?"
ABYSS_TEAM_PATTERN = r"(?:喵喵|miao|MM)?深渊(?:组队|配队|配对)"
ABYSS_SUMMARY_PATTERN = r"(?:喵喵|上传|miao|MM)?(?:深渊|深境|深境螺旋)\s*[0-9]*(?:数据)?"
ROLE_COMBAT_PATTERN = r"(?:喵喵|miao|MM)?(?:本期|上期)?(?:幻想|幻境|剧诗|幻想真境剧诗)\s*[0-9]*(?:数据)?"
HARD_SUMMARY_PATTERN = r"(?:喵喵|miao|MM)?(?:本期|上期)?(?:幽境|危战|幽境危战)(?:单人|单挑|组队|多人|合作|最佳)?\s*[0-9]*(?:数据)?"


def _kind_title(text: str) -> tuple[str, str]:
    if "组队" in text or "配队" in text or "配对" in text:
        return "team", "喵喵深渊配队建议" if "配" in text else "喵喵深渊组队"
    if "幻想" in text or "幻境" in text or "剧诗" in text:
        return "role_combat", "喵喵幻想真境剧诗数据"
    if ("幽境" in text or "危战" in text) and "数据" in text:
        return "hard_summary", "喵喵幽境危战数据"
    if "深渊" in text and "数据" in text:
        return "abyss_summary", "喵喵深渊数据"
    if "幽境" in text or "危战" in text:
        return "hard_own" if "出场" in text else "hard_use", "喵喵幽境危战出场率" if "出场" in text else "喵喵幽境危战使用率"
    if "持有" in text:
        return "cons", "喵喵原神角色持有率"
    if "5命" in text or "五命" in text:
        return "cons5", "喵喵原神角色5命统计"
    if "命座" in text or "满命" in text:
        return "cons_dist", "喵喵原神角色命座统计"
    return "abyss_own" if "出场" in text else "abyss_use", "喵喵深渊出场率" if "出场" in text else "喵喵深渊使用率"


@sv_stat.on_fullmatch(STAT_COMMANDS + PREFIXED_STAT_COMMANDS, block=True)
async def send_public_stat_fullmatch(bot: Bot, ev: Event):
    await _send_public_stat(bot, ev)


@sv_stat.on_fullmatch(SR_OWNERSHIP_COMMANDS + PREFIXED_SR_OWNERSHIP_COMMANDS, block=True)
async def send_sr_ownership_unavailable(bot: Bot, ev: Event):
    if not MiaoConfig.get_config("EnablePublicStat").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    return await bot.send("崩铁目前没有做角色持有量排行，暂不支持该指令。")


@sv_stat.on_regex(rf"^(?P<cmd>{STAT_COMMAND_PATTERN})$", block=True)
async def send_public_stat(bot: Bot, ev: Event):
    await _send_public_stat(bot, ev)


@sv_stat.on_regex(rf"^(?P<cmd>{ABYSS_PCT_PATTERN}|{ABYSS_TEAM_PATTERN}|{ABYSS_SUMMARY_PATTERN})$", block=True)
async def send_miao_abyss_stat(bot: Bot, ev: Event):
    await _send_public_stat(bot, ev)


@sv_stat.on_regex(rf"^(?P<cmd>{ROLE_COMBAT_PATTERN}|{HARD_SUMMARY_PATTERN})$", block=True)
async def send_miao_personal_stat(bot: Bot, ev: Event):
    await _send_public_stat(bot, ev)


def _empty_stat_message(kind: str, title: str, data: dict) -> str:
    clean_title = title.removeprefix("喵喵")
    if kind == "role_combat":
        return f"你的{clean_title}为空。"
    if kind == "hard_summary":
        return f"你的{clean_title}为空。"
    return f"{title}数据为空。"


async def _send_public_stat(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = (ev.regex_dict or {}).get("cmd") or getattr(ev, "raw_text", "") or ""
    kind, title = _kind_title(text)
    if kind in {"role_combat", "hard_summary"}:
        if not MiaoConfig.get_config("EnablePersonalChallengeStat").data:
            return
        cfg = await get_user_cfg(ev.user_id, ev.bot_id)
        if not str(cfg.get("mys_cookie") or ""):
            return await bot.send(f"请绑定CK后再使用{title}。")
        uid = str(cfg.get("uid") or "").strip()
        if not uid:
            return await bot.send(f"你的{title.removeprefix('喵喵')}为空。")
        try:
            cookie = str(cfg.get("mys_cookie") or "")
            previous = "上期" in text
            if kind == "role_combat":
                payload = {"kind": kind, "raw": await fetch_role_combat(cookie, uid, True), "cached": False, "personal": True, "previous": previous}
            else:
                payload = {"kind": kind, "raw": await fetch_hard_challenge(cookie, uid), "cached": False, "personal": True, "previous": previous}
            data = normalize_stat_rows(payload, limit=999)
        except Exception:
            data = build_stat_placeholder(kind, f"你的{title.removeprefix('喵喵')}为空。")
        if not data.get("rows"):
            return await bot.send(_empty_stat_message(kind, title, data))
        images = await render_stat_images(data, title)
        if len(images) == 1:
            return await bot.send(images[0])
        try:
            return await bot.send(MessageSegment.node(images))
        except Exception:
            for image in images:
                await bot.send(image)
            return
    if not MiaoConfig.get_config("EnablePublicStat").data:
        return
    try:
        payload = await fetch_stat(kind)
        data = normalize_stat_rows(payload, limit=999)
    except Exception as e:
        data = build_stat_placeholder(kind, f"统计接口获取失败：{e}")
    if not data.get("rows"):
        return await bot.send(_empty_stat_message(kind, title, data))
    images = await render_stat_images(data, title)
    if len(images) == 1:
        return await bot.send(images[0])
    try:
        await bot.send(MessageSegment.node(images))
    except Exception:
        for image in images:
            await bot.send(image)
