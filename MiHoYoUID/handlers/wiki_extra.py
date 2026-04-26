from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..material_service import build_today_material
from ..panel_renderer import render_material_image, render_status_card

sv_wiki_extra = SV("GsCoreMiao素材Wiki")

MATERIAL_COMMANDS = (
    "原神今日素材",
    "原神今天素材",
    "原神每日材料",
    "原神今日材料",
    "原神明日材料",
    "原神明天材料",
    "今日素材",
    "今天素材",
    "每日材料",
    "今日材料",
    "明日材料",
    "明天材料",
    "周一素材",
    "周一材料",
    "周一天赋",
    "周二素材",
    "周二材料",
    "周二天赋",
    "周三素材",
    "周三材料",
    "周三天赋",
    "周四素材",
    "周四材料",
    "周四天赋",
    "周五素材",
    "周五材料",
    "周五天赋",
    "周六素材",
    "周六材料",
    "周六天赋",
    "周日素材",
    "周日材料",
    "周日天赋",
    "周天素材",
    "周天材料",
    "周天天赋",
    "原神周一素材",
    "原神周一材料",
    "原神周一天赋",
    "原神周二素材",
    "原神周二材料",
    "原神周二天赋",
    "原神周三素材",
    "原神周三材料",
    "原神周三天赋",
    "原神周四素材",
    "原神周四材料",
    "原神周四天赋",
    "原神周五素材",
    "原神周五材料",
    "原神周五天赋",
    "原神周六素材",
    "原神周六材料",
    "原神周六天赋",
    "原神周日素材",
    "原神周日材料",
    "原神周日天赋",
    "原神周天素材",
    "原神周天材料",
    "原神周天天赋",
)

ZZZ_CALENDAR_COMMANDS = (
    "绝区零日历",
    "绝区零日历列表",
    "绝区零活动",
    "ZZZ日历",
    "ZZZ日历列表",
    "ZZZ活动",
    "zzz日历",
    "zzz日历列表",
    "zzz活动",
)


@sv_wiki_extra.on_fullmatch(MATERIAL_COMMANDS, block=True)
async def send_today_material_fullmatch(bot: Bot, ev: Event):
    await _send_today_material(bot, ev)


@sv_wiki_extra.on_regex(r"^(原神)?(今日素材|今天素材|每日材料|今日材料|明日材料|明天材料|周[1-7一二三四五六日天]素材|周[1-7一二三四五六日天]材料|周[1-7一二三四五六日天]天赋)$", block=True)
async def send_today_material(bot: Bot, ev: Event):
    await _send_today_material(bot, ev)


async def _send_today_material(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = getattr(ev, "raw_text", "") or ""
    await bot.send(await render_material_image(build_today_material(text)))


@sv_wiki_extra.on_fullmatch(ZZZ_CALENDAR_COMMANDS, block=True)
async def send_zzz_calendar_fullmatch(bot: Bot, ev: Event):
    await _send_zzz_calendar(bot, ev)


@sv_wiki_extra.on_regex(r"^(绝区零|ZZZ|zzz)(日历|日历列表|活动)$", block=True)
async def send_zzz_calendar(bot: Bot, ev: Event):
    await _send_zzz_calendar(bot, ev)


async def _send_zzz_calendar(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    await bot.send(await render_status_card("喵喵绝区零日历", ["已预留 miao-plugin 同款日历入口。", "当前本仓库尚未配置绝区零公告 API，避免返回错误数据。", "原神/崩铁日历可直接使用：喵喵原神日历、喵喵崩铁日历。"], "日历入口"))