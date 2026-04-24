from __future__ import annotations

import hashlib
import json
import random
import string
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin

import httpx

from .config import MiaoConfig
from .panel_cache import get_cached_panel, set_cached_panel
from .panel_models import BasePanelSource, PanelResult, PanelSourceError


def _timeout() -> float:
    return float(MiaoConfig.get_config("PanelRequestTimeout").data)


def _strip_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _headers(token: str = "") -> Dict[str, str]:
    headers = {
        "User-Agent": "gscore_miao-plugin/0.4",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _source_headers(source: str) -> Dict[str, str]:
    if source in {"enka", "mgg"}:
        ua = "Miao-Plugin/3.1"
    elif source == "hutao":
        ua = "Snap Hutao/miao"
    else:
        ua = "gscore_miao-plugin/0.5"
    return {"User-Agent": ua, "Accept": "application/json"}


def _as_dict(data: Any) -> Dict[str, Any]:
    return data if isinstance(data, dict) else {"data": data}


def _dig(data: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        cur: Any = data
        ok = True
        for part in key.split("."):
            if not isinstance(cur, dict) or part not in cur:
                ok = False
                break
            cur = cur[part]
        if ok:
            return cur
    return None


def _avatars_from(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    avatars = _dig(data, "avatars", "avatarInfoList", "list", "data.avatars", "data.avatarInfoList", "data.list")
    return avatars if isinstance(avatars, list) else []


def _nickname_from(data: Dict[str, Any]) -> str:
    return str(_dig(data, "nickname", "name", "playerInfo.nickname", "data.nickname", "data.name", "data.playerInfo.nickname") or "")


def _level_from(data: Dict[str, Any]) -> Optional[int]:
    level = _dig(data, "level", "playerInfo.level", "data.level", "data.playerInfo.level")
    return level if isinstance(level, int) else None


def _signature_from(data: Dict[str, Any]) -> str:
    return str(_dig(data, "signature", "playerInfo.signature", "data.signature", "data.playerInfo.signature") or "")


def _server_id(uid: str) -> str:
    return "cn_qd01" if str(uid).startswith("5") else "cn_gf01"


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _mys_ds(q: str = "", b: Optional[Dict[str, Any]] = None) -> str:
    salt = str(MiaoConfig.get_config("MysDsSalt").data or "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs")
    body = json.dumps(b, separators=(",", ":")) if b else ""
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = _md5(f"salt={salt}&t={t}&r={r}&b={body}&q={q}")
    return f"{t},{r},{c}"


def _mys_headers(cookie: str, q: str = "", b: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    device_id = str(MiaoConfig.get_config("MysDeviceId").data or uuid.uuid4()).lower()
    device_fp = str(MiaoConfig.get_config("MysDeviceFp").data or "").strip()
    app_version = str(MiaoConfig.get_config("MysAppVersion").data or "2.102.1")
    client_type = str(MiaoConfig.get_config("MysClientType").data or "5")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; PHK110 Build/SKQ1.221119.001; wv)"
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.6478.133 "
            f"Mobile Safari/537.36 miHoYoBBS/{app_version}"
        ),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "DS": _mys_ds(q, b),
        "x-rpc-app_version": app_version,
        "x-rpc-client_type": client_type,
        "x-rpc-device_id": device_id,
        "X-Requested-With": "com.mihoyo.hyperion",
        "Referer": "https://webstatic.mihoyo.com/",
        "Origin": "https://webstatic.mihoyo.com/",
    }
    if device_fp:
        headers["x-rpc-device_fp"] = device_fp
    return headers


def _check_retcode(source: str, raw: Dict[str, Any]) -> None:
    retcode = raw.get("retcode", raw.get("code", 0))
    if retcode not in (0, "0", None):
        msg = raw.get("message") or raw.get("msg") or raw.get("error") or "未知错误"
        raise PanelSourceError(source, f"接口返回 {retcode}: {msg}")


class EnkaPanelSource(BasePanelSource):
    source_name = "enka"

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(self.source_name, uid)
        if cached:
            return cached

        base_url = _strip_url(MiaoConfig.get_config("EnkaApiBaseUrl").data)
        locale = MiaoConfig.get_config("EnkaLocale").data
        if not base_url:
            raise PanelSourceError(self.source_name, "Enka API 地址未配置")

        url = f"{base_url}/{uid}"
        params = {"lang": locale} if locale else None
        try:
            async with httpx.AsyncClient(timeout=_timeout(), headers=_source_headers(self.source_name)) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                raw = _as_dict(resp.json())
        except Exception as e:
            raise PanelSourceError(self.source_name, f"Enka 请求失败：{e}") from e

        player = raw.get("playerInfo") or {}
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=str(player.get("nickname") or ""),
            level=player.get("level"),
            signature=str(player.get("signature") or ""),
            avatars=raw.get("avatarInfoList") or [],
        )
        set_cached_panel(self.source_name, uid, result)
        return result


class MiaoPanelSource(BasePanelSource):
    source_name = "miao"

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(self.source_name, uid)
        if cached:
            return cached

        base_url = _strip_url(MiaoConfig.get_config("MiaoApiBaseUrl").data)
        qq = str(MiaoConfig.get_config("MiaoApiQQ").data or "").strip()
        token = str(MiaoConfig.get_config("MiaoApiToken").data or "").strip()
        game = str(MiaoConfig.get_config("MiaoApiGame").data or "gs")
        if not base_url:
            raise PanelSourceError(self.source_name, "Miao API 地址未配置")
        if not token:
            raise PanelSourceError(self.source_name, "Miao API Token 未配置")
        if len(token) != 32:
            raise PanelSourceError(self.source_name, "Miao API Token 应为32位")

        url = urljoin(f"{base_url}/", "profile/data")
        params = {
            "uid": uid,
            "qq": qq if qq.isdigit() and 5 <= len(qq) <= 12 else "none",
            "token": token,
            "version": "2",
            "game": game,
        }
        try:
            async with httpx.AsyncClient(timeout=_timeout(), headers=_source_headers(self.source_name)) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                raw = _as_dict(resp.json())
        except Exception as e:
            raise PanelSourceError(self.source_name, f"Miao 请求失败：{e}") from e

        _check_retcode(self.source_name, raw)

        data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=_nickname_from(data),
            level=_level_from(data),
            signature=_signature_from(data),
            avatars=_avatars_from(data),
        )
        set_cached_panel(self.source_name, uid, result)
        return result


class MysPanelSource(BasePanelSource):
    source_name = "mys"

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(self.source_name, uid)
        if cached:
            return cached

        base_url = _strip_url(MiaoConfig.get_config("MysApiBaseUrl").data)
        cookie = str(MiaoConfig.get_config("MysCookie").data or "").strip()
        if not base_url:
            raise PanelSourceError(self.source_name, "米游社 API 地址未配置")
        if not cookie:
            raise PanelSourceError(self.source_name, "米游社 Cookie 未配置")

        server = _server_id(uid)
        index_params = {"role_id": uid, "server": server}
        index_q = urlencode(index_params)
        index_url = urljoin(f"{base_url}/", "game_record/app/genshin/api/index")
        try:
            async with httpx.AsyncClient(timeout=_timeout()) as client:
                index_resp = await client.get(
                    index_url,
                    params=index_params,
                    headers=_mys_headers(cookie, index_q),
                )
                index_resp.raise_for_status()
                index_raw = _as_dict(index_resp.json())
                _check_retcode(self.source_name, index_raw)

                index_data = index_raw.get("data") if isinstance(index_raw.get("data"), dict) else {}
                avatars = index_data.get("avatars") if isinstance(index_data, dict) else []
                character_ids = [x.get("id") for x in avatars if isinstance(x, dict) and x.get("id")]
                detail_raw: Dict[str, Any] = {}
                if character_ids:
                    detail_body = {"character_ids": character_ids, "role_id": uid, "server": server}
                    detail_url = urljoin(f"{base_url}/", "game_record/app/genshin/api/character/list")
                    detail_resp = await client.post(
                        detail_url,
                        json=detail_body,
                        headers=_mys_headers(cookie, "", detail_body),
                    )
                    detail_resp.raise_for_status()
                    detail_raw = _as_dict(detail_resp.json())
                    _check_retcode(self.source_name, detail_raw)

                raw = {"index": index_raw, "detail": detail_raw}
        except Exception as e:
            raise PanelSourceError(self.source_name, f"米游社请求失败：{e}") from e

        detail_data = detail_raw.get("data") if isinstance(detail_raw.get("data"), dict) else {}
        data = deepcopy(index_data)
        if isinstance(detail_data, dict) and isinstance(detail_data.get("list"), list):
            data["avatars"] = detail_data["list"]
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=str((data.get("role") or {}).get("nickname") or ""),
            level=(data.get("role") or {}).get("level"),
            signature="",
            avatars=data.get("avatars") or [],
        )
        set_cached_panel(self.source_name, uid, result)
        return result


class SimpleHttpPanelSource(BasePanelSource):
    def __init__(self, source_name: str, config_key: str, path_template: str):
        self.source_name = source_name
        self.config_key = config_key
        self.path_template = path_template

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(self.source_name, uid)
        if cached:
            return cached

        base_url = _strip_url(MiaoConfig.get_config(self.config_key).data)
        if not base_url:
            raise PanelSourceError(self.source_name, f"{self.source_name} API 地址未配置")

        url = urljoin(f"{base_url}/", self.path_template.format(uid=uid))
        try:
            async with httpx.AsyncClient(timeout=_timeout(), headers=_source_headers(self.source_name)) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                raw = _as_dict(resp.json())
        except Exception as e:
            raise PanelSourceError(self.source_name, f"{self.source_name} 请求失败：{e}") from e

        data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=_nickname_from(data),
            level=_level_from(data),
            signature=_signature_from(data),
            avatars=_avatars_from(data),
        )
        set_cached_panel(self.source_name, uid, result)
        return result


def get_source(name: str) -> BasePanelSource:
    source_map = {
        "enka": EnkaPanelSource,
        "miao": MiaoPanelSource,
        "mys": MysPanelSource,
    }
    if name in source_map:
        return source_map[name]()
    if name == "mgg":
        return SimpleHttpPanelSource("mgg", "MggApiBaseUrl", "api/uid/{uid}")
    if name == "hutao":
        return SimpleHttpPanelSource("hutao", "HutaoApiBaseUrl", "{uid}")
    raise PanelSourceError(name, "未知面板数据源")


def get_source_order(user_source: str) -> List[str]:
    allowed = set(MiaoConfig.get_config("AllowedPanelServers").data)
    if user_source and user_source != "auto":
        return [user_source] if user_source in allowed else []

    order = [x for x in MiaoConfig.get_config("PanelSourcePriority").data if x in allowed]
    return order or [x for x in ["miao", "enka", "mys"] if x in allowed]
