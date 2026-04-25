from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..config import MiaoConfig
from ..version import CHANGELOGS

sv_changelog = SV("GsCoreMiao更新日志")


@sv_changelog.on_fullmatch(("更新日志", "changelog"), block=True)
async def send_changelog(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")

    limit = MiaoConfig.get_config("UpdateLogLimit").data
    logs = CHANGELOGS[:limit]

    msg_list = []
    for item in logs:
        content = f"{item['version']} ({item['date']})"
        for x in item.get("items", []):
            content += f"\n• {x}"
        msg_list.append(content)

    await bot.send(MessageSegment.node(msg_list))
