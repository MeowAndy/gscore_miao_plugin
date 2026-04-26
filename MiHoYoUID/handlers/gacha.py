from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..gacha_service import analyze_gacha, extract_uid
from ..panel_renderer import render_gacha_image
from ..settings import merge_user_cfg
from ..store import get_user_cfg

sv_gacha = SV("GsCoreMiao抽卡统计")


async def _uid_from_event(ev: Event, text: str, game: str) -> str:
    uid = extract_uid(text)
    if uid:
        return uid
    cfg = merge_user_cfg(await get_user_cfg(ev.user_id, ev.bot_id))
    if game == "sr":
        return str(cfg.get("sr_uid") or "")
    return str(cfg.get("uid") or "")


GACHA_COMMANDS = (
    "抽卡统计",
    "抽卡记录",
    "抽奖记录",
    "祈愿统计",
    "祈愿记录",
    "抽卡分析",
    "角色池抽卡统计",
    "角色抽卡统计",
    "武器池抽卡统计",
    "武器抽卡统计",
    "常驻池抽卡统计",
    "常驻抽卡统计",
    "集录池抽卡统计",
    "集录抽卡统计",
    "原神抽卡统计",
    "原神抽卡记录",
    "原神祈愿统计",
    "原神角色池抽卡统计",
    "原神武器池抽卡统计",
    "原神常驻池抽卡统计",
    "原神集录池抽卡统计",
    "崩铁抽卡统计",
    "崩铁抽卡记录",
    "崩铁角色池抽卡统计",
    "崩铁光锥池抽卡统计",
    "崩铁常驻池抽卡统计",
    "星铁抽卡统计",
    "星铁抽卡记录",
    "星铁角色池抽卡统计",
    "星铁光锥池抽卡统计",
    "星铁常驻池抽卡统计",
)


@sv_gacha.on_fullmatch(GACHA_COMMANDS, block=True)
async def send_gacha_stat_fullmatch(bot: Bot, ev: Event):
    await _send_gacha_stat(bot, ev)


@sv_gacha.on_regex(r"^(?:喵喵|miao|MM)?(?P<game>原神|崩铁|星铁)?(?P<pool>角色|武器|光锥|常驻|集录|up|UP)?池?(?P<cmd>抽卡记录|抽卡统计|抽奖记录|祈愿记录|祈愿统计|抽卡分析)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_gacha_stat(bot: Bot, ev: Event):
    await _send_gacha_stat(bot, ev)


@sv_gacha.on_regex(r"^(?:喵喵|miao|MM)?(?P<game>原神|崩铁|星铁)?(?P<pool>角色|武器|光锥|常驻|集录|up|UP)?池?(?P<cmd>抽卡记录|抽卡统计|抽奖记录|祈愿记录|祈愿统计|抽卡分析)\s+(?P<uid>\d{9,10})$", block=True)
async def send_gacha_stat_with_uid(bot: Bot, ev: Event):
    await _send_gacha_stat(bot, ev)


async def _send_gacha_stat(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    text = getattr(ev, "raw_text", "") or ""
    game = "sr" if data.get("game") in {"崩铁", "星铁"} or "崩铁" in text or "星铁" in text else "gs"
    uid = await _uid_from_event(ev, text or (data.get("uid") or ""), game)
    if not uid:
        name = "崩铁" if game == "sr" else "原神"
        return await bot.send(f"请先绑定 {name} UID，或在命令后携带 UID。")
    result = analyze_gacha(game, str(ev.user_id or ""), uid, text)
    await bot.send(await render_gacha_image(result))