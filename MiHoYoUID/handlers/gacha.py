from __future__ import annotations

import json
import re

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..gacha_service import (analyze_gacha, extract_uid, import_gacha_authkey,
                             import_gacha_json)
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


def _game_from_text(text: str) -> str:
    return "sr" if "崩铁" in text or "星铁" in text else "gs"


def _strip_import_payload(text: str) -> str:
    text = re.sub(r"^(?:喵喵|miao|MM)?导入(?:原神|崩铁|星铁)抽卡记录", "", text or "", flags=re.I).strip()
    return text


def _game_name(game: str) -> str:
    return "崩铁" if game == "sr" else "原神"


def _import_help_command(game: str) -> str:
    return f"MM导入{_game_name(game)}抽卡记录帮助"


def _extract_json_payload(text: str) -> object | None:
    payload = _strip_import_payload(text)
    if not payload:
        return None
    start_candidates = [idx for idx in (payload.find("{"), payload.find("[")) if idx >= 0]
    if not start_candidates:
        return None
    raw = payload[min(start_candidates):].strip()
    try:
        return json.loads(raw)
    except Exception:
        return None


def _format_import_result(result: dict) -> str:
    if not result.get("ok"):
        return f"抽卡记录导入失败：{result.get('message') or '未知错误'}"
    game_name = _game_name(str(result.get("game") or "gs"))
    lines = [
        f"【{game_name}抽卡记录导入完成】",
        f"UID：{result.get('uid')}",
        f"新增：{result.get('added', 0)} 条",
        f"当前总计：{result.get('total', 0)} 条",
    ]
    pools = result.get("pools") or {}
    if pools:
        lines.append("卡池：" + " / ".join(f"{name}{count}" for name, count in pools.items()))
    lines.append("可继续使用：MM抽卡统计 / MM崩铁抽卡统计")
    return "\n".join(lines)


def _import_help(game: str) -> str:
    game_name = _game_name(game)
    action = "跃迁" if game == "sr" else "祈愿"
    command = _import_help_command(game)
    return (
        f"【{command}】\n"
        "miao-plugin 本体只读取本地 data/gachaJson 与 data/srJson，不负责抓取导入；本迁移版已补齐导入入口，并保存成同款目录结构。\n\n"
        f"方式一：发送游戏内{game_name}{action}历史链接\n"
        f"1. 打开游戏内{action}历史记录。\n"
        "2. 复制带 authkey 的链接。\n"
        f"3. 发送：MM导入{game_name}抽卡记录 <链接>\n\n"
        "方式二：导入 UIGF/JSON 文本\n"
        f"发送：MM导入{game_name}抽卡记录 <JSON内容>\n\n"
        "注意：authkey 通常有效期较短；如果提示过期，请重新打开游戏历史记录复制链接。"
    )


def _empty_gacha_message(game: str) -> str:
    return f"当前{_game_name(game)}抽卡记录为空，请导入抽卡记录，发送【{_import_help_command(game)}】查看详情。"


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
    "UP池抽卡统计",
    "up池抽卡统计",
    "原神抽卡统计",
    "原神抽卡记录",
    "原神祈愿统计",
    "原神抽卡分析",
    "原神角色池抽卡统计",
    "原神武器池抽卡统计",
    "原神常驻池抽卡统计",
    "原神集录池抽卡统计",
    "原神UP池抽卡统计",
    "原神up池抽卡统计",
    "崩铁抽卡统计",
    "崩铁抽卡记录",
    "崩铁祈愿统计",
    "崩铁抽卡分析",
    "崩铁角色池抽卡统计",
    "崩铁光锥池抽卡统计",
    "崩铁常驻池抽卡统计",
    "星铁抽卡统计",
    "星铁抽卡记录",
    "星铁祈愿统计",
    "星铁抽卡分析",
    "星铁角色池抽卡统计",
    "星铁光锥池抽卡统计",
    "星铁常驻池抽卡统计",
)

GACHA_PREFIXES = ("喵喵", "miao", "MM")
PREFIXED_GACHA_COMMANDS = tuple(f"{prefix}{cmd}" for prefix in GACHA_PREFIXES for cmd in GACHA_COMMANDS)

GACHA_COMMAND_PREFIXES = tuple(f"{cmd} " for cmd in GACHA_COMMANDS)
PREFIXED_GACHA_COMMAND_PREFIXES = tuple(f"{cmd} " for cmd in PREFIXED_GACHA_COMMANDS)


@sv_gacha.on_fullmatch(("导入原神抽卡记录帮助", "原神抽卡记录导入帮助", "原神抽卡帮助"), block=True)
async def send_gacha_import_help(bot: Bot, ev: Event):
    await bot.send(_import_help("gs"))


@sv_gacha.on_fullmatch(("导入崩铁抽卡记录帮助", "导入星铁抽卡记录帮助", "崩铁抽卡记录导入帮助", "星铁抽卡记录导入帮助", "崩铁抽卡帮助", "星铁抽卡帮助"), block=True)
async def send_sr_gacha_import_help(bot: Bot, ev: Event):
    await bot.send(_import_help("sr"))


@sv_gacha.on_regex(r"^(?:喵喵|miao|MM)?导入(?P<game>原神|崩铁|星铁)抽卡记录(?!帮助)\s*(?P<payload>.*)$", block=True)
async def send_gacha_import(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = getattr(ev, "raw_text", "") or ""
    data = ev.regex_dict or {}
    game = "sr" if data.get("game") in {"崩铁", "星铁"} or _game_from_text(text) == "sr" else "gs"
    payload = (data.get("payload") or _strip_import_payload(text)).strip()
    uid = await _uid_from_event(ev, payload or text, game)
    if not uid:
        name = _game_name(game)
        return await bot.send(f"请先绑定 {name} UID，或在导入命令后携带 UID。\n可发送：{_import_help_command(game)}")
    if not payload:
        return await bot.send(_empty_gacha_message(game))
    if "authkey=" in payload and payload.startswith(("http://", "https://")):
        result = await import_gacha_authkey(game, str(ev.user_id or ""), uid, payload)
        return await bot.send(_format_import_result(result))
    raw_json = _extract_json_payload(text)
    if raw_json is None:
        return await bot.send(f"未识别到可导入内容。请发送 authkey 链接或 UIGF/JSON 文本。\n可发送：{_import_help_command(game)}")
    result = import_gacha_json(game, str(ev.user_id or ""), uid, raw_json)
    await bot.send(_format_import_result(result))


@sv_gacha.on_fullmatch(GACHA_COMMANDS + PREFIXED_GACHA_COMMANDS, block=True)
async def send_gacha_stat_fullmatch(bot: Bot, ev: Event):
    await _send_gacha_stat(bot, ev)


@sv_gacha.on_regex(r"^(?:喵喵|miao|MM)?(?P<game>原神|崩铁|星铁)?(?P<pool>角色|武器|光锥|常驻|集录|up|UP)?池?(?P<cmd>抽卡记录|抽卡统计|抽奖记录|祈愿记录|祈愿统计|抽卡分析)\s*(?P<uid>\d{9,10})?$", block=True)
async def send_gacha_stat(bot: Bot, ev: Event):
    await _send_gacha_stat(bot, ev)


@sv_gacha.on_regex(r"^(?:喵喵|miao|MM)?(?P<game>原神|崩铁|星铁)?(?P<pool>角色|武器|光锥|常驻|集录|up|UP)?池?(?P<cmd>抽卡记录|抽卡统计|抽奖记录|祈愿记录|祈愿统计|抽卡分析)\s+(?P<uid>\d{9,10})$", block=True)
async def send_gacha_stat_with_uid(bot: Bot, ev: Event):
    await _send_gacha_stat(bot, ev)


@sv_gacha.on_prefix(GACHA_COMMAND_PREFIXES + PREFIXED_GACHA_COMMAND_PREFIXES, block=True)
async def send_gacha_stat_prefix_uid(bot: Bot, ev: Event):
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
    if not result.get("ok") or not int(result.get("total") or 0):
        return await bot.send(_empty_gacha_message(game))
    await bot.send(await render_gacha_image(result))