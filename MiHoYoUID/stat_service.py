from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

from .config import MiaoConfig
from .path import MAIN_PATH

STAT_CACHE_DIR = MAIN_PATH / "cache" / "stat"
STAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "cons": "https://api.lelaer.com/ys/getRoleAvg.php?star=all&lang=zh-Hans",
    "abyss": "https://api.yshelper.com/ys/getAbyssRank.php?star=all&role=all&lang=zh-Hans",
    "hard": "https://api.lelaer.com/ys/getAbyssRank2.php?star=all&role=all&lang=zh-Hans",
    "team": "http://miao.games/api/hutao?api=team",
}


def _timeout() -> float:
    return float(MiaoConfig.get_config("PanelRequestTimeout").data or 15)


def _cache_path(kind: str) -> Path:
    return STAT_CACHE_DIR / f"{kind}.json"


def _read_cache(kind: str, ttl: int = 3600) -> Dict[str, Any] | None:
    path = _cache_path(kind)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(data.get("ts") or 0) <= ttl:
            return data.get("payload") if isinstance(data.get("payload"), dict) else data
    except Exception:
        return None
    return None


def _write_cache(kind: str, payload: Dict[str, Any]) -> None:
    try:
        _cache_path(kind).write_text(json.dumps({"ts": time.time(), "payload": payload}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        return


def _unwrap(raw: Any) -> Any:
    if isinstance(raw, dict):
        for key in ("data", "list", "result"):
            value = raw.get(key)
            if isinstance(value, (dict, list)):
                return value
    return raw


async def fetch_stat(kind: str, force: bool = False) -> Dict[str, Any]:
    kind = kind if kind in URLS else "abyss"
    cached = None if force else _read_cache(kind)
    if cached:
        cached["cached"] = True
        return cached
    async with httpx.AsyncClient(timeout=_timeout(), follow_redirects=True) as client:
        resp = await client.get(URLS[kind], headers={"User-Agent": "GsCoreMiao/0.15"})
        resp.raise_for_status()
        raw = resp.json()
    payload = {"kind": kind, "url": URLS[kind], "raw": _unwrap(raw), "cached": False, "updated": int(time.time())}
    _write_cache(kind, payload)
    return payload


def _as_rows(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        for key in ("list", "data", "rank", "result", "avatars", "roles"):
            rows = value.get(key)
            if isinstance(rows, list):
                return [x for x in rows if isinstance(x, dict)]
        rows = []
        for key, item in value.items():
            if isinstance(item, dict):
                row = dict(item)
                row.setdefault("name", key)
                rows.append(row)
        return rows
    return []


def normalize_stat_rows(payload: Dict[str, Any], limit: int = 24) -> Dict[str, Any]:
    kind = payload.get("kind") or "abyss"
    raw = payload.get("raw")
    rows = _as_rows(raw)
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        name = row.get("name") or row.get("avatar") or row.get("role") or row.get("title") or row.get("cn") or row.get("key") or f"第{idx}项"
        rate = row.get("rate") or row.get("value") or row.get("avg") or row.get("percent") or row.get("use") or row.get("usage") or row.get("持有率") or row.get("出场率")
        count = row.get("count") or row.get("total") or row.get("num") or row.get("sample") or ""
        cons = row.get("cons") or row.get("命座") or row.get("life") or ""
        try:
            score = float(str(rate).strip("%"))
        except (TypeError, ValueError):
            score = 0.0
        out.append({"rank": idx, "name": str(name), "rate": rate, "count": count, "cons": cons, "score": score, "raw": row})
    out.sort(key=lambda x: x["score"], reverse=True)
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return {**payload, "rows": out[:limit], "total_rows": len(out)}


def build_stat_placeholder(kind: str, message: str) -> Dict[str, Any]:
    return {"kind": kind, "rows": [], "total_rows": 0, "message": message, "cached": False}