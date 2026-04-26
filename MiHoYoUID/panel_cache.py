from __future__ import annotations

import time
from typing import Dict, Tuple

from .config import MiaoConfig
from .panel_models import PanelResult

_CACHE: Dict[Tuple[str, str], Tuple[float, PanelResult]] = {}


def get_cached_panel(source: str, uid: str) -> PanelResult | None:
    ttl = int(MiaoConfig.get_config("PanelCacheTTL").data)
    if ttl <= 0:
        return None
    item = _CACHE.get((source, uid))
    if not item:
        return None
    ts, result = item
    if time.time() - ts > ttl:
        _CACHE.pop((source, uid), None)
        return None
    return result


def set_cached_panel(source: str, uid: str, result: PanelResult) -> None:
    ttl = int(MiaoConfig.get_config("PanelCacheTTL").data)
    if ttl <= 0:
        return
    _CACHE[(source, uid)] = (time.time(), result)


def _latest_key(game: str) -> str:
    return f"latest:{'sr' if game in {'sr', 'starrail', 'hkrpg'} else 'gs'}"


def get_latest_panel(uid: str, game: str = "gs") -> PanelResult | None:
    return get_cached_panel(_latest_key(game), uid)


def set_latest_panel(uid: str, result: PanelResult, game: str = "gs") -> None:
    set_cached_panel(_latest_key(game), uid, result)


def clear_cached_panel(uid: str, source: str | None = None) -> int:
    keys = [key for key in _CACHE if key[1] == uid and (source is None or key[0] == source)]
    for key in keys:
        _CACHE.pop(key, None)
    return len(keys)
