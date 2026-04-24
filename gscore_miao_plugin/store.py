import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict

from .path import MAIN_PATH

_USER_CFG_PATH = MAIN_PATH / "user_config.json"
_LOCK = asyncio.Lock()


def _load_json() -> Dict[str, Any]:
    if not _USER_CFG_PATH.exists():
        return {}
    try:
        return json.loads(_USER_CFG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(data: Dict[str, Any]) -> None:
    _USER_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _USER_CFG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _user_key(user_id: str, bot_id: str) -> str:
    return f"{bot_id}:{user_id}"


async def get_user_cfg(user_id: str, bot_id: str) -> Dict[str, Any]:
    async with _LOCK:
        data = _load_json()
        return data.get(_user_key(user_id, bot_id), {})


async def set_user_cfg(user_id: str, bot_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    async with _LOCK:
        data = _load_json()
        k = _user_key(user_id, bot_id)
        old = data.get(k, {})
        merged = {**old, **patch, "updated_at": int(time.time())}
        data[k] = merged
        _save_json(data)
        return merged


async def get_all_user_cfg() -> Dict[str, Any]:
    async with _LOCK:
        return _load_json()


async def reset_user_cfg(user_id: str, bot_id: str) -> None:
    async with _LOCK:
        data = _load_json()
        k = _user_key(user_id, bot_id)
        if k in data:
            del data[k]
            _save_json(data)


async def bind_uid(user_id: str, bot_id: str, uid: str) -> Dict[str, Any]:
    return await set_user_cfg(user_id, bot_id, {"uid": uid})


async def bind_mys_cookie(user_id: str, bot_id: str, cookie: str, roles: list[dict[str, Any]]) -> Dict[str, Any]:
    default_uid = str((roles[0] or {}).get("game_uid") or (roles[0] or {}).get("uid") or "") if roles else ""
    patch: Dict[str, Any] = {
        "mys_cookie": cookie,
        "mys_roles": roles,
        "login_type": "mys_cookie",
        "login_at": int(time.time()),
    }
    if default_uid:
        patch["uid"] = default_uid
    return await set_user_cfg(user_id, bot_id, patch)


async def unbind_mys_cookie(user_id: str, bot_id: str) -> Dict[str, Any]:
    async with _LOCK:
        data = _load_json()
        k = _user_key(user_id, bot_id)
        old = data.get(k, {})
        merged = {**old, "updated_at": int(time.time())}
        for key in ("mys_cookie", "mys_roles", "login_type", "login_at"):
            merged.pop(key, None)
        data[k] = merged
        _save_json(data)
        return merged


async def unbind_uid(user_id: str, bot_id: str) -> Dict[str, Any]:
    async with _LOCK:
        data = _load_json()
        k = _user_key(user_id, bot_id)
        old = data.get(k, {})
        merged = {**old, "updated_at": int(time.time())}
        merged.pop("uid", None)
        data[k] = merged
        _save_json(data)
        return merged
