from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..calendar_service import fetch_calendar
from ..config import MiaoConfig
from ..panel_renderer import render_calendar_images

sv_calendar = SV("GsCoreMiao活动日历")


async def _send_calendar(bot: Bot, ev: Event, game: str, list_mode: bool) -> None:
    if not MiaoConfig.get_config("EnableActivityCalendar").data:
        return
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    try:
        data = await fetch_calendar(game, list_mode=list_mode)
        images = await render_calendar_images(data, page_size=12)
        if len(images) == 1:
            return await bot.send(images[0])
        try:
            await bot.send(MessageSegment.node(images))
        except Exception as send_error:
            logger.warning(f"[喵喵日历] 合并消息发送失败，改为逐张发送：{send_error!r}")
            for image in images:
                await bot.send(image)
    except Exception as e:
        name = "原神" if game == "gs" else "崩铁"
        logger.exception(f"[喵喵日历] {name}日历获取失败")
        detail = str(e).strip() or repr(e) or type(e).__name__
        await bot.send(f"{name}日历获取失败：{detail}")


@sv_calendar.on_regex(r"^(崩铁|星铁)(日历|日历列表|活动)$", block=True)
async def send_starrail_calendar(bot: Bot, ev: Event):
    text = getattr(ev, "raw_text", "") or ""
    await _send_calendar(bot, ev, "sr", "列表" in text or text.endswith("活动"))


@sv_calendar.on_regex(r"^原神(日历|日历列表|活动)$", block=True)
async def send_genshin_calendar(bot: Bot, ev: Event):
    text = getattr(ev, "raw_text", "") or ""
    await _send_calendar(bot, ev, "gs", "列表" in text or text.endswith("活动"))
