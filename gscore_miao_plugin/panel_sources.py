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
from gsuid_core.utils.api.mys_api import mys_api

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
    if isinstance(avatars, list):
        return avatars
    detail = _dig(data, "detailInfo", "data.detailInfo")
    if isinstance(detail, dict):
        merged: List[Dict[str, Any]] = []
        for key in ("assistAvatarList", "avatarDetailList"):
            value = detail.get(key) or []
            if isinstance(value, list):
                merged.extend(x for x in value if isinstance(x, dict))
        if merged:
            return merged
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
            return merged
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
        "crit_dmg": "暴击伤害",
        "critDamage": "暴击伤害",
        "energy_recharge": "充能效率",
        "recharge": "充能效率",
        "speed": "速度",
        "spd": "速度",
        "break_effect": "击破特攻",
        "breakEffect": "击破特攻",
        "effect_hit": "效果命中",
        "effectHitRate": "效果命中",
        "effect_res": "效果抵抗",
        "effectRes": "效果抵抗",
    }
    return mapping.get(text, text)


def _props_from_avatar(avatar: Dict[str, Any]) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    source = avatar.get("fight_props") or avatar.get("fightProps") or avatar.get("attr") or avatar.get("attrs") or {}
    if isinstance(source, dict):
        for key, value in source.items():
            if isinstance(value, dict):
                value = value.get("value") or value.get("val") or value.get("total")
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
        "crit_dmg": "暴击伤害",
        "critDamage": "暴击伤害",
        "energy_recharge": "充能效率",
        "recharge": "充能效率",
        "speed": "速度",
        "spd": "速度",
        "break_effect": "击破特攻",
        "breakEffect": "击破特攻",
        "effect_hit": "效果命中",
        "effectHitRate": "效果命中",
        "effect_res": "效果抵抗",
        "effectRes": "效果抵抗",
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
                "main_prop": item.get("main_prop") or item.get("mainId") or item.get("main") or item.get("mainPropId") or item.get("mainAffixId"),
                "sub_props": item.get("sub_props") or item.get("attrs") or item.get("attrIds") or item.get("appendPropIdList") or item.get("subAffixList") or [],
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
    for item in avatar.get("relics") or avatar.get("reliquaries") or []:
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
        characters.append(
            {
                "avatar_id": base.get("id") or avatar.get("id") or avatar.get("avatar_id") or avatar.get("avatarId"),
                "name": base.get("name") or _name_from_avatar(avatar),
                "element": base.get("element") or avatar.get("element"),
                "rarity": base.get("rarity") or avatar.get("rarity"),
                "level": base.get("level") or avatar.get("level") or avatar.get("lv"),
                "promote_level": base.get("promote_level") or avatar.get("promote") or avatar.get("promote_level"),
                "constellation": base.get("actived_constellation_num") or avatar.get("cons") or avatar.get("constellation") or avatar.get("actived_constellation_num"),
                "friendship": base.get("fetter") or avatar.get("fetter") or avatar.get("friendship"),
                "skill_levels": _mys_skill_levels(avatar) or avatar.get("skill_levels") or avatar.get("talent") or avatar.get("talents") or [],
                "weapon": _weapon_from_avatar(avatar),
                "reliquaries": _mys_reliquaries(avatar) or _reliquaries_from_avatar(avatar),
                "fight_props": _mys_fight_props(avatar),
                "game": game,
            }
        )
    return characters


def _signature_from(data: Dict[str, Any]) -> str:
    return str(_dig(data, "signature", "playerInfo.signature", "detailInfo.signature", "playerDetailInfo.signature", "data.signature", "data.playerInfo.signature") or "")


def _server_id(uid: str) -> str:
    return "cn_qd01" if str(uid).startswith("5") else "cn_gf01"


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


def _retcode(raw: Dict[str, Any]) -> Any:
    return raw.get("retcode", raw.get("code", 0))


def _is_mys_dead_code(raw: Dict[str, Any]) -> bool:
    return _retcode(raw) in {10035, 5003, 10041, 1034, "10035", "5003", "10041", "1034"}


def _mys_code_message(code: Any) -> str:
    messages = {
        -51: "米游社 Cookie 未配置或不可用",
        -999: "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
        1034: "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
        "1034": "米游社风控验证失败，请稍后重试或检查 Cookie/设备指纹",
    }
    return messages.get(code, f"接口返回 {code}")


def _add_mys_challenge_headers(headers: Dict[str, str], q: str = "", b: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    fixed = dict(headers)
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
        if isinstance(detail_data.get("list"), list):
            data["avatars"] = detail_data["list"]
        return PanelResult(
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

    async def _get_json_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        q: str,
    ) -> Dict[str, Any]:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        raw = _as_dict(resp.json())
        if _is_mys_dead_code(raw):
            resp = await client.get(url, params=params, headers=_add_mys_challenge_headers(headers, q))
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
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        raw = _as_dict(resp.json())
        if _is_mys_dead_code(raw):
            resp = await client.post(url, json=body, headers=_add_mys_challenge_headers(headers, "", body))
            resp.raise_for_status()
            raw = _as_dict(resp.json())
        _check_retcode(self.source_name, raw)
        return raw

    async def fetch(self, uid: str) -> PanelResult:
        if self.game == "sr":
            raise PanelSourceError(self.source_name, "星铁米游社面板源暂未适配，请使用 auto/miao/mihomo/avocado/enkahsr")

        cached = get_cached_panel(_cache_key(self.source_name, self.game), uid)
        if cached:
            return cached

        base_url = _strip_url(MiaoConfig.get_config("MysApiBaseUrl").data) or MYS_API_BASE_URL
        cookie = self.cookie or str(MiaoConfig.get_config("MysCookie").data or "").strip()
        if not cookie:
            raise PanelSourceError(self.source_name, "米游社 Cookie 未配置")

        try:
            result = await self._fetch_with_gscore_api(uid, cookie)
            set_cached_panel(self.source_name, uid, result)
            return result
        except PanelSourceError:
            raise
        except Exception as e:
            raise PanelSourceError(self.source_name, f"米游社请求失败：{e}") from e

        server = _server_id(uid)
        index_params = {"role_id": uid, "server": server}
        index_q = urlencode(index_params)
        index_url = urljoin(f"{base_url}/", "game_record/app/genshin/api/index")
        try:
            async with httpx.AsyncClient(timeout=_timeout()) as client:
                index_raw = await self._get_json_with_retry(
                    client,
                    index_url,
                    index_params,
                    _mys_headers(cookie, index_q),
                    index_q,
                )

                index_data = index_raw.get("data") if isinstance(index_raw.get("data"), dict) else {}
                avatars = index_data.get("avatars") if isinstance(index_data, dict) else []
                character_ids = [x.get("id") for x in avatars if isinstance(x, dict) and x.get("id")]
                detail_raw: Dict[str, Any] = {}
                if character_ids:
                    detail_body = {"character_ids": character_ids, "role_id": uid, "server": server}
                    detail_url = urljoin(f"{base_url}/", "game_record/app/genshin/api/character/list")
                    detail_raw = await self._post_json_with_retry(
                        client,
                        detail_url,
                        detail_body,
                        _mys_headers(cookie, "", detail_body),
                    )

                raw = {"index": index_raw, "detail": detail_raw}
        except httpx.HTTPStatusError as e:
            raise PanelSourceError(self.source_name, _http_error_message(self.source_name, e)) from e
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
            characters=_characters_from_mys_avatars(data.get("avatars") or [], "gs"),
            game="gs",
        )
        set_cached_panel(self.source_name, uid, result)
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
