from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..material_service import build_today_material
from ..panel_renderer import render_material_image, render_status_card

sv_wiki_extra = SV("GsCoreMiao素材Wiki")


@sv_wiki_extra.on_regex(r"^(今日素材|今天素材|每日材料|今日材料|明日材料|明天材料|周[一二三四五六日天]素材|周[一二三四五六日天]材料|周[一二三四五六日天]天赋)$", block=True)
async def send_today_material(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = getattr(ev, "raw_text", "") or ""
    await bot.send(await render_material_image(build_today_material(text)))


@sv_wiki_extra.on_regex(r"^(绝区零|ZZZ|zzz)(日历|日历列表|活动)$", block=True)
async def send_zzz_calendar(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    await bot.send(await render_status_card("喵喵绝区零日历", ["已预留 miao-plugin 同款日历入口。", "当前本仓库尚未配置绝区零公告 API，避免返回错误数据。", "原神/崩铁日历可直接使用：喵喵原神日历、喵喵崩铁日历。"], "日历入口"))