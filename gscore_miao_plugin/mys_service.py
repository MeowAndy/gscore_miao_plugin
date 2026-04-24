from __future__ import annotations

import hashlib
import json
import random
import re
import time
import uuid
from http.cookies import SimpleCookie
from typing import Any, Dict, List
from urllib.parse import urlencode

import httpx
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.utils.api.mys.tools import get_web_ds_token
from gsuid_core.utils.api.mys_api import mys_api
from gsuid_core.utils.cookie_manager.qrlogin import get_qrcode_base64, refresh

from .config import MiaoConfig
from .const import PACKAGE_DIR

GENSHIN_SIGN_ACT_ID = "e202311201442471"
STARRAIL_SIGN_ACT_ID = "e202304121516551"


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


def _sign_headers(cookie: str, q: str = "", b: Dict[str, Any] | None = None, signgame: str = "hk4e") -> Dict[str, str]:
    headers = _headers(cookie, q, b)
    headers.update(
        {
            "DS": get_web_ds_token(True),
            "Referer": "https://webstatic.mihoyo.com/",
            "Origin": "https://webstatic.mihoyo.com",
            "x-rpc-signgame": signgame,
        }
    )
    return headers


def _server_id(uid: str) -> str:
    return "cn_qd01" if str(uid).startswith("5") else "cn_gf01"


def _starrail_server_id(uid: str) -> str:
    return "prod_qd_cn" if str(uid).startswith("5") else "prod_gf_cn"


def _message(raw: Dict[str, Any]) -> str:
    message = str(raw.get("message") or raw.get("msg") or raw.get("error") or "未知错误")
    retcode = raw.get("retcode")
    return f"{message}（retcode: {retcode}）" if retcode not in (None, "") else message


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


async def fetch_starrail_roles(cookie: str) -> List[Dict[str, Any]]:
    url = "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie"
    params = {"game_biz": "hkrpg_cn"}
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
    params = {"act_id": GENSHIN_SIGN_ACT_ID, "lang": "zh-cn", "region": _server_id(uid), "uid": uid}
    q = urlencode(params)
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.get(url, params=params, headers=_sign_headers(cookie, q))
        resp.raise_for_status()
        raw = resp.json()
    if raw.get("retcode") not in (0, "0"):
        raise RuntimeError(_message(raw))
    return raw.get("data") or {}


async def fetch_starrail_sign_info(cookie: str, uid: str) -> Dict[str, Any]:
    url = "https://api-takumi.mihoyo.com/event/luna/info"
    params = {"act_id": STARRAIL_SIGN_ACT_ID, "lang": "zh-cn", "region": _starrail_server_id(uid), "uid": uid}
    q = urlencode(params)
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.get(url, params=params, headers=_sign_headers(cookie, q, signgame="hkrpg"))
        resp.raise_for_status()
        raw = resp.json()
    if raw.get("retcode") not in (0, "0"):
        raise RuntimeError(_message(raw))
    return raw.get("data") or {}


async def daily_sign(cookie: str, uid: str) -> Dict[str, Any]:
    url = "https://api-takumi.mihoyo.com/event/luna/sign"
    body = {"act_id": GENSHIN_SIGN_ACT_ID, "lang": "zh-cn", "region": _server_id(uid), "uid": uid}
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.post(url, json=body, headers=_sign_headers(cookie, "", body))
        resp.raise_for_status()
        raw = resp.json()
    retcode = raw.get("retcode")
    if retcode not in (0, "0", -5003):
        raise RuntimeError(_message(raw))
    return raw


async def daily_sign_starrail(cookie: str, uid: str) -> Dict[str, Any]:
    url = "https://api-takumi.mihoyo.com/event/luna/sign"
    body = {"act_id": STARRAIL_SIGN_ACT_ID, "lang": "zh-cn", "region": _starrail_server_id(uid), "uid": uid}
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.post(url, json=body, headers=_sign_headers(cookie, "", body, signgame="hkrpg"))
        resp.raise_for_status()
        raw = resp.json()
    retcode = raw.get("retcode")
    if retcode not in (0, "0", -5003):
        raise RuntimeError(_message(raw))
    return raw


async def validate_cookie(cookie: str) -> List[Dict[str, Any]]:
    roles = await fetch_genshin_roles(cookie)
    sr_roles = await fetch_starrail_roles(cookie)
    if not roles and not sr_roles:
        raise RuntimeError("当前 Cookie 未绑定原神或崩铁角色")
    return roles


async def qrcode_login_cookie(bot: Bot, ev: Event) -> str:
    code_data = await mys_api.create_qrcode_url()
    if isinstance(code_data, int):
        raise RuntimeError("二维码链接创建失败")

    path = PACKAGE_DIR / f"miao_qrcode_{ev.user_id}.gif"
    msg = [
        MessageSegment.text("请使用米游社 App 扫描下方二维码登录："),
        MessageSegment.image(await get_qrcode_base64(code_data["url"], path, ev.bot_id)),
        MessageSegment.text(
            "扫码确认后将获取米游社 Cookie，用于面板、签到等查询。\n"
            "请勿在不可信机器人或群聊中登录。二维码约 2 分钟内有效。"
        ),
    ]
    try:
        await bot.send(MessageSegment.node(msg))
    except Exception:
        await bot.send(await get_qrcode_base64(code_data["url"], path, ev.bot_id))
        await bot.send("请使用米游社 App 扫码确认登录，二维码约 2 分钟内有效。")
    finally:
        if path.exists():
            path.unlink()

    status, game_token_data = await refresh(code_data)
    if not status or not game_token_data:
        raise RuntimeError("二维码已过期或未确认")

    stoken_data = await mys_api.get_stoken_by_game_token(
        account_id=int(game_token_data["uid"]),
        game_token=game_token_data["token"],
    )
    if isinstance(stoken_data, int):
        raise RuntimeError("获取 stoken 失败")

    account_id = str(game_token_data["uid"])
    stoken = stoken_data["token"]["token"]
    mid = stoken_data["user_info"]["mid"]
    app_cookie = f"stuid={account_id};stoken={stoken};mid={mid}"
    ck = await mys_api.get_cookie_token_by_stoken(stoken, account_id, app_cookie)
    if isinstance(ck, int):
        raise RuntimeError("获取 cookie_token 失败")

    return normalize_cookie(
        SimpleCookie(
            {
                "stoken_v2": stoken_data["token"]["token"],
                "stuid": stoken_data["user_info"].get("aid") or account_id,
                "mid": mid,
                "cookie_token": ck["cookie_token"],
                "account_id": account_id,
                "ltuid": account_id,
            }
        ).output(header="", sep=";")
    )