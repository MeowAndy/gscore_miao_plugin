from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

from .alias_data import resolve_alias
from .path import MAIN_PATH

CHARACTER_DATA = MAIN_PATH / "character"
CUSTOM_IMG_DIR = CHARACTER_DATA / "images"
PROFILE_IMG_DIR = CHARACTER_DATA / "profile_images"
WIFE_FILE = CHARACTER_DATA / "wife.json"
LAST_FILE = CHARACTER_DATA / "last_image.json"

for path in (CUSTOM_IMG_DIR, PROFILE_IMG_DIR):
    path.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_name(name: str) -> str:
    return "".join(ch for ch in str(name or "") if ch not in '\\/:*?"<>|').strip() or "未知"


def resolve_character_name(query: str, game: str = "gs") -> str:
    return resolve_alias(query, game=game) or str(query or "").strip()


def _resource_dirs() -> List[Path]:
    root = Path(__file__).resolve().parents[1]
    return [
        root,
        root / "MiHoYoUID",
        root.parent / "miao-plugin" / "resources",
        Path("E:/gsuid_core/gsuid_core/plugins/miao-plugin/resources"),
    ]


def _resource_image_candidates(name: str, game: str = "gs") -> List[Path]:
    base = "meta-sr" if game == "sr" else "meta-gs"
    files = ("splash.webp", "splash0.webp", "splash1.webp", "gacha.webp", "party.webp", "stand.webp", "profile.webp", "card.webp", "splash.png", "card.png")
    rels = []
    for file in files:
        rels.extend([
            Path(base) / "character" / name / "imgs" / file,
            Path("character-img") / name / file,
            Path("profile") / "normal-character" / name / file,
        ])
    found: List[Path] = []
    for root in _resource_dirs():
        for rel in rels:
            path = root / rel
            if path.exists():
                found.append(path)
    return list(dict.fromkeys(found))


def list_custom_images(name: str, kind: str = "images") -> List[Path]:
    root = (PROFILE_IMG_DIR if kind == "profile" else CUSTOM_IMG_DIR) / _safe_name(name)
    if not root.exists():
        return []
    return sorted([p for p in root.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}], key=lambda p: p.stat().st_mtime, reverse=True)


def character_images(name: str, game: str = "gs") -> List[Path]:
    name = resolve_character_name(name, game)
    images = list_custom_images(name, "images") + _resource_image_candidates(name, game)
    return list(dict.fromkeys(images))


def set_last_image(user_id: str, path: Path, name: str, game: str = "gs") -> None:
    data = _read_json(LAST_FILE, {})
    data[str(user_id)] = {"path": str(path), "name": name, "game": game, "ts": int(time.time())}
    _write_json(LAST_FILE, data)


def get_last_image(user_id: str) -> Dict[str, Any] | None:
    data = _read_json(LAST_FILE, {})
    item = data.get(str(user_id))
    if not isinstance(item, dict):
        return None
    path = Path(str(item.get("path") or ""))
    if not path.exists():
        return None
    return item


def pick_character_image(name: str, game: str, user_id: str = "") -> Dict[str, Any]:
    real_name = resolve_character_name(name, game)
    images = character_images(real_name, game)
    if not images:
        return {"ok": False, "name": real_name, "game": game, "message": "未找到角色图片资源"}
    path = random.choice(images)
    if user_id:
        set_last_image(user_id, path, real_name, game)
    return {"ok": True, "name": real_name, "game": game, "path": str(path), "count": len(images)}


def wife_key(user_id: str, game: str, relation: str) -> str:
    return f"{user_id}:{game}:{relation}"


def set_wife(user_id: str, game: str, relation: str, name: str) -> Dict[str, Any]:
    real_name = resolve_character_name(name, game)
    data = _read_json(WIFE_FILE, {})
    data[wife_key(user_id, game, relation)] = {"name": real_name, "ts": int(time.time())}
    _write_json(WIFE_FILE, data)
    return {"relation": relation, "name": real_name, "game": game}


def get_wife(user_id: str, game: str, relation: str) -> Dict[str, Any] | None:
    data = _read_json(WIFE_FILE, {})
    item = data.get(wife_key(user_id, game, relation))
    return item if isinstance(item, dict) else None


def list_wives(user_id: str, game: str = "gs") -> List[Dict[str, Any]]:
    data = _read_json(WIFE_FILE, {})
    prefix = f"{user_id}:{game}:"
    rows = []
    for key, item in data.items():
        if key.startswith(prefix) and isinstance(item, dict):
            rows.append({"relation": key.removeprefix(prefix), "name": item.get("name"), "ts": item.get("ts")})
    return rows


async def save_remote_image(url: str, name: str, kind: str = "images") -> Dict[str, Any]:
    target_dir = (PROFILE_IMG_DIR if kind == "profile" else CUSTOM_IMG_DIR) / _safe_name(name)
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    path = target_dir / f"{int(time.time() * 1000)}{suffix}"
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        path.write_bytes(resp.content)
    return {"ok": True, "name": name, "kind": kind, "path": str(path)}


def delete_custom_image(name: str, index: int, kind: str = "images") -> Dict[str, Any]:
    images = list_custom_images(name, "profile" if kind == "profile" else "images")
    if index < 1 or index > len(images):
        return {"ok": False, "message": f"序号不存在，当前共有 {len(images)} 张"}
    path = images[index - 1]
    path.unlink(missing_ok=True)
    return {"ok": True, "path": str(path), "left": len(images) - 1}