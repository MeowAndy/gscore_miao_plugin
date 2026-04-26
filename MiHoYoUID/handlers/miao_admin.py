from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import is_admin_event
from ..config import MiaoConfig
from ..panel_renderer import render_status_card
from ..version import PLUGIN_VERSION

sv_miao_admin = SV("GsCoreMiao管理")


@sv_miao_admin.on_regex(r"^(喵喵)?(?P<force>强制)?更新(?P<img>图像|图片|资源)?$", block=True)
async def send_update_hint(bot: Bot, ev: Event):
    if not is_admin_event(ev):
        return await bot.send("该指令仅管理员可用。")
    data = ev.regex_dict or {}
    target = "图像资源" if data.get("img") else "插件代码"
    mode = "强制更新" if data.get("force") else "更新"
    lines = [
        f"目标：{target}",
        f"模式：{mode}",
        "GsCore 运行时内直接 git pull 可能阻塞或破坏当前进程。",
        "请在插件目录手动执行 git pull 后重启 GsCore；资源目录可通过 MiaoPluginResourcePath 指向 miao-plugin/resources。",
    ]
    await bot.send(await render_status_card("喵喵更新管理", lines, f"当前版本 {PLUGIN_VERSION}"))


@sv_miao_admin.on_regex(r"^(喵喵)?(api|API|接口|状态)$", block=True)
async def send_api_status(bot: Bot, ev: Event):
    if not is_admin_event(ev):
        return await bot.send("该指令仅管理员可用。")
    keys = ["MiaoApiBaseUrl", "EnkaApiBaseUrl", "MysApiBaseUrl", "MggApiBaseUrl", "HutaoApiBaseUrl", "MihomoApiBaseUrl", "AvocadoApiBaseUrl", "EnkaHSRApiBaseUrl"]
    lines = [f"版本：{PLUGIN_VERSION}"]
    for key in keys:
        value = MiaoConfig.get_config(key).data
        lines.append(f"{key}: {value}")
    await bot.send(await render_status_card("喵喵 API 状态", lines, "数据源配置"))