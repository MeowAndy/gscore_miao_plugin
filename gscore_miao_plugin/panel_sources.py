from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urljoin

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


def _as_dict(data: Any) -> Dict[str, Any]:
    return data if isinstance(data, dict) else {"data": data}


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
            async with httpx.AsyncClient(timeout=_timeout(), headers=_headers()) as client:
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
        token = MiaoConfig.get_config("MiaoApiToken").data
        if not base_url:
            raise PanelSourceError(self.source_name, "Miao API 地址未配置")

        url = urljoin(f"{base_url}/", f"panel/{uid}")
        try:
            async with httpx.AsyncClient(timeout=_timeout(), headers=_headers(token)) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                raw = _as_dict(resp.json())
        except Exception as e:
            raise PanelSourceError(self.source_name, f"Miao 请求失败：{e}") from e

        data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=str(data.get("nickname") or data.get("name") or ""),
            level=data.get("level"),
            signature=str(data.get("signature") or ""),
            avatars=data.get("avatars") or data.get("avatarInfoList") or [],
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
        cookie = MiaoConfig.get_config("MysCookie").data
        device_id = MiaoConfig.get_config("MysDeviceId").data
        if not base_url:
            raise PanelSourceError(self.source_name, "米游社 API 地址未配置")
        if not cookie:
            raise PanelSourceError(self.source_name, "米游社 Cookie 未配置")

        headers = _headers()
        headers["Cookie"] = cookie
        if device_id:
            headers["x-rpc-device_id"] = device_id

        url = urljoin(f"{base_url}/", f"panel/{uid}")
        try:
            async with httpx.AsyncClient(timeout=_timeout(), headers=headers) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                raw = _as_dict(resp.json())
        except Exception as e:
            raise PanelSourceError(self.source_name, f"米游社请求失败：{e}") from e

        data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=str(data.get("nickname") or data.get("name") or ""),
            level=data.get("level"),
            signature=str(data.get("signature") or ""),
            avatars=data.get("avatars") or data.get("avatarInfoList") or [],
        )
        set_cached_panel(self.source_name, uid, result)
        return result


class SimpleHttpPanelSource(BasePanelSource):
    def __init__(self, source_name: str, config_key: str):
        self.source_name = source_name
        self.config_key = config_key

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(self.source_name, uid)
        if cached:
            return cached

        base_url = _strip_url(MiaoConfig.get_config(self.config_key).data)
        if not base_url:
            raise PanelSourceError(self.source_name, f"{self.source_name} API 地址未配置")

        url = urljoin(f"{base_url}/", f"panel/{uid}")
        try:
            async with httpx.AsyncClient(timeout=_timeout(), headers=_headers()) as client:
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
            nickname=str(data.get("nickname") or data.get("name") or ""),
            level=data.get("level"),
            signature=str(data.get("signature") or ""),
            avatars=data.get("avatars") or data.get("avatarInfoList") or [],
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
        return SimpleHttpPanelSource("mgg", "MggApiBaseUrl")
    if name == "hutao":
        return SimpleHttpPanelSource("hutao", "HutaoApiBaseUrl")
    raise PanelSourceError(name, "未知面板数据源")


def get_source_order(user_source: str) -> List[str]:
    allowed = set(MiaoConfig.get_config("AllowedPanelServers").data)
    if user_source and user_source != "auto":
        return [user_source] if user_source in allowed else []

    order = [x for x in MiaoConfig.get_config("PanelSourcePriority").data if x in allowed]
    return order or [x for x in ["miao", "enka", "mys"] if x in allowed]
