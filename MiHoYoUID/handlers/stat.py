from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..panel_renderer import render_stat_image
from ..stat_service import (build_stat_placeholder, fetch_stat,
                            normalize_stat_rows)

sv_stat = SV("GsCoreMiao统计")


def _kind_title(text: str) -> tuple[str, str]:
    if "组队" in text or "配队" in text:
        return "team", "喵喵深渊组队"
    if "幽境" in text or "危战" in text:
        return "hard", "喵喵幽境危战统计"
    if "持有" in text or "命座" in text or "5命" in text or "满命" in text:
        return "cons", "喵喵角色持有/命座统计"
    if "幻想" in text or "剧诗" in text:
        return "abyss", "喵喵幻想真境剧诗数据"
    return "abyss", "喵喵深渊出场率"


@sv_stat.on_regex(r"^(?P<cmd>角色持有率|角色命座统计|角色5命统计|深渊出场率|深渊使用率|深渊组队|深渊配队|深渊数据|幻想真境剧诗数据|幻想真境数据|幽境危战出场率|幽境危战使用率|幽境危战数据)$", block=True)
async def send_public_stat(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = (ev.regex_dict or {}).get("cmd") or getattr(ev, "raw_text", "") or ""
    kind, title = _kind_title(text)
    try:
        payload = await fetch_stat(kind)
        data = normalize_stat_rows(payload)
    except Exception as e:
        data = build_stat_placeholder(kind, f"统计接口获取失败：{e}")
    await bot.send(await render_stat_image(data, title))