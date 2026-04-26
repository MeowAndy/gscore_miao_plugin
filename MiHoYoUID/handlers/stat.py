from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..panel_renderer import render_stat_images
from ..stat_service import (build_stat_placeholder, fetch_stat,
                            normalize_stat_rows)

sv_stat = SV("GsCoreMiao统计")

STAT_COMMANDS = (
    "原神角色持有率",
    "角色命座统计",
    "角色5命统计",
    "深渊出场率",
    "深渊使用率",
    "深渊组队",
    "深渊配队",
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


def _kind_title(text: str) -> tuple[str, str]:
    if "组队" in text or "配队" in text:
        return "team", "喵喵深渊组队"
    if "幽境" in text or "危战" in text:
        return "hard", "喵喵幽境危战统计"
    if "持有" in text or "命座" in text or "5命" in text or "满命" in text:
        return "cons", "喵喵原神角色持有/命座统计"
    if "幻想" in text or "剧诗" in text:
        return "abyss", "喵喵幻想真境剧诗数据"
    return "abyss", "喵喵深渊出场率"


@sv_stat.on_fullmatch(STAT_COMMANDS + PREFIXED_STAT_COMMANDS, block=True)
async def send_public_stat_fullmatch(bot: Bot, ev: Event):
    await _send_public_stat(bot, ev)


@sv_stat.on_fullmatch(SR_OWNERSHIP_COMMANDS + PREFIXED_SR_OWNERSHIP_COMMANDS, block=True)
async def send_sr_ownership_unavailable(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    return await bot.send("崩铁目前没有做角色持有量排行，暂不支持该指令。")


@sv_stat.on_regex(rf"^(?P<cmd>{STAT_COMMAND_PATTERN})$", block=True)
async def send_public_stat(bot: Bot, ev: Event):
    await _send_public_stat(bot, ev)


async def _send_public_stat(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = (ev.regex_dict or {}).get("cmd") or getattr(ev, "raw_text", "") or ""
    kind, title = _kind_title(text)
    try:
        payload = await fetch_stat(kind)
        data = normalize_stat_rows(payload, limit=999)
    except Exception as e:
        data = build_stat_placeholder(kind, f"统计接口获取失败：{e}")
    images = await render_stat_images(data, title)
    if len(images) == 1:
        return await bot.send(images[0])
    try:
        await bot.send(MessageSegment.node(images))
    except Exception:
        for image in images:
            await bot.send(image)
