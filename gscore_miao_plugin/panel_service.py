from __future__ import annotations

from typing import List, Tuple

from .config import MiaoConfig
from .panel_models import PanelResult, PanelSourceError
from .panel_sources import get_source, get_source_order


def _avatar_count(result: PanelResult) -> int:
    avatars = result.avatars or []
    return len(avatars)


def render_panel_text(result: PanelResult) -> str:
    lines = [
        "【喵喵面板】",
        f"UID：{result.uid}",
        f"数据源：{result.source}",
    ]
    if result.nickname:
        lines.append(f"昵称：{result.nickname}")
    if result.level is not None:
        lines.append(f"等级：{result.level}")
    if result.signature:
        lines.append(f"签名：{result.signature}")
    lines.append(f"公开角色数：{_avatar_count(result)}")
    lines.append("")
    lines.append("已完成数据接入骨架；图片面板渲染会在后续迁移 miao-plugin 渲染模板时补齐。")
    return "\n".join(lines)


async def query_panel(uid: str, user_source: str) -> Tuple[PanelResult | None, List[str]]:
    errors: List[str] = []
    fallback = bool(MiaoConfig.get_config("EnablePanelFallback").data)

    for source_name in get_source_order(user_source):
        try:
            return await get_source(source_name).fetch(uid), errors
        except PanelSourceError as e:
            errors.append(f"{e.source}: {e.message}")
            if not fallback:
                break
        except Exception as e:
            errors.append(f"{source_name}: {e}")
            if not fallback:
                break

    return None, errors
