from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .alias_data import resolve_alias
from .panel_models import PanelResult
from .panel_renderer import CHARACTER_ID_NAMES

DEFAULT_WEIGHT = {"atk": 75, "cpct": 100, "cdmg": 100, "dmg": 100, "phy": 100}
DEFAULT_SR_WEIGHT = {"atk": 75, "speed": 75, "cpct": 100, "cdmg": 100, "dmg": 100, "stance": 50, "recharge": 50}

CHARACTER_WEIGHTS: Dict[str, Dict[str, float]] = {
    "芭芭拉": {"hp": 100, "atk": 50, "cpct": 50, "cdmg": 50, "dmg": 80, "recharge": 55, "heal": 100},
    "甘雨": {"atk": 75, "cpct": 100, "cdmg": 100, "mastery": 75, "dmg": 100},
    "雷电将军": {"atk": 75, "cpct": 100, "cdmg": 100, "mastery": 0, "dmg": 75, "recharge": 90},
    "八重神子": {"atk": 75, "cpct": 100, "cdmg": 100, "mastery": 75, "dmg": 75, "recharge": 55},
    "申鹤": {"atk": 100, "cpct": 50, "cdmg": 50, "dmg": 80, "recharge": 100},
    "云堇": {"atk": 75, "def": 100, "cpct": 80, "cdmg": 80, "dmg": 80, "recharge": 80},
    "荒泷一斗": {"atk": 50, "def": 100, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 30},
    "班尼特": {"hp": 100, "atk": 50, "cpct": 50, "cdmg": 50, "dmg": 80, "recharge": 100, "heal": 100},
    "枫原万叶": {"atk": 50, "cpct": 50, "cdmg": 50, "mastery": 100, "dmg": 80, "recharge": 55},
    "行秋": {"atk": 75, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 75},
    "钟离": {"hp": 100, "atk": 30, "cpct": 40, "cdmg": 40, "dmg": 80, "recharge": 55},
    "神里绫华": {"atk": 85, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 45},
    "香菱": {"atk": 75, "cpct": 100, "cdmg": 100, "mastery": 75, "dmg": 100, "recharge": 75},
    "胡桃": {"hp": 80, "atk": 50, "cpct": 100, "cdmg": 100, "mastery": 75, "dmg": 100},
    "温迪": {"atk": 75, "cpct": 100, "cdmg": 100, "mastery": 30, "dmg": 100, "recharge": 45},
    "珊瑚宫心海": {"hp": 100, "atk": 50, "mastery": 75, "dmg": 100, "recharge": 55, "heal": 100},
    "阿贝多": {"def": 75, "cpct": 100, "cdmg": 100, "dmg": 100},
    "优菈": {"atk": 75, "cpct": 100, "cdmg": 100, "dmg": 40, "phy": 100, "recharge": 55},
    "夜兰": {"hp": 80, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 55},
    "纳西妲": {"atk": 55, "cpct": 100, "cdmg": 100, "mastery": 100, "dmg": 100, "recharge": 55},
    "艾尔海森": {"atk": 55, "cpct": 100, "cdmg": 100, "mastery": 100, "dmg": 100, "recharge": 35},
    "那维莱特": {"hp": 100, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 55},
    "芙宁娜": {"hp": 100, "cpct": 100, "cdmg": 100, "dmg": 95, "recharge": 75, "heal": 95},
    "娜维娅": {"atk": 75, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 55},
    "阿蕾奇诺": {"atk": 75, "cpct": 100, "cdmg": 100, "mastery": 75, "dmg": 100, "recharge": 30},
    "玛薇卡": {"atk": 75, "cpct": 100, "cdmg": 100, "mastery": 85, "dmg": 100},
}

STAR_RAIL_CHARACTER_WEIGHTS: Dict[str, Dict[str, float]] = {
    "黄泉": {"atk": 100, "speed": 75, "cpct": 100, "cdmg": 100, "dmg": 100},
    "流萤": {"atk": 100, "speed": 100, "stance": 100, "effDef": 30},
    "卡芙卡": {"atk": 100, "speed": 100, "effPct": 75, "dmg": 100, "stance": 50},
    "黑天鹅": {"atk": 100, "speed": 75, "effPct": 100, "dmg": 100},
    "刃": {"hp": 100, "speed": 100, "cpct": 100, "cdmg": 100, "dmg": 100},
    "镜流": {"atk": 75, "speed": 100, "cpct": 100, "cdmg": 100, "dmg": 100},
    "丹恒•饮月": {"atk": 75, "speed": 50, "cpct": 100, "cdmg": 100, "dmg": 100},
    "希儿": {"atk": 75, "speed": 100, "cpct": 100, "cdmg": 100, "dmg": 100},
    "景元": {"atk": 75, "speed": 100, "cpct": 100, "cdmg": 100, "dmg": 100},
    "飞霄": {"atk": 75, "speed": 75, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 100},
    "真理医生": {"atk": 75, "speed": 100, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 50},
    "波提欧": {"speed": 100, "stance": 100, "cpct": 50, "cdmg": 50, "dmg": 50},
    "乱破": {"atk": 100, "speed": 100, "stance": 100, "effDef": 30},
    "砂金": {"def": 100, "speed": 100, "cpct": 100, "cdmg": 100, "dmg": 100, "recharge": 75, "effDef": 50},
    "符玄": {"hp": 100, "speed": 100, "cpct": 100, "cdmg": 100, "dmg": 100, "effDef": 50},
    "藿藿": {"hp": 100, "speed": 75, "heal": 100, "recharge": 100, "effDef": 50},
    "罗刹": {"atk": 100, "speed": 100, "heal": 100, "recharge": 100, "cpct": 100, "cdmg": 100},
    "灵砂": {"atk": 75, "speed": 100, "stance": 100, "heal": 100, "recharge": 100},
    "知更鸟": {"atk": 100, "speed": 100, "recharge": 100, "hp": 75, "def": 75, "effDef": 50},
    "花火": {"hp": 75, "def": 75, "speed": 100, "cdmg": 100, "recharge": 100, "effDef": 50},
    "星期日": {"hp": 75, "def": 75, "speed": 100, "cdmg": 100, "recharge": 100, "effDef": 50},
    "阮•梅": {"hp": 75, "def": 75, "speed": 100, "stance": 100, "recharge": 100, "effDef": 50},
    "银狼": {"atk": 75, "speed": 100, "cpct": 100, "cdmg": 100, "effPct": 100, "recharge": 75},
    "椒丘": {"hp": 75, "atk": 50, "def": 75, "speed": 100, "effPct": 100, "effDef": 50},
    "停云": {"atk": 100, "speed": 100, "recharge": 100, "hp": 50},
}
PROP_KEY_MAP = {
    "FIGHT_PROP_HP": "hp",
    "FIGHT_PROP_HP_PERCENT": "hp",
    "FIGHT_PROP_ATTACK": "atk",
    "FIGHT_PROP_ATTACK_PERCENT": "atk",
    "FIGHT_PROP_DEFENSE": "def",
    "FIGHT_PROP_DEFENSE_PERCENT": "def",
    "FIGHT_PROP_ELEMENT_MASTERY": "mastery",
    "FIGHT_PROP_CRITICAL": "cpct",
    "FIGHT_PROP_CRITICAL_HURT": "cdmg",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "recharge",
    "FIGHT_PROP_HEAL_ADD": "heal",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "phy",
    "FIGHT_PROP_FIRE_ADD_HURT": "dmg",
    "FIGHT_PROP_ELEC_ADD_HURT": "dmg",
    "FIGHT_PROP_WATER_ADD_HURT": "dmg",
    "FIGHT_PROP_GRASS_ADD_HURT": "dmg",
    "FIGHT_PROP_WIND_ADD_HURT": "dmg",
    "FIGHT_PROP_ROCK_ADD_HURT": "dmg",
    "FIGHT_PROP_ICE_ADD_HURT": "dmg",
    "生命值": "hp",
    "生命值%": "hp",
    "攻击力": "atk",
    "攻击力%": "atk",
    "防御力": "def",
    "防御力%": "def",
    "元素精通": "mastery",
    "暴击率": "cpct",
    "暴击伤害": "cdmg",
    "元素充能": "recharge",
    "充能效率": "recharge",
    "治疗加成": "heal",
    "物理伤害": "phy",
    "元素伤害": "dmg",
    "伤害加成": "dmg",
    "速度": "speed",
    "击破特攻": "stance",
    "击破": "stance",
    "效果命中": "effPct",
    "命中": "effPct",
    "效果抵抗": "effDef",
    "抵抗": "effDef",
    "治疗加成": "heal",
    "能量恢复效率": "recharge",
    "energy_recharge": "recharge",
    "speed": "speed",
    "spd": "speed",
    "hp": "hp",
    "atk": "atk",
    "def": "def",
    "cpct": "cpct",
    "cdmg": "cdmg",
    "heal": "heal",
    "stance": "stance",
    "effPct": "effPct",
    "effDef": "effDef",
    "recharge": "recharge",
    "crit": "cpct",
    "crit_rate": "cpct",
    "critRate": "cpct",
    "crit_damage": "cdmg",
    "crit_dmg": "cdmg",
    "critDamage": "cdmg",
    "break_effect": "stance",
    "breakEffect": "stance",
    "break_dmg": "stance",
    "breakDamage": "stance",
    "effect_hit": "effPct",
    "effectHitRate": "effPct",
    "effect_hit_rate": "effPct",
    "effect_res": "effDef",
    "effectRes": "effDef",
    "effect_resistance": "effDef",
    "dmg": "dmg",
    "damage": "dmg",
}

MAX_SUB_VALUE = {
    "hp": 5.8,
    "atk": 5.8,
    "def": 7.3,
    "cpct": 3.9,
    "cdmg": 7.8,
    "recharge": 6.5,
    "mastery": 23.3,
    "dmg": 7.0,
    "phy": 7.0,
    "heal": 5.4,
    "speed": 2.6,
    "stance": 6.48,
    "effPct": 4.32,
    "effDef": 4.32,
}

SR_MAX_SUB_VALUE = {
    "atk": 4.32,
    "atkPlus": 127 / 6,
    "def": 5.4,
    "defPlus": 127 / 6,
    "hp": 4.32,
    "hpPlus": 254 / 6,
    "speed": 2.6,
    "cpct": 3.24,
    "cdmg": 6.48,
    "recharge": 3.11,
    "dmg": 6.22,
    "heal": 5.53,
    "stance": 6.48,
    "effPct": 4.32,
    "effDef": 4.32,
}

ARTIFACT_SLOT_INDEX = {
    "EQUIP_BRACER": 1,
    "EQUIP_NECKLACE": 2,
    "EQUIP_SHOES": 3,
    "EQUIP_RING": 4,
    "EQUIP_DRESS": 5,
    "生之花": 1,
    "死之羽": 2,
    "时之沙": 3,
    "空之杯": 4,
    "理之冠": 5,
}

FLAT_PROP_MAX = {
    "FIGHT_PROP_HP": (298.75, 5.8),
    "FIGHT_PROP_ATTACK": (19.45, 5.8),
    "FIGHT_PROP_DEFENSE": (23.15, 7.3),
}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _char_name(char: Dict[str, Any]) -> str:
    avatar_id = char.get("avatar_id") or char.get("avatarId")
    try:
        id_name = CHARACTER_ID_NAMES.get(int(avatar_id))
    except (TypeError, ValueError):
        id_name = None
    if id_name:
        return id_name
    name = str(char.get("name") or char.get("avatar_name") or "").strip()
    if name and not name.isdigit():
        game = "sr" if char.get("game") in {"sr", "starrail", "hkrpg"} else "gs"
        return resolve_alias(name, game=game) or name
    return name or "未知角色"


def _weapon_name(char: Dict[str, Any]) -> str:
    weapon = char.get("weapon") or {}
    return str(weapon.get("name") or "") if isinstance(weapon, dict) else ""


def _weapon_refine(char: Dict[str, Any]) -> int:
    weapon = char.get("weapon") or {}
    return int(_as_float(weapon.get("refine"), 1)) if isinstance(weapon, dict) else 1


def _artifact_sets(char: Dict[str, Any]) -> Dict[str, int]:
    sets: Dict[str, int] = {}
    for rel in char.get("reliquaries") or []:
        if not isinstance(rel, dict):
            continue
        set_name = str(rel.get("set_name") or "")
        if set_name and not set_name.isdigit():
            sets[set_name] = sets.get(set_name, 0) + 1
    return sets


def _prop_key(prop: Any) -> str:
    text = str(prop or "").strip()
    if text in PROP_KEY_MAP:
        return PROP_KEY_MAP[text]
    if text in {"atkPlus", "defPlus", "hpPlus"}:
        return text
    lower = text.lower()
    if lower in PROP_KEY_MAP:
        return PROP_KEY_MAP[lower]
    upper = text.upper()
    if upper in PROP_KEY_MAP:
        return PROP_KEY_MAP[upper]
    if "CRIT" in upper and ("DMG" in upper or "HURT" in upper):
        return "cdmg"
    if "CRIT" in upper:
        return "cpct"
    if "RECHARGE" in upper or "CHARGE" in upper:
        return "recharge"
    if "SPEED" in upper or upper == "SPD":
        return "speed"
    if "BREAK" in upper or "STANCE" in upper:
        return "stance"
    if "EFFECT" in upper and ("HIT" in upper or "PCT" in upper):
        return "effPct"
    if "EFFECT" in upper and ("RES" in upper or "DEF" in upper):
        return "effDef"
    if "MASTERY" in upper:
        return "mastery"
    if "HP" in upper:
        return "hp"
    if "DEF" in upper:
        return "def"
    if "ATK" in upper or "ATTACK" in upper:
        return "atk"
    if "ADD_HURT" in upper or "DAMAGE" in upper:
        return "dmg"
    return ""


def _sub_value(prop: Any, max_values: Dict[str, float] | None = None) -> float:
    max_values = max_values or MAX_SUB_VALUE
    if isinstance(prop, dict):
        raw_prop_id = prop.get("appendPropId") or prop.get("prop_id") or prop.get("key") or prop.get("field") or prop.get("mainPropId") or prop.get("name") or prop.get("type") or ""
        prop_id = str(raw_prop_id).upper()
        prop_key = _prop_key(prop_id)
        for key in ("value", "val", "statValue", "base", "display", "value_str", "valueStr", "count", "cnt"):
            if key in prop:
                value = _as_float(prop.get(key), 0)
                if prop_id in FLAT_PROP_MAX:
                    flat_max, pct_max = FLAT_PROP_MAX[prop_id]
                    return value / flat_max * pct_max
                if 0 < abs(value) < 1 and prop_key not in {"speed"}:
                    value *= 100
                return value
        return max_values.get(prop_key, 2.5)
    return max_values.get(_prop_key(prop), 2.5)


def _artifact_pos_index(reliq: Dict[str, Any], fallback_idx: int = 0) -> int:
    pos = reliq.get("pos")
    if pos in ARTIFACT_SLOT_INDEX:
        return ARTIFACT_SLOT_INDEX[pos]
    try:
        num = int(pos)
        if 1 <= num <= 6:
            return num
    except (TypeError, ValueError):
        pass
    return fallback_idx + 1


def _weight_for_char(char: Dict[str, Any]) -> Tuple[str, Dict[str, float]]:
    name = _char_name(char)
    is_sr = char.get("game") in {"sr", "starrail", "hkrpg"}
    weight = dict(DEFAULT_SR_WEIGHT if is_sr else DEFAULT_WEIGHT)
    weight.update((STAR_RAIL_CHARACTER_WEIGHTS if is_sr else CHARACTER_WEIGHTS).get(name, {}))

    # 使用本插件适配后的常见动态评分规则。
    weapon_name = _weapon_name(char)
    refine = max(min(_weapon_refine(char), 5), 1)
    sets = _artifact_sets(char)
    title = f"{name}-{'星铁通用' if is_sr else '通用'}"
    if is_sr:
        return title, weight
    if name == "雷电将军" and weapon_name == "薙草之稻光" and refine >= 3:
        weight.update({"atk": 90, "cpct": 100, "cdmg": 100, "dmg": 90, "recharge": 90})
        title = "雷神-高精"
    if "绝缘之旗印" in sets and sets["绝缘之旗印"] >= 4:
        weight["recharge"] = max(weight.get("recharge", 0), max(weight.get("atk", 0), weight.get("hp", 0), weight.get("def", 0), weight.get("mastery", 0)))
        title = f"{name}-绝缘4"
    if weapon_name.startswith("西风"):
        weight["cpct"] = max(weight.get("cpct", 0), 100)
        title = f"{name}-西风"
    return title, weight


def _prop_score(prop: Any, weight: Dict[str, float], main: bool = False, max_values: Dict[str, float] | None = None) -> float:
    key = _prop_key(prop.get("appendPropId") or prop.get("prop_id") or prop.get("key") or prop.get("field") or prop.get("mainPropId") or prop.get("name") or prop.get("type") if isinstance(prop, dict) else prop)
    if not key:
        return 0.0
    max_values = max_values or MAX_SUB_VALUE
    value = _sub_value(prop, max_values)
    w = weight.get(key, 0)
    if w <= 0:
        return 0.0
    base = max_values.get(key, 5.0)
    mark = value / base * (w / 100) * 7.0
    return mark / 4 if main else mark


def score_reliquary(reliq: Dict[str, Any], weight: Dict[str, float], fallback_idx: int = 0, game: str = "gs") -> float:
    score = 0.0
    max_values = SR_MAX_SUB_VALUE if game == "sr" else MAX_SUB_VALUE
    if _artifact_pos_index(reliq, fallback_idx) >= 3:
        score += _prop_score(reliq.get("main_prop"), weight, True, max_values)
    for prop in reliq.get("sub_props") or []:
        if isinstance(prop, dict):
            score += _as_float(prop.get("score"), _prop_score(prop, weight, max_values=max_values))
        else:
            score += _prop_score(prop, weight, max_values=max_values)
    rarity = _as_float(reliq.get("rarity"), 5)
    level = _as_float(reliq.get("level"), 1)
    score *= 1 + max(rarity - 4, 0) * 0.03
    score *= min(max(level, 1), 21) / 21
    return round(min(score, 66), 1)


def character_artifact_score(char: Dict[str, Any]) -> Tuple[float, List[float], str]:
    title, weight = _weight_for_char(char)
    game = "sr" if char.get("game") in {"sr", "starrail", "hkrpg"} else "gs"
    scores = [score_reliquary(x, weight, idx, game=game) for idx, x in enumerate(char.get("reliquaries") or []) if isinstance(x, dict)]
    return round(sum(scores), 1), scores, title


def artifact_rank(score: float) -> str:
    avg = score / 5 if score > 80 else score
    if avg >= 56:
        return "MAX"
    if avg >= 49:
        return "ACE"
    if avg >= 42:
        return "SSS"
    if avg >= 35:
        return "SS"
    if avg >= 28:
        return "S"
    if avg >= 21:
        return "A"
    if avg >= 14:
        return "B"
    if avg >= 7:
        return "C"
    return "C"


def render_artifact_text(result: PanelResult, character_query: str = "") -> str:
    is_sr = result.game == "sr"
    characters = result.characters or []
    if character_query:
        q = (resolve_alias(character_query, game=result.game) or character_query).lower()
        matched = [
            c for c in characters
            if q in _char_name(c).lower()
        ]
        if not matched:
            available = "、".join(_char_name(c) for c in characters[:8]) or "无角色"
            return "\n".join([
                "【喵喵崩铁遗器评分】" if is_sr else "【喵喵原神圣遗物评分】",
                f"UID：{result.uid}",
                f"数据源：{result.source}",
                f"未在公开面板中找到角色：{character_query}。当前可见角色：{available}",
            ])
        characters = matched

    lines = ["【喵喵崩铁遗器评分】" if is_sr else "【喵喵原神圣遗物评分】", f"UID：{result.uid}", f"数据源：{result.source}"]
    if not characters:
        lines.append("当前数据源没有返回遗器详情。建议使用 miao/mihomo/avocado/enkahsr 且公开角色展柜。" if is_sr else "当前数据源没有返回圣遗物详情。建议使用 Enka 且公开角色展柜。")
        return "\n".join(lines)

    for index, char in enumerate(characters[:8], start=1):
        name = _char_name(char)
        total, scores, title = character_artifact_score(char)
        detail = " / ".join(str(x) for x in scores) if scores else "无圣遗物"
        rank_score = total / (6 if is_sr else 5) if is_sr and total > 0 else total
        lines.append(f"{index}. {name}：{total} 分 [{artifact_rank(rank_score)}] | {detail}")
        lines.append(f"   规则：{title}")
    lines.append("评分已按 miao-plugin 常用角色权重迁移；未知角色使用通用权重。")
    return "\n".join(lines)