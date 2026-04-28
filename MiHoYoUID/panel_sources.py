from __future__ import annotations

import asyncio
import hashlib
import json
import random
import string
import time
import uuid
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from gsuid_core.utils.api.mys_api import mys_api

from .config import MiaoConfig
from .panel_cache import get_cached_panel, set_cached_panel
from .panel_models import BasePanelSource, PanelResult, PanelSourceError


def _timeout() -> float:
    return float(MiaoConfig.get_config("PanelRequestTimeout").data)


def _mys_timeout() -> httpx.Timeout:
    # miao-plugin gives mysPanel 20s before timeout, and GsCore's own mys
    # request wrapper allows much longer network waits.  Use a dedicated,
    # more tolerant timeout for MiHoYo endpoints so slow character/detail
    # responses do not fail immediately with ReadTimeout.
    total = max(_timeout(), 30.0)
    return httpx.Timeout(total, connect=10.0, read=total, write=10.0, pool=10.0)


def _strip_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _headers(token: str = "") -> Dict[str, str]:
    headers = {
        "User-Agent": "MiHoYoUID/0.4",
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
        ua = "MiHoYoUID/0.5"
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
    def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ret: Dict[str, Dict[str, Any]] = {}
        for item in items:
            key = str(item.get("avatarId") or item.get("AvatarID") or item.get("id") or len(ret))
            ret[key] = item
        return list(ret.values())

    avatars = _dig(data, "avatars", "characters", "avatarInfoList", "avatar_list", "list", "data.avatars", "data.characters", "data.avatarInfoList", "data.avatar_list", "data.list")
    if isinstance(avatars, list):
        return _dedupe([x for x in avatars if isinstance(x, dict)])
    if isinstance(avatars, dict):
        return _dedupe([x for x in avatars.values() if isinstance(x, dict)])
    detail = _dig(data, "detailInfo", "data.detailInfo")
    if isinstance(detail, dict):
        merged: List[Dict[str, Any]] = []
        for key in ("assistAvatarList", "assistAvatarDetail", "avatarDetailList", "avatars"):
            value = detail.get(key) or []
            if isinstance(value, dict):
                if any(k in value for k in ("avatarId", "AvatarID", "id")):
                    merged.append(value)
                    continue
                value = value.values()
            if isinstance(value, list):
                merged.extend(x for x in value if isinstance(x, dict))
            else:
                merged.extend(x for x in value if isinstance(x, dict))
        if merged:
            return _dedupe(merged)
    player = _dig(data, "playerDetailInfo", "data.playerDetailInfo")
    if isinstance(player, dict):
        merged = []
        assist = player.get("assistAvatar")
        if isinstance(assist, dict):
            merged.append(assist)
        display = player.get("displayAvatars") or []
        if isinstance(display, list):
            merged.extend(x for x in display if isinstance(x, dict))
        if merged:
            return _dedupe(merged)
    return []


def _nickname_from(data: Dict[str, Any]) -> str:
    return str(_dig(data, "nickname", "name", "playerInfo.nickname", "detailInfo.nickname", "playerDetailInfo.nickname", "data.nickname", "data.name", "data.playerInfo.nickname") or "")


def _level_from(data: Dict[str, Any]) -> Optional[int]:
    level = _dig(data, "level", "playerInfo.level", "detailInfo.level", "playerDetailInfo.level", "data.level", "data.playerInfo.level")
    return level if isinstance(level, int) else None


def _cache_key(source: str, game: str) -> str:
    return f"{source}:{game}" if game != "gs" else source


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _name_from_avatar(avatar: Dict[str, Any]) -> str:
    for key in ("name", "avatar_name", "avatarName"):
        value = avatar.get(key)
        if value:
            return str(value)
    return str(((avatar.get("character") or {}).get("name")) or "")


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resource_candidates(*parts: str) -> List[Path]:
    root = _plugin_root()
    return [
        root / "resources" / Path(*parts),
        root.parent / "miao-plugin" / "resources" / Path(*parts),
        root.parent / "miao-plugin" / Path(*parts),
    ]


@lru_cache(maxsize=128)
def _load_resource_json(*parts: str) -> Dict[str, Any]:
    for path in _resource_candidates(*parts):
        if not path.exists():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            try:
                return json.loads(path.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
    return {}


@lru_cache(maxsize=1)
def _sr_artifact_meta() -> Dict[str, Any]:
    return _load_resource_json("meta-sr", "artifact", "meta.json")


@lru_cache(maxsize=1)
def _sr_artifact_data() -> Dict[str, Any]:
    return _load_resource_json("meta-sr", "artifact", "data.json")


@lru_cache(maxsize=256)
def _sr_artifact_by_id(item_id: str) -> Dict[str, Any]:
    if not item_id:
        return {}
    for set_data in _sr_artifact_data().values():
        if not isinstance(set_data, dict):
            continue
        for idx, item in (set_data.get("idxs") or {}).items():
            ids = item.get("ids") if isinstance(item, dict) else {}
            if isinstance(ids, dict) and item_id in {str(x) for x in ids.keys()}:
                return {
                    "set_id": set_data.get("id"),
                    "set_name": set_data.get("name"),
                    "idx": int(idx),
                    "name": item.get("name"),
                    "star": ids.get(item_id),
                }
    return {}


@lru_cache(maxsize=256)
def _sr_character_meta_by_id(avatar_id: str) -> Dict[str, Any]:
    if not avatar_id:
        return {}
    base = _plugin_root()
    roots = [base / "resources" / "meta-sr" / "character", base.parent / "miao-plugin" / "resources" / "meta-sr" / "character"]
    for root in roots:
        if not root.exists():
            continue
        for data_path in root.glob("*/data.json"):
            try:
                data = json.loads(data_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if str(data.get("id") or "") == str(avatar_id):
                return data
    return {}


def _sr_prop_key(raw: Any) -> str:
    text = str(raw or "").strip()
    mapping = {
        "hp": "hp",
        "max_hp": "hp",
        "hp_pct": "hp",
        "hppercent": "hp",
        "atk": "atk",
        "attack": "atk",
        "atk_pct": "atk",
        "attackpercent": "atk",
        "def": "def",
        "defense": "def",
        "def_pct": "def",
        "speed": "speed",
        "spd": "speed",
        "crit_rate": "cpct",
        "critical_chance": "cpct",
        "cpct": "cpct",
        "crit_dmg": "cdmg",
        "crit_damage": "cdmg",
        "cdmg": "cdmg",
        "break_effect": "stance",
        "break_dmg": "stance",
        "stance": "stance",
        "effect_hit": "effPct",
        "effect_hit_rate": "effPct",
        "effpct": "effPct",
        "effect_res": "effDef",
        "effect_resistance": "effDef",
        "effdef": "effDef",
        "energy_recharge": "recharge",
        "energy_recovery": "recharge",
        "recharge": "recharge",
        "heal": "heal",
        "healing_boost": "heal",
        "dmg": "dmg",
        "damage": "dmg",
        "damage_boost": "dmg",
        "phy": "phy",
        "fire": "fire",
        "ice": "ice",
        "elec": "elec",
        "wind": "wind",
        "quantum": "quantum",
        "imaginary": "imaginary",
        "hpplus": "hpPlus",
        "atkplus": "atkPlus",
        "defplus": "defPlus",
    }
    return mapping.get(text, mapping.get(text.lower(), text))


def _sr_prop_display_value(key: str, value: Any) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value or "")
    if key in {"hp", "atk", "def", "cpct", "cdmg", "stance", "effPct", "effDef", "recharge", "heal", "dmg"}:
        return f"{num:.1f}%" if abs(num - round(num)) >= 0.01 else f"{round(num)}%"
    return f"{num:.1f}" if abs(num - round(num)) >= 0.01 else str(round(num))


def _sr_relic_attr(main_id: Any = None, sub: Optional[Dict[str, Any]] = None, level: int = 0, star: int = 5, idx: int = 1) -> Dict[str, Any]:
    meta = _sr_artifact_meta()
    star_data = (meta.get("starData") or {}).get(str(star)) or (meta.get("starData") or {}).get("5") or {}
    if main_id not in (None, ""):
        main_key = (((meta.get("mainIdx") or {}).get(str(idx)) or {}).get(str(main_id)))
        main_cfg = ((star_data.get("main") or {}).get(main_key) or {}) if main_key else {}
        if not main_key or not main_cfg:
            return {"key": str(main_id), "appendPropId": str(main_id), "value": "", "display": ""}
        value = float(main_cfg.get("base") or 0) + float(main_cfg.get("step") or 0) * max(level, 0)
        return {"key": main_key, "appendPropId": main_key, "value": value, "display": _sr_prop_display_value(main_key, value)}
    sub = sub or {}
    affix_id = sub.get("affixId") or sub.get("affix_id") or sub.get("id")
    sub_cfg = (star_data.get("sub") or {}).get(str(affix_id)) or {}
    key = sub_cfg.get("key") or str(affix_id or "")
    cnt = _to_int(sub.get("cnt") or sub.get("count"), 1)
    step = _to_int(sub.get("step"), 0)
    value = float(sub_cfg.get("base") or 0) * cnt + float(sub_cfg.get("step") or 0) * step
    base = float(sub_cfg.get("base") or 0)
    step_base = float(sub_cfg.get("step") or 0)
    eff_base = base + step_base * 2
    eff = value / eff_base if eff_base else 0
    return {
        "key": key,
        "appendPropId": key,
        "id": affix_id,
        "value": value,
        "display": _sr_prop_display_value(key, value),
        "cnt": cnt,
        "count": cnt,
        "step": step,
        "upNum": cnt,
        "eff": eff,
    }


def _sr_weapon_attrs(weapon: Dict[str, Any]) -> Dict[str, Any]:
    attrs = weapon.get("attrs") or weapon.get("attributes") or weapon.get("properties") or weapon.get("stats") or {}
    if isinstance(attrs, dict) and attrs:
        return attrs
    item_id = str(weapon.get("item_id") or weapon.get("itemId") or weapon.get("id") or weapon.get("tid") or "")
    weapon_index = _load_resource_json("meta-sr", "weapon", "data.json")
    name = ""
    type_name = ""
    if item_id and isinstance(weapon_index.get(item_id), dict):
        name = str(weapon_index[item_id].get("name") or "")
        type_name = str(weapon_index[item_id].get("type") or "")
    detail = _load_resource_json("meta-sr", "weapon", type_name, name, "data.json") if name and type_name else {}
    attr = detail.get("attr") if isinstance(detail.get("attr"), dict) else {}
    promote = str(weapon.get("promote") or weapon.get("promote_level") or weapon.get("promotion") or "")
    level = _to_int(weapon.get("level") or weapon.get("lv"), 0)
    best = attr.get(promote) if promote else None
    if not isinstance(best, dict):
        candidates = [x for x in attr.values() if isinstance(x, dict)]
        candidates.sort(key=lambda x: abs(_to_int(x.get("maxLevel"), level) - level))
        best = candidates[0] if candidates else {}
    return (best.get("attrs") or {}) if isinstance(best, dict) else {}


def _sr_weapon_from_avatar(avatar: Dict[str, Any]) -> Dict[str, Any]:
    weapon = avatar.get("light_cone") or avatar.get("lightCone") or avatar.get("equipment") or avatar.get("equip") or avatar.get("weapon") or {}
    if not isinstance(weapon, dict):
        return {}
    item_id = weapon.get("item_id") or weapon.get("itemId") or weapon.get("id") or weapon.get("tid")
    weapon_index = _load_resource_json("meta-sr", "weapon", "data.json")
    meta = weapon_index.get(str(item_id)) if isinstance(weapon_index.get(str(item_id)), dict) else {}
    return {
        "item_id": item_id,
        "name": weapon.get("name") or weapon.get("weapon_name") or weapon.get("weaponName") or meta.get("name"),
        "level": weapon.get("level") or weapon.get("lv"),
        "promote_level": weapon.get("promote") or weapon.get("promote_level") or weapon.get("promotion"),
        "refine": weapon.get("affix") or weapon.get("refine") or weapon.get("rank") or weapon.get("affix_level"),
        "rarity": weapon.get("star") or weapon.get("rarity") or meta.get("star"),
        "attrs": _sr_weapon_attrs({**weapon, "item_id": item_id}),
        "game": "sr",
    }


def _sr_reliquaries_from_avatar(avatar: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = avatar.get("reliquaries") or avatar.get("artifacts") or avatar.get("artis") or avatar.get("relicList") or avatar.get("relics") or []
    ornament_raw = avatar.get("ornaments") or []
    iterable: List[Any] = []
    for source in (raw, ornament_raw):
        if isinstance(source, dict):
            iterable.extend(source.values())
        elif isinstance(source, list):
            iterable.extend(source)
    reliqs: List[Dict[str, Any]] = []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id") or item.get("itemId") or item.get("id") or item.get("tid") or "")
        meta = _sr_artifact_by_id(item_id)
        idx = _to_int(item.get("type") or item.get("pos") or item.get("idx") or meta.get("idx"), len(reliqs) + 1)
        star = _to_int(item.get("star") or item.get("rarity") or meta.get("star"), 5)
        level = _to_int(item.get("level") or item.get("lv"), 0)
        main = item.get("main_prop") or item.get("mainProp") or item.get("main_affix") or item.get("mainAffix") or item.get("mainstat") or item.get("main")
        if isinstance(main, dict):
            main_prop = _norm_relic_prop(main)
        else:
            main_id = item.get("mainAffixId") or item.get("main_affix_id") or item.get("mainId") or item.get("mainPropId") or main
            main_prop = _sr_relic_attr(main_id=main_id, level=level, star=star, idx=idx)
        sub_raw = item.get("sub_props") or item.get("substats") or item.get("subStats") or item.get("sub_affix") or item.get("subAffix") or item.get("subAffixList") or item.get("sub_affix_id") or item.get("attrs") or []
        sub_props = [_sr_relic_attr(sub=x, star=star) if isinstance(x, dict) and (x.get("affixId") or x.get("affix_id") or x.get("id")) else _norm_relic_prop(x) for x in sub_raw]
        reliqs.append(
            {
                "item_id": item_id,
                "name": item.get("name") or meta.get("name"),
                "set_name": item.get("set") or item.get("set_name") or item.get("setName") or meta.get("set_name"),
                "pos": idx,
                "level": level,
                "rarity": star,
                "main_prop": main_prop,
                "sub_props": sub_props,
                "game": "sr",
            }
        )
    return reliqs


def _sr_fight_props_from_avatar(avatar: Dict[str, Any]) -> Dict[str, Any]:
    props = _props_from_avatar(avatar)
    if props:
        return props
    avatar_id = str(avatar.get("avatarId") or avatar.get("AvatarID") or avatar.get("id") or avatar.get("avatar_id") or "")
    meta = _sr_character_meta_by_id(avatar_id)
    base_attr = meta.get("baseAttr") if isinstance(meta.get("baseAttr"), dict) else {}
    weapon_attrs = _sr_weapon_from_avatar(avatar).get("attrs") or {}
    totals: Dict[str, float] = {
        "hp": float(base_attr.get("hp") or 0) + float(weapon_attrs.get("hp") or 0),
        "atk": float(base_attr.get("atk") or 0) + float(weapon_attrs.get("atk") or 0),
        "def": float(base_attr.get("def") or 0) + float(weapon_attrs.get("def") or 0),
        "speed": float(base_attr.get("speed") or 0),
        "cpct": float(base_attr.get("cpct") or 5),
        "cdmg": float(base_attr.get("cdmg") or 50),
        "stance": 0.0,
        "effPct": 0.0,
        "effDef": 0.0,
        "recharge": 100.0,
        "heal": 0.0,
        "dmg": 0.0,
    }
    pct_bonus = {"hp": 0.0, "atk": 0.0, "def": 0.0}
    flat_bonus = {"hp": 0.0, "atk": 0.0, "def": 0.0}
    for relic in _sr_reliquaries_from_avatar(avatar):
        for prop in [relic.get("main_prop"), *(relic.get("sub_props") or [])]:
            if not isinstance(prop, dict):
                continue
            key = _sr_prop_key(prop.get("key") or prop.get("appendPropId"))
            try:
                value = float(prop.get("value") or 0)
            except (TypeError, ValueError):
                continue
            if key == "hpPlus":
                flat_bonus["hp"] += value
            elif key == "atkPlus":
                flat_bonus["atk"] += value
            elif key == "defPlus":
                flat_bonus["def"] += value
            elif key in pct_bonus:
                pct_bonus[key] += value
            elif key in totals:
                totals[key] += value
            elif key in {"phy", "fire", "ice", "elec", "wind", "quantum", "imaginary"}:
                totals["dmg"] = max(totals["dmg"], value)
    for key in ("hp", "atk", "def"):
        totals[key] = totals[key] * (1 + pct_bonus[key] / 100) + flat_bonus[key]
    return {
        "生命值": round(totals["hp"]),
        "攻击力": round(totals["atk"]),
        "防御力": round(totals["def"]),
        "速度": round(totals["speed"], 1),
        "暴击率": round(totals["cpct"], 1),
        "暴击伤害": round(totals["cdmg"], 1),
        "伤害加成": round(totals["dmg"], 1),
        "击破特攻": round(totals["stance"], 1),
        "效果命中": round(totals["effPct"], 1),
        "效果抵抗": round(totals["effDef"], 1),
        "能量恢复效率": round(totals["recharge"], 1),
        "治疗加成": round(totals["heal"], 1),
    }


def _normalize_prop_name(name: Any) -> str:
    text = str(name or "").strip()
    mapping = {
        "max_hp": "生命值",
        "hp": "生命值",
        "attack": "攻击力",
        "atk": "攻击力",
        "defense": "防御力",
        "def": "防御力",
        "element_mastery": "元素精通",
        "mastery": "元素精通",
        "crit_rate": "暴击率",
        "critRate": "暴击率",
        "crit": "暴击率",
        "cpct": "暴击率",
        "crit_dmg": "暴击伤害",
        "critDamage": "暴击伤害",
        "crit_damage": "暴击伤害",
        "cdmg": "暴击伤害",
        "energy_recharge": "充能效率",
        "recharge": "充能效率",
        "speed": "速度",
        "spd": "速度",
        "break_effect": "击破特攻",
        "breakEffect": "击破特攻",
        "break_dmg": "击破特攻",
        "breakDamage": "击破特攻",
        "stance": "击破特攻",
        "effect_hit": "效果命中",
        "effectHitRate": "效果命中",
        "effect_hit_rate": "效果命中",
        "effPct": "效果命中",
        "effect_res": "效果抵抗",
        "effectRes": "效果抵抗",
        "effect_resistance": "效果抵抗",
        "effDef": "效果抵抗",
        "dmg": "伤害加成",
        "damage": "伤害加成",
    }
    return mapping.get(text, text)


def _props_from_avatar(avatar: Dict[str, Any]) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    source = avatar.get("fight_props") or avatar.get("fightProps") or avatar.get("properties") or avatar.get("attribute") or avatar.get("attributes") or avatar.get("attr") or avatar.get("attrs") or {}
    if isinstance(source, dict):
        for key, value in source.items():
            if isinstance(value, dict):
                value = value.get("display") or value.get("value_str") or value.get("valueStr") or value.get("value") or value.get("val") or value.get("total")
            props[_normalize_prop_name(key)] = value
    elif isinstance(source, list):
        for item in source:
            if not isinstance(item, dict):
                continue
            key = item.get("field") or item.get("key") or item.get("type") or item.get("name")
            value = item.get("display") or item.get("value_str") or item.get("valueStr") or item.get("value") or item.get("val") or item.get("total")
            if key and value not in (None, ""):
                props[_normalize_prop_name(key)] = value
    for src_key, dst_key in {
        "max_hp": "生命值",
        "hp": "生命值",
        "attack": "攻击力",
        "atk": "攻击力",
        "defense": "防御力",
        "def": "防御力",
        "element_mastery": "元素精通",
        "mastery": "元素精通",
        "crit_rate": "暴击率",
        "critRate": "暴击率",
        "crit": "暴击率",
        "cpct": "暴击率",
        "crit_dmg": "暴击伤害",
        "critDamage": "暴击伤害",
        "crit_damage": "暴击伤害",
        "cdmg": "暴击伤害",
        "energy_recharge": "充能效率",
        "recharge": "充能效率",
        "speed": "速度",
        "spd": "速度",
        "break_effect": "击破特攻",
        "breakEffect": "击破特攻",
        "break_dmg": "击破特攻",
        "breakDamage": "击破特攻",
        "stance": "击破特攻",
        "effect_hit": "效果命中",
        "effectHitRate": "效果命中",
        "effect_hit_rate": "效果命中",
        "effPct": "效果命中",
        "effect_res": "效果抵抗",
        "effectRes": "效果抵抗",
        "effect_resistance": "效果抵抗",
        "effDef": "效果抵抗",
        "dmg": "伤害加成",
        "damage": "伤害加成",
    }.items():
        if src_key in avatar and dst_key not in props:
            props[dst_key] = avatar[src_key]
    return props


def _weapon_from_avatar(avatar: Dict[str, Any]) -> Dict[str, Any]:
    weapon = avatar.get("weapon") or avatar.get("equipment") or {}
    if not isinstance(weapon, dict):
        return {}
    return {
        "item_id": weapon.get("item_id") or weapon.get("itemId") or weapon.get("id") or weapon.get("tid"),
        "name": weapon.get("name") or weapon.get("weapon_name") or weapon.get("weaponName"),
        "level": weapon.get("level") or weapon.get("lv"),
        "promote_level": weapon.get("promote") or weapon.get("promote_level"),
        "refine": weapon.get("affix") or weapon.get("refine") or weapon.get("rank") or weapon.get("affix_level"),
        "rarity": weapon.get("star") or weapon.get("rarity") or weapon.get("rankLevel"),
        "attrs": weapon.get("attrs") or weapon.get("attributes") or weapon.get("properties") or weapon.get("stats") or weapon.get("main"),
    }


def _norm_relic_prop(prop: Any) -> Any:
    if not isinstance(prop, dict):
        return prop
    return {
        "key": prop.get("key") or prop.get("field") or prop.get("type") or prop.get("appendPropId") or prop.get("mainPropId") or prop.get("name"),
        "appendPropId": prop.get("appendPropId") or prop.get("prop_id") or prop.get("key") or prop.get("field") or prop.get("type"),
        "name": prop.get("name") or prop.get("title"),
        "value": prop.get("value") if prop.get("value") not in (None, "") else prop.get("val") or prop.get("statValue") or prop.get("display") or prop.get("value_str") or prop.get("valueStr") or prop.get("base"),
        "display": prop.get("display") or prop.get("value_str") or prop.get("valueStr") or prop.get("formatted"),
        "cnt": prop.get("cnt") or prop.get("count") or prop.get("rolls") or prop.get("step"),
        "score": prop.get("score") or prop.get("mark"),
    }


def _reliquaries_from_avatar(avatar: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = avatar.get("reliquaries") or avatar.get("artifacts") or avatar.get("artis") or avatar.get("relics") or avatar.get("relicList") or []
    if isinstance(raw, dict):
        iterable = raw.values()
    elif isinstance(raw, list):
        iterable = raw
    else:
        iterable = []
    reliqs: List[Dict[str, Any]] = []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        reliqs.append(
            {
                "item_id": item.get("item_id") or item.get("itemId") or item.get("id") or item.get("tid"),
                "name": item.get("name"),
                "set_name": item.get("set") or item.get("set_name") or item.get("setName"),
                "pos": item.get("pos") or item.get("idx") or item.get("equipType"),
                "level": item.get("level") or item.get("lv"),
                "rarity": item.get("star") or item.get("rarity"),
                "main_prop": _norm_relic_prop(item.get("main_prop") or item.get("mainProp") or item.get("mainstat") or item.get("mainStat") or item.get("main")) if isinstance(item.get("main_prop") or item.get("mainProp") or item.get("mainstat") or item.get("mainStat") or item.get("main"), dict) else (item.get("main_prop") or item.get("mainId") or item.get("main") or item.get("mainPropId") or item.get("mainAffixId")),
                "sub_props": [_norm_relic_prop(x) for x in (item.get("sub_props") or item.get("substats") or item.get("subStats") or item.get("attrs") or item.get("attrIds") or item.get("appendPropIdList") or item.get("subAffixList") or [])],
            }
        )
    return reliqs


_MYS_PROP_NAMES = {
    2: "生命值",
    3: "生命值%",
    5: "攻击力",
    6: "攻击力%",
    8: "防御力",
    9: "防御力%",
    20: "暴击率",
    22: "暴击伤害",
    23: "充能效率",
    26: "治疗加成",
    28: "元素精通",
    30: "物理伤害加成",
    40: "火元素伤害加成",
    41: "雷元素伤害加成",
    42: "水元素伤害加成",
    43: "草元素伤害加成",
    44: "风元素伤害加成",
    45: "岩元素伤害加成",
    46: "冰元素伤害加成",
    2000: "生命值",
    2001: "攻击力",
    2002: "防御力",
}


def _mys_prop_name(prop: Dict[str, Any]) -> str:
    raw_type = prop.get("property_type") or prop.get("propertyType") or prop.get("type")
    name = _MYS_PROP_NAMES.get(_to_int(raw_type, -1))
    return name or str(prop.get("name") or prop.get("property_name") or raw_type or "")


def _mys_prop_value(prop: Dict[str, Any]) -> Any:
    for key in ("final", "base", "add", "value", "val"):
        value = prop.get(key)
        if value not in (None, ""):
            return value
    return prop.get("value_str") or prop.get("valueStr")


def _first_dict(*values: Any) -> Dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _extract_mys_detail_avatars(data: Any) -> List[Dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    avatars = _avatars_from(data)
    if avatars:
        return avatars
    inner = data.get("data")
    return _avatars_from(inner) if isinstance(inner, dict) else []


def _has_reliquary_props(rel: Dict[str, Any]) -> bool:
    main_prop = rel.get("main_property") or rel.get("main_prop") or rel.get("main")
    sub_props = rel.get("sub_property_list") or rel.get("sub_props") or rel.get("subProperties")
    if isinstance(main_prop, dict) and main_prop:
        return True
    if isinstance(sub_props, list) and any(isinstance(x, dict) and x for x in sub_props):
        return True
    return False


def _avatar_has_mys_detail(avatar: Dict[str, Any]) -> bool:
    if not isinstance(avatar, dict):
        return False
    if _props_from_avatar(avatar):
        return True
    for key in ("selected_properties", "base_properties", "extra_properties", "properties"):
        value = avatar.get(key)
        if isinstance(value, list) and value:
            return True
    for key in ("relics", "reliquaries", "artifacts", "relic_list", "relicList"):
        value = avatar.get(key)
        if isinstance(value, list) and any(isinstance(x, dict) and _has_reliquary_props(x) for x in value):
            return True
    return False


def _panel_has_mys_detail(result: PanelResult) -> bool:
    for char in result.characters or []:
        if not isinstance(char, dict):
            continue
        if char.get("fight_props"):
            return True
        for rel in char.get("reliquaries") or []:
            if isinstance(rel, dict) and (rel.get("main_prop") or rel.get("sub_props")):
                return True
    return False


def _mys_fight_props(avatar: Dict[str, Any]) -> Dict[str, Any]:
    props = _props_from_avatar(avatar)
    for key in ("selected_properties", "base_properties", "extra_properties", "properties"):
        values = avatar.get(key) or []
        if not isinstance(values, list):
            continue
        for prop in values:
            if not isinstance(prop, dict):
                continue
            name = _mys_prop_name(prop)
            if name:
                props[name] = _mys_prop_value(prop)
    return props


def _mys_skill_levels(avatar: Dict[str, Any]) -> List[int]:
    levels: List[int] = []
    for item in avatar.get("skills") or []:
        if not isinstance(item, dict):
            continue
        if _to_int(item.get("skill_type") or item.get("skillType"), 1) != 1:
            continue
        level = item.get("level") or item.get("lv")
        if level is not None:
            levels.append(_to_int(level))
    return levels[:3]


def _mys_reliquaries(avatar: Dict[str, Any]) -> List[Dict[str, Any]]:
    reliqs: List[Dict[str, Any]] = []
    for item in avatar.get("relics") or avatar.get("reliquaries") or avatar.get("artifacts") or avatar.get("relic_list") or avatar.get("relicList") or []:
        if not isinstance(item, dict):
            continue
        main_prop = item.get("main_property") or item.get("main_prop") or item.get("main")
        sub_props = item.get("sub_property_list") or item.get("sub_props") or item.get("subProperties") or []
        item_set = item.get("set") or {}
        reliqs.append(
            {
                "item_id": item.get("id") or item.get("item_id") or item.get("itemId"),
                "name": item.get("name"),
                "set_name": item_set.get("name") if isinstance(item_set, dict) else item.get("set_name"),
                "pos": item.get("pos") or item.get("idx") or item.get("equipType"),
                "level": min(20, _to_int(item.get("level") or item.get("lv"))),
                "rarity": item.get("rarity") or item.get("star"),
                "main_prop": main_prop,
                "sub_props": sub_props,
            }
        )
    return reliqs


def _characters_from_mys_avatars(avatars: List[Dict[str, Any]], game: str = "gs") -> List[Dict[str, Any]]:
    characters: List[Dict[str, Any]] = []
    for avatar in avatars:
        if not isinstance(avatar, dict):
            continue
        base = avatar.get("base") if isinstance(avatar.get("base"), dict) else avatar
        characters.append(
            {
                "avatar_id": base.get("id") or avatar.get("id") or avatar.get("avatar_id") or avatar.get("avatarId"),
                "name": base.get("name") or _name_from_avatar(avatar),
                "element": base.get("element") or avatar.get("element"),
                "rarity": base.get("rarity") or avatar.get("rarity"),
                "level": base.get("level") or avatar.get("level") or avatar.get("lv"),
                "promote_level": base.get("promote_level") or avatar.get("promote") or avatar.get("promote_level"),
                "constellation": base.get("actived_constellation_num") or avatar.get("actived_constellation_num") or avatar.get("cons") or avatar.get("constellation"),
                "friendship": base.get("fetter") or avatar.get("fetter") or avatar.get("friendship"),
                "skill_levels": _mys_skill_levels(avatar) or avatar.get("skill_levels") or avatar.get("talent") or avatar.get("talents") or [],
                "weapon": _weapon_from_avatar(avatar),
                "reliquaries": _mys_reliquaries(avatar) or _reliquaries_from_avatar(avatar),
                "fight_props": _mys_fight_props(avatar),
                "game": game,
            }
        )
    return characters


def _characters_from_avatars(avatars: List[Dict[str, Any]], game: str = "gs") -> List[Dict[str, Any]]:
    characters: List[Dict[str, Any]] = []
    for avatar in avatars:
        if not isinstance(avatar, dict):
            continue
        base = avatar.get("base") if isinstance(avatar.get("base"), dict) else avatar
        is_sr = game in {"sr", "starrail", "hkrpg"}
        avatar_id = base.get("id") or avatar.get("id") or avatar.get("avatar_id") or avatar.get("avatarId") or avatar.get("AvatarID")
        sr_meta = _sr_character_meta_by_id(str(avatar_id or "")) if is_sr else {}
        characters.append(
            {
                "avatar_id": avatar_id,
                "name": base.get("name") or _name_from_avatar(avatar) or sr_meta.get("name"),
                "element": base.get("element") or avatar.get("element") or sr_meta.get("elem"),
                "rarity": base.get("rarity") or avatar.get("rarity") or sr_meta.get("star"),
                "level": base.get("level") or avatar.get("level") or avatar.get("lv"),
                "promote_level": base.get("promote_level") or avatar.get("promote") or avatar.get("promote_level") or avatar.get("promotion"),
                "constellation": base.get("actived_constellation_num") or avatar.get("cons") or avatar.get("constellation") or avatar.get("actived_constellation_num") or avatar.get("rank") or 0,
                "friendship": base.get("fetter") or avatar.get("fetter") or avatar.get("friendship"),
                "skill_levels": _mys_skill_levels(avatar) or avatar.get("skill_levels") or avatar.get("talent") or avatar.get("talents") or [x.get("level") or x.get("Level") for x in avatar.get("skillTreeList") or [] if isinstance(x, dict) and (x.get("level") or x.get("Level"))],
                "weapon": _sr_weapon_from_avatar(avatar) if is_sr else _weapon_from_avatar(avatar),
                "reliquaries": (_sr_reliquaries_from_avatar(avatar) if is_sr else (_mys_reliquaries(avatar) or _reliquaries_from_avatar(avatar))),
                "fight_props": _sr_fight_props_from_avatar(avatar) if is_sr else _mys_fight_props(avatar),
                "game": game,
            }
        )
    return characters


def _signature_from(data: Dict[str, Any]) -> str:
    return str(_dig(data, "signature", "playerInfo.signature", "detailInfo.signature", "playerDetailInfo.signature", "data.signature", "data.playerInfo.signature") or "")


def _server_id(uid: str) -> str:
    return "cn_qd01" if str(uid).startswith("5") else "cn_gf01"


def _starrail_server_id(uid: str) -> str:
    return "prod_qd_cn" if str(uid).startswith("5") else "prod_gf_cn"


MYS_API_BASE_URL = "https://api-takumi-record.mihoyo.com"


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _mys_ds(q: str = "", b: Optional[Dict[str, Any]] = None) -> str:
    salt = str(MiaoConfig.get_config("MysDsSalt").data or "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs")
    body = json.dumps(b) if b else ""
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = _md5(f"salt={salt}&t={t}&r={r}&b={body}&q={q}")
    return f"{t},{r},{c}"


def _mys_query(params: Dict[str, Any], sort_keys: bool = False) -> str:
    items = sorted(params.items(), key=lambda x: x[0]) if sort_keys else params.items()
    return "&".join(f"{k}={str(v).lower() if isinstance(v, bool) else v}" for k, v in items)


def _exception_message(exc: Exception) -> str:
    text = str(exc).strip()
    return text or exc.__class__.__name__


def _mys_headers(cookie: str, q: str = "", b: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    device_id = str(MiaoConfig.get_config("MysDeviceId").data or "").strip().lower()
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
        "X-Requested-With": "com.mihoyo.hyperion",
        "Referer": "https://webstatic.mihoyo.com/",
        "Origin": "https://webstatic.mihoyo.com/",
    }
    if device_id:
        headers["x-rpc-device_id"] = device_id
    if device_fp:
        headers["x-rpc-device_fp"] = device_fp
    return headers


async def _fill_gscore_device_headers(headers: Dict[str, str], uid: str, game: str = "gs") -> Dict[str, str]:
    if headers.get("x-rpc-device_fp") and headers.get("x-rpc-device_id"):
        return headers
    try:
        device_id, device_fp = await asyncio.wait_for(
            asyncio.gather(
                mys_api.get_user_device_id(uid, game),
                mys_api.get_user_fp(uid, game),
            ),
            timeout=5,
        )
        if device_id:
            headers["x-rpc-device_id"] = str(device_id)
        if device_fp:
            headers["x-rpc-device_fp"] = str(device_fp)
    except (asyncio.TimeoutError, TimeoutError):
        pass
    except Exception:
        pass
    if not headers.get("x-rpc-device_id"):
        headers["x-rpc-device_id"] = str(uuid.uuid4()).lower()
    return headers


def _check_retcode(source: str, raw: Dict[str, Any]) -> None:
    retcode = raw.get("retcode", raw.get("code", 0))
    if retcode not in (0, "0", None):
        if _is_mys_dead_code(raw):
            raise PanelSourceError(source, _mys_code_message(retcode))
        msg = raw.get("message") or raw.get("msg") or raw.get("error") or "未知错误"
        raise PanelSourceError(source, f"接口返回 {retcode}: {msg}")


def _retcode(raw: Dict[str, Any]) -> Any:
    return raw.get("retcode", raw.get("code", 0))


def _is_mys_dead_code(raw: Dict[str, Any]) -> bool:
    return _retcode(raw) in {10035, 5003, 10041, 1034, "10035", "5003", "10041", "1034"}


def _mys_code_message(code: Any) -> str:
    messages = {
        -51: "米游社 Cookie 未配置或不可用",
        -999: "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
        10035: "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
        "10035": "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
        1034: "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
        "1034": "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
    }
    return messages.get(code, f"接口返回 {code}")


def _add_mys_challenge_headers(headers: Dict[str, str], q: str = "", b: Optional[Dict[str, Any]] = None, game: str = "gs") -> Dict[str, str]:
    fixed = dict(headers)
    if game in {"sr", "starrail", "hkrpg"}:
        fixed["x-rpc-challenge_game"] = "6"
        fixed["x-rpc-page"] = "v1.4.1-rpg_#/rpg"
        fixed["x-rpc-tool-verison"] = "v1.4.1-rpg"
    else:
        fixed["x-rpc-challenge_game"] = "2"
        fixed["x-rpc-page"] = "v4.1.5-ys_#ys"
        fixed["x-rpc-tool-verison"] = "v4.1.5-ys"
    fixed["DS"] = _mys_ds(q, b)
    return fixed


def _http_error_message(source: str, exc: httpx.HTTPStatusError) -> str:
    status = exc.response.status_code
    if source == "enka" and status == 424:
        return "Enka 暂时没有该 UID 的公开面板缓存，请先在游戏内展示角色，稍后重试，或切换到 auto/Miao/米游社数据源"
    if source == "enka" and status == 404:
        return "Enka 未找到该 UID，请确认 UID 正确且角色展柜已公开"
    return f"HTTP {status}: {exc.response.reason_phrase}"


def _enka_fight_props(props: Dict[str, Any]) -> Dict[str, Any]:
    def number(key: str, default: float = 0) -> float:
        value = props.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    result = {
        "生命值": round(number("2000")),
        "攻击力": round(number("2001")),
        "防御力": round(number("2002")),
        "元素精通": round(number("28")),
        "暴击率": round(number("20") * 100, 1),
        "暴击伤害": round(number("22") * 100, 1),
        "充能效率": round(number("23") * 100, 1),
        "治疗加成": round(number("26") * 100, 1),
    }
    element_values = [
        number("30"),  # 物理
        number("40"),  # 火
        number("41"),  # 雷
        number("42"),  # 水
        number("43"),  # 草
        number("44"),  # 风
        number("45"),  # 岩
        number("46"),  # 冰
    ]
    dmg = max(element_values) if element_values else 0
    if dmg:
        result["伤害加成"] = round(dmg * 100, 1)
        result["元素伤害加成"] = round(dmg * 100, 1)
    return result


def _enka_skill_levels(skill_map: Dict[str, Any]) -> List[int]:
    levels: List[int] = []
    for key in sorted(skill_map.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x)):
        value = skill_map.get(key)
        if isinstance(value, int):
            levels.append(value)
    return levels


def _enka_weapon(equip_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    for equip in equip_list:
        if equip.get("weapon"):
            flat = equip.get("flat") or {}
            weapon = equip.get("weapon") or {}
            item_id = weapon.get("itemId") or equip.get("itemId")
            refine_values = list((weapon.get("affixMap") or {}).values())
            stats = [x for x in flat.get("weaponStats") or [] if isinstance(x, dict)]
            attrs = {}
            for stat in stats:
                key = stat.get("appendPropId")
                value = stat.get("statValue")
                if key and value is not None:
                    attrs[key] = value
            return {
                "item_id": item_id,
                "name": flat.get("nameTextMapHash") or str(item_id or "未知武器"),
                "level": weapon.get("level"),
                "promote_level": weapon.get("promoteLevel"),
                "refine": (_to_int(refine_values[0]) + 1) if refine_values else 1,
                "rarity": flat.get("rankLevel"),
                "attrs": attrs,
                "stats": stats,
            }
    return {}


def _enka_reliquaries(equip_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    reliquaries: List[Dict[str, Any]] = []
    for equip in equip_list:
        reliq = equip.get("reliquary")
        if not isinstance(reliq, dict):
            continue
        flat = equip.get("flat") or {}
        main_stat = flat.get("reliquaryMainstat") or {}
        reliquaries.append(
            {
                "item_id": equip.get("itemId"),
                "name": flat.get("nameTextMapHash") or str(equip.get("itemId") or "未知圣遗物"),
                "set_name": flat.get("setNameTextMapHash"),
                "pos": flat.get("equipType"),
                "level": reliq.get("level"),
                "rarity": flat.get("rankLevel"),
                "main_prop": {
                    "key": main_stat.get("mainPropId"),
                    "value": main_stat.get("statValue"),
                },
                "sub_props": [
                    {
                        "key": x.get("appendPropId"),
                        "appendPropId": x.get("appendPropId"),
                        "value": x.get("statValue"),
                    }
                    for x in flat.get("reliquarySubstats") or []
                    if isinstance(x, dict)
                ],
            }
        )
    return reliquaries


def _parse_enka_characters(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    characters: List[Dict[str, Any]] = []
    for avatar in raw.get("avatarInfoList") or []:
        if not isinstance(avatar, dict):
            continue
        prop_map = avatar.get("propMap") or {}
        fight_props = avatar.get("fightPropMap") or {}
        equip_list = avatar.get("equipList") or []
        skill_map = avatar.get("skillLevelMap") or {}
        characters.append(
            {
                "avatar_id": avatar.get("avatarId"),
                "level": (prop_map.get("4001") or {}).get("val"),
                "promote_level": avatar.get("propMap", {}).get("1002", {}).get("ival"),
                "constellation": len(avatar.get("talentIdList") or []),
                "friendship": (prop_map.get("10010") or {}).get("val"),
                "skill_levels": _enka_skill_levels(skill_map),
                "weapon": _enka_weapon(equip_list),
                "reliquaries": _enka_reliquaries(equip_list),
                "fight_props": _enka_fight_props(fight_props),
            }
        )
    return characters


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
        except httpx.HTTPStatusError as e:
            raise PanelSourceError(self.source_name, _http_error_message(self.source_name, e)) from e
        except Exception as e:
            raise PanelSourceError(self.source_name, f"Enka 请求失败：{e}") from e

        player = raw.get("playerInfo") or {}
        characters = _parse_enka_characters(raw)
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=str(player.get("nickname") or ""),
            level=player.get("level"),
            signature=str(player.get("signature") or ""),
            avatars=raw.get("avatarInfoList") or [],
            characters=characters,
            game="gs",
        )
        set_cached_panel(self.source_name, uid, result)
        return result


class MiaoPanelSource(BasePanelSource):
    source_name = "miao"

    def __init__(self, game: str = "gs"):
        self.game = "sr" if game in {"sr", "starrail", "hkrpg"} else "gs"

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(_cache_key(self.source_name, self.game), uid)
        if cached:
            return cached

        base_url = _strip_url(MiaoConfig.get_config("MiaoApiBaseUrl").data)
        qq = str(MiaoConfig.get_config("MiaoApiQQ").data or "").strip()
        token = str(MiaoConfig.get_config("MiaoApiToken").data or "").strip()
        game = self.game or str(MiaoConfig.get_config("MiaoApiGame").data or "gs")
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
        except httpx.HTTPStatusError as e:
            raise PanelSourceError(self.source_name, _http_error_message(self.source_name, e)) from e
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
            characters=_characters_from_avatars(_avatars_from(data), self.game),
            game=self.game,
        )
        set_cached_panel(_cache_key(self.source_name, self.game), uid, result)
        return result


class MysPanelSource(BasePanelSource):
    source_name = "mys"

    def __init__(self, cookie: str = "", game: str = "gs"):
        self.cookie = cookie
        self.game = "sr" if game in {"sr", "starrail", "hkrpg"} else "gs"

    async def _fetch_with_gscore_api(self, uid: str, cookie: str) -> PanelResult:
        index_data = await mys_api.get_info(uid, cookie)
        if not isinstance(index_data, dict):
            raise PanelSourceError(self.source_name, _mys_code_message(index_data))

        avatars = index_data.get("avatars") if isinstance(index_data, dict) else []
        character_ids = [x.get("id") for x in avatars if isinstance(x, dict) and x.get("id")]
        detail_data: Dict[str, Any] = {}
        if character_ids:
            detail_ret = await mys_api.get_character(uid, character_ids, cookie)
            if not isinstance(detail_ret, dict):
                raise PanelSourceError(self.source_name, _mys_code_message(detail_ret))
            detail_data = detail_ret

        data = deepcopy(index_data)
        detail_avatars = _extract_mys_detail_avatars(detail_data)
        if detail_avatars:
            data["avatars"] = detail_avatars
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw={"index": {"retcode": 0, "data": index_data}, "detail": {"retcode": 0, "data": detail_data}},
            nickname=str((data.get("role") or {}).get("nickname") or ""),
            level=(data.get("role") or {}).get("level"),
            signature="",
            avatars=data.get("avatars") or [],
            characters=_characters_from_mys_avatars(data.get("avatars") or [], "gs"),
            game="gs",
        )
        if character_ids and not any(_avatar_has_mys_detail(x) for x in detail_avatars):
            raise PanelSourceError(self.source_name, "米游社角色详情缺少属性/圣遗物数据")
        return result

    async def _fetch_with_record_api(self, uid: str, cookie: str) -> PanelResult:
        base_url = _strip_url(MiaoConfig.get_config("MysApiBaseUrl").data) or MYS_API_BASE_URL
        server = _server_id(uid)
        index_params = {"role_id": uid, "server": server}
        index_q = _mys_query(index_params)
        index_url = urljoin(f"{base_url}/", "game_record/app/genshin/api/index")
        try:
            async with httpx.AsyncClient(timeout=_mys_timeout()) as client:
                index_headers = await _fill_gscore_device_headers(_mys_headers(cookie, index_q), uid, "gs")
                index_raw = await self._get_json_with_retry(
                    client,
                    index_url,
                    index_params,
                    index_headers,
                    index_q,
                )

                index_data = index_raw.get("data") if isinstance(index_raw.get("data"), dict) else {}
                avatars = index_data.get("avatars") if isinstance(index_data, dict) else []
                character_ids = [x.get("id") for x in avatars if isinstance(x, dict) and x.get("id")]
                detail_raw: Dict[str, Any] = {}
                if character_ids:
                    detail_body = {"character_ids": character_ids, "role_id": uid, "server": server}
                    detail_url = urljoin(f"{base_url}/", "game_record/app/genshin/api/character/list")
                    detail_headers = await _fill_gscore_device_headers(_mys_headers(cookie, "", detail_body), uid, "gs")
                    detail_raw = await self._post_json_with_retry(
                        client,
                        detail_url,
                        detail_body,
                        detail_headers,
                    )

                raw = {"index": index_raw, "detail": detail_raw}
        except httpx.HTTPStatusError as e:
            raise PanelSourceError(self.source_name, _http_error_message(self.source_name, e)) from e
        except Exception as e:
            raise PanelSourceError(self.source_name, f"米游社请求失败：{_exception_message(e)}") from e

        detail_data = detail_raw.get("data") if isinstance(detail_raw.get("data"), dict) else detail_raw
        data = deepcopy(index_data)
        detail_avatars = _extract_mys_detail_avatars(detail_data)
        if detail_avatars:
            data["avatars"] = detail_avatars
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=str((data.get("role") or {}).get("nickname") or ""),
            level=(data.get("role") or {}).get("level"),
            signature="",
            avatars=data.get("avatars") or [],
            characters=_characters_from_mys_avatars(data.get("avatars") or [], "gs"),
            game="gs",
        )
        if character_ids and not _panel_has_mys_detail(result):
            raise PanelSourceError(self.source_name, "米游社角色详情缺少属性/圣遗物数据")
        return result

    async def _fetch_starrail_avatar_info(self, uid: str, cookie: str) -> PanelResult:
        base_url = _strip_url(MiaoConfig.get_config("MysApiBaseUrl").data) or MYS_API_BASE_URL
        params = {"role_id": uid, "server": _starrail_server_id(uid)}
        q = _mys_query(params)
        url = urljoin(f"{base_url}/", "game_record/app/hkrpg/api/avatar/info")
        try:
            async with httpx.AsyncClient(timeout=_mys_timeout()) as client:
                headers = await _fill_gscore_device_headers(_mys_headers(cookie, q), uid, "sr")
                raw = await self._get_json_with_retry(client, url, params, headers, q)
        except httpx.HTTPStatusError as e:
            raise PanelSourceError(self.source_name, _http_error_message(self.source_name, e)) from e
        except Exception as e:
            raise PanelSourceError(self.source_name, f"星铁米游社请求失败：{_exception_message(e)}") from e

        data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
        avatars = data.get("avatar_list") or data.get("avatars") or []
        if not isinstance(avatars, list):
            avatars = []
        result = PanelResult(
            source=self.source_name,
            uid=uid,
            raw=raw,
            nickname=str((data.get("role") or {}).get("nickname") or ""),
            level=(data.get("role") or {}).get("level"),
            signature="",
            avatars=avatars,
            characters=_characters_from_avatars(avatars, "sr"),
            game="sr",
        )
        set_cached_panel(_cache_key(self.source_name, "sr"), uid, result)
        return result

    async def _get_json_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        q: str,
    ) -> Dict[str, Any]:
        resp = await self._request_json_with_timeout_retry(client, "GET", url, params=params, headers=headers)
        resp.raise_for_status()
        raw = _as_dict(resp.json())
        if _is_mys_dead_code(raw):
            retry_q = _mys_query(params, sort_keys=True)
            resp = await self._request_json_with_timeout_retry(
                client,
                "GET",
                url,
                params=params,
                headers=_add_mys_challenge_headers(headers, retry_q, game=self.game),
            )
            resp.raise_for_status()
            raw = _as_dict(resp.json())
        _check_retcode(self.source_name, raw)
        return raw

    async def _post_json_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        body: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        resp = await self._request_json_with_timeout_retry(client, "POST", url, json=body, headers=headers)
        resp.raise_for_status()
        raw = _as_dict(resp.json())
        if _is_mys_dead_code(raw):
            resp = await self._request_json_with_timeout_retry(
                client,
                "POST",
                url,
                json=body,
                headers=_add_mys_challenge_headers(headers, "", body, self.game),
            )
            resp.raise_for_status()
            raw = _as_dict(resp.json())
        _check_retcode(self.source_name, raw)
        return raw

    async def _request_json_with_timeout_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        last_error: httpx.ReadTimeout | None = None
        for _ in range(2):
            try:
                return await client.request(method, url, **kwargs)
            except httpx.ReadTimeout as e:
                last_error = e
        if last_error:
            raise last_error
        raise httpx.ReadTimeout("米游社请求读取超时")

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(_cache_key(self.source_name, self.game), uid)
        if cached:
            if self.game == "gs" and not _panel_has_mys_detail(cached):
                cached = None
            else:
                return cached

        cookie = self.cookie or str(MiaoConfig.get_config("MysCookie").data or "").strip()
        if not cookie:
            raise PanelSourceError(self.source_name, "米游社 Cookie 未配置")

        if self.game == "sr":
            return await self._fetch_starrail_avatar_info(uid, cookie)

        gscore_error: PanelSourceError | None = None
        try:
            result = await self._fetch_with_gscore_api(uid, cookie)
            if _panel_has_mys_detail(result):
                set_cached_panel(_cache_key(self.source_name, self.game), uid, result)
                return result
            gscore_error = PanelSourceError(self.source_name, "米游社角色详情缺少属性/圣遗物数据")
        except PanelSourceError as e:
            gscore_error = e
        except Exception as e:
            gscore_error = PanelSourceError(self.source_name, f"米游社请求失败：{_exception_message(e)}")

        try:
            result = await self._fetch_with_record_api(uid, cookie)
        except PanelSourceError as e:
            if gscore_error and "缺少属性/圣遗物数据" not in str(e):
                raise e
            if gscore_error:
                raise gscore_error
            raise
        set_cached_panel(_cache_key(self.source_name, self.game), uid, result)
        return result


class SimpleHttpPanelSource(BasePanelSource):
    def __init__(self, source_name: str, config_key: str, path_template: str, game: str = "gs"):
        self.source_name = source_name
        self.config_key = config_key
        self.path_template = path_template
        self.game = "sr" if game in {"sr", "starrail", "hkrpg"} else "gs"

    async def fetch(self, uid: str) -> PanelResult:
        cached = get_cached_panel(_cache_key(self.source_name, self.game), uid)
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
        except httpx.HTTPStatusError as e:
            raise PanelSourceError(self.source_name, _http_error_message(self.source_name, e)) from e
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
            characters=_characters_from_avatars(_avatars_from(data), self.game),
            game=self.game,
        )
        set_cached_panel(_cache_key(self.source_name, self.game), uid, result)
        return result


def get_source(name: str) -> BasePanelSource:
    return get_source_with_context(name)


def get_source_with_context(name: str, user_cfg: Optional[Dict[str, Any]] = None, game: str = "gs") -> BasePanelSource:
    user_cfg = user_cfg or {}
    game = "sr" if game in {"sr", "starrail", "hkrpg"} else "gs"
    source_map = {
        "enka": EnkaPanelSource,
    }
    if name in source_map:
        return source_map[name]()
    if name == "miao":
        return MiaoPanelSource(game)
    if name == "mys":
        return MysPanelSource(str(user_cfg.get("mys_cookie") or "").strip(), game)
    if name == "mgg":
        return SimpleHttpPanelSource("mgg", "MggApiBaseUrl", "api/uid/{uid}")
    if name == "hutao":
        return SimpleHttpPanelSource("hutao", "HutaoApiBaseUrl", "{uid}")
    if name in {"mihomo", "homo"}:
        return SimpleHttpPanelSource("mihomo", "MihomoApiBaseUrl", "{uid}", "sr")
    if name == "avocado":
        return SimpleHttpPanelSource("avocado", "AvocadoApiBaseUrl", "{uid}", "sr")
    if name in {"enkahsr", "enkaHSR"}:
        return SimpleHttpPanelSource("enkahsr", "EnkaHSRApiBaseUrl", "{uid}", "sr")
    raise PanelSourceError(name, "未知面板数据源")


def get_source_order(user_source: str, game: str = "gs") -> List[str]:
    allowed = set(MiaoConfig.get_config("AllowedPanelServers").data)
    game = "sr" if game in {"sr", "starrail", "hkrpg"} else "gs"
    user_source = {"homo": "mihomo", "enkaHSR": "enkahsr"}.get(user_source, user_source)
    if game == "sr":
        # 兼容已生成过旧配置的部署：旧 AllowedPanelServers 里没有星铁公开源时，仍允许星铁 auto 回退。
        allowed |= {"auto", "miao", "mys", "mihomo", "avocado", "enkahsr"}
        allowed = {x for x in allowed if x in {"auto", "miao", "mys", "mihomo", "avocado", "enkahsr"}}
    if user_source and user_source != "auto":
        if user_source not in allowed:
            return []
        fallback = bool(MiaoConfig.get_config("EnablePanelFallback").data)
        if not fallback:
            return [user_source]
        priority = [x for x in MiaoConfig.get_config("PanelSourcePriority").data if x in allowed]
        if game == "sr" and not priority:
            priority = [x for x in ["miao", "mihomo", "avocado", "enkahsr"] if x in allowed]
        return [user_source] + [x for x in priority if x != user_source]

    if game == "sr":
        return [x for x in ["miao", "mihomo", "avocado", "enkahsr"] if x in allowed] or ["mihomo"]
    order = [x for x in MiaoConfig.get_config("PanelSourcePriority").data if x in allowed]
    return order or [x for x in ["miao", "enka", "mys"] if x in allowed]
