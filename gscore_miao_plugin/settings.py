from __future__ import annotations

from typing import Dict

from .config import MiaoConfig


def build_default_user_cfg() -> Dict[str, object]:
    return {
        "panel_server": MiaoConfig.get_config("DefaultPanelServer").data,
        "uid": "",
        "custom_splash": True,
        "team_calc": False,
        "show_star": False,
        "comma_group": 3,
    }


def merge_user_cfg(user_cfg: Dict[str, object]) -> Dict[str, object]:
    default_cfg = build_default_user_cfg()
    return {
        **default_cfg,
        **(user_cfg or {}),
    }
