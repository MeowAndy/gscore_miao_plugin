from __future__ import annotations

import hashlib
import json
import random
import re
import time
import uuid
from typing import Any, Dict, List
from urllib.parse import urlencode

import httpx

from .config import MiaoConfig

SIGN_ACT_ID = "e202311201442471"


def _timeout() -> float:
    return float(MiaoConfig.get_config("PanelRequestTimeout").data or 15)


def normalize_cookie(text: str) -> str:
    raw = (text or "").strip().replace("\n", ";")
    pairs: Dict[str, str] = {}
    for item in raw.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            pairs[key] = value
    return "; ".join(f"{k}={v}" for k, v in pairs.items())


def cookie_uid(cookie: str) -> str:
    for key in ("ltuid_v2", "ltuid", "account_id_v2", "account_id"):
        match = re.search(rf"(?:^|;\s*){key}=([^;]+)", cookie)
        if match:
            return match.group(1)
    return ""


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _ds(q: str = "", b: Dict[str, Any] | None = None) -> str:
    salt = str(MiaoConfig.get_config("MysDsSalt").data or "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs")
    body = json.dumps(b, separators=(",", ":"), ensure_ascii=False) if b else ""
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = _md5(f"salt={salt}&t={t}&r={r}&b={body}&q={q}")
    return f"{t},{r},{c}"


def _headers(cookie: str, q: str = "", b: Dict[str, Any] | None = None) -> Dict[str, str]:
    app_version = str(MiaoConfig.get_config("MysAppVersion").data or "2.102.1")
    client_type = str(MiaoConfig.get_config("MysClientType").data or "5")
    device_id = str(MiaoConfig.get_config("MysDeviceId").data or uuid.uuid4()).lower()
    device_fp = str(MiaoConfig.get_config("MysDeviceFp").data or "").strip()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; PHK110 Build/SKQ1.221119.001; wv) "
            f"miHoYoBBS/{app_version}"
        ),
        "Accept": "application/json",
        "Content-Type": "application/json;charset=utf-8",
        "Cookie": cookie,
        "DS": _ds(q, b),
        "x-rpc-app_version": app_version,
        "x-rpc-client_type": client_type,
        "x-rpc-device_id": device_id,
        "X-Requested-With": "com.mihoyo.hyperion",
        "Referer": "https://webstatic.mihoyo.com/",
        "Origin": "https://webstatic.mihoyo.com",
    }
    if device_fp:
        headers["x-rpc-device_fp"] = device_fp
    return headers


def _server_id(uid: str) -> str:
    return "cn_qd01" if str(uid).startswith("5") else "cn_gf01"


def _message(raw: Dict[str, Any]) -> str:
    return str(raw.get("message") or raw.get("msg") or raw.get("error") or "未知错误")


async def fetch_genshin_roles(cookie: str) -> List[Dict[str, Any]]:
    url = "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie"
    params = {"game_biz": "hk4e_cn"}
    q = urlencode(params)
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.get(url, params=params, headers=_headers(cookie, q))
        resp.raise_for_status()
        raw = resp.json()
    if raw.get("retcode") not in (0, "0"):
        raise RuntimeError(_message(raw))
    data = raw.get("data") or {}
    roles = data.get("list") or []
    return roles if isinstance(roles, list) else []


async def fetch_sign_info(cookie: str, uid: str) -> Dict[str, Any]:
    url = "https://api-takumi.mihoyo.com/event/luna/info"
    params = {"act_id": SIGN_ACT_ID, "region": _server_id(uid), "uid": uid}
    q = urlencode(params)
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.get(url, params=params, headers=_headers(cookie, q))
        resp.raise_for_status()
        raw = resp.json()
    if raw.get("retcode") not in (0, "0"):
        raise RuntimeError(_message(raw))
    return raw.get("data") or {}


async def daily_sign(cookie: str, uid: str) -> Dict[str, Any]:
    url = "https://api-takumi.mihoyo.com/event/luna/sign"
    body = {"act_id": SIGN_ACT_ID, "region": _server_id(uid), "uid": uid}
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.post(url, json=body, headers=_headers(cookie, "", body))
        resp.raise_for_status()
        raw = resp.json()
    retcode = raw.get("retcode")
    if retcode not in (0, "0", -5003):
        raise RuntimeError(_message(raw))
    return raw


async def validate_cookie(cookie: str) -> List[Dict[str, Any]]:
    roles = await fetch_genshin_roles(cookie)
    if not roles:
        raise RuntimeError("当前 Cookie 未绑定原神角色")
    return roles