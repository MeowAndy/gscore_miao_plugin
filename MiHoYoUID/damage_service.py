from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .alias_data import resolve_alias
from .panel_models import PanelResult
from .panel_renderer import CHARACTER_ID_NAMES


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_num(props: Dict[str, Any], keys: Tuple[str, ...], default: float = 0.0) -> float:
    for key in keys:
        if key in props and props[key] not in (None, ""):
            return _num(props[key], default)
    return default


def _pct(value: float) -> float:
    return value / 100 if abs(value) > 1 else value


def _talent_level(char: Dict[str, Any], idx: int, default: int = 9) -> int:
    skills = char.get("skill_levels") or []
    try:
        return int(skills[idx] or default)
    except (IndexError, TypeError, ValueError):
        return default


def _pct_attr(props: Dict[str, Any], keys: Tuple[str, ...], default: float = 0.0) -> float:
    return _pct(_first_num(props, keys, default))


def _text_blob(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{k} {_text_blob(v)}" for k, v in value.items())
    if isinstance(value, list):
        return " ".join(_text_blob(v) for v in value)
    return str(value or "")


def _weapon_name(char: Dict[str, Any]) -> str:
    weapon = char.get("weapon") or {}
    if isinstance(weapon, dict):
        return str(weapon.get("name") or weapon.get("weapon_name") or weapon.get("light_cone") or weapon.get("title") or "")
    return str(weapon or "")


def _set_names(char: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for rel in char.get("reliquaries") or []:
        if not isinstance(rel, dict):
            continue
        text = str(rel.get("set_name") or rel.get("setName") or rel.get("suit") or rel.get("name") or "")
        if text:
            names.append(text)
    return names


def _count_text(texts: List[str], keyword: str) -> int:
    return sum(1 for text in texts if keyword and keyword in text)


def _parse_damage_query(text: str, game: str = "gs") -> Tuple[str, Dict[str, float | str | List[str]]]:
    raw = (text or "").strip()
    ctx: Dict[str, float | str | List[str]] = {
        "enemy_level": 95 if game == "sr" else 90,
        "res": 0.10,
        "def_ignore": 0.0,
        "def_reduce": 0.0,
        "vulnerability": 0.0,
        "team_bonus": 0.0,
        "team_atk": 0.0,
        "team_hp": 0.0,
        "team_def": 0.0,
        "team_cpct": 0.0,
        "team_cdmg": 0.0,
        "break_bonus": 0.0,
        "reaction": "auto",
        "tags": [],
    }
    tags: List[str] = []
    level_match = re.search(r"(?:(?:敌人|怪物)\s*)?(?:等级|Lv|lv|LV)\s*(\d{2,3})(?=\s|$|级)|(?:敌人|怪物)\s*(\d{2,3})(?=\s|$|级)", raw)
    if level_match:
        ctx["enemy_level"] = float(level_match.group(1) or level_match.group(2))
        raw = raw.replace(level_match.group(0), " ")
        tags.append(f"敌人Lv.{int(ctx['enemy_level'])}")
    res_match = re.search(r"(?:抗性|抗)\s*(-?\d+(?:\.\d+)?)%?", raw)
    if res_match:
        ctx["res"] = _pct(float(res_match.group(1)))
        raw = raw.replace(res_match.group(0), " ")
        tags.append(f"抗性{float(ctx['res']) * 100:.0f}%")
    if any(x in raw for x in ("万班", "万达", "万叶", "班尼特", "班爷")):
        ctx["team_bonus"] = float(ctx["team_bonus"]) + (0.35 if game != "sr" else 0)
        ctx["team_atk"] = float(ctx["team_atk"]) + (900 if "班" in raw else 0)
        tags.append("组队Buff：万叶/班尼特")
    if any(x in raw for x in ("夜芙", "双水", "芙宁娜", "水神")):
        ctx["team_hp"] = float(ctx["team_hp"]) + 0.25
        ctx["team_bonus"] = float(ctx["team_bonus"]) + 0.35
        tags.append("组队Buff：双水/芙宁娜")
    if any(x in raw for x in ("钟离", "减抗")):
        ctx["res"] = max(float(ctx["res"]) - 0.20, -1.0)
        tags.append("组队Buff：钟离减抗")
    if game == "sr" and any(x in raw for x in ("阮梅", "同谐主", "击破队", "超击破")):
        ctx["break_bonus"] = float(ctx["break_bonus"]) + 0.50
        ctx["team_bonus"] = float(ctx["team_bonus"]) + 0.24
        tags.append("组队Buff：阮梅/同谐主")
    if game == "sr" and any(x in raw for x in ("花火", "布洛妮娅", "知更鸟", "停云")):
        ctx["team_atk"] = float(ctx["team_atk"]) + 0.35
        ctx["team_cdmg"] = float(ctx["team_cdmg"]) + 0.45
        ctx["team_bonus"] = float(ctx["team_bonus"]) + 0.24
        tags.append("组队Buff：同谐增益")
    for token in ("蒸发", "融化", "激化", "超激化", "蔓激化", "扩散", "直伤", "无反应"):
        if token in raw:
            ctx["reaction"] = token
            raw = raw.replace(token, " ")
            tags.append(f"反应：{token}")
    for token in ("万班", "万达", "万叶", "班尼特", "班爷", "夜芙", "双水", "芙宁娜", "水神", "钟离", "减抗", "阮梅", "同谐主", "击破队", "超击破", "花火", "布洛妮娅", "知更鸟", "停云"):
        raw = raw.replace(token, " ")
    raw = re.sub(r"\s+", " ", raw).strip()
    ctx["tags"] = tags
    return raw, ctx


def _reaction_mul(reaction: str, default: float = 1.0) -> float:
    if reaction in {"蒸发", "融化"}:
        return 1.5
    if reaction in {"激化", "超激化", "蔓激化"}:
        return 1.25
    if reaction in {"直伤", "无反应"}:
        return 1.0
    return default


def _enemy_factor(char: Dict[str, Any], ctx: Dict[str, float | str | List[str]], *, extra_def_ignore: float = 0.0, extra_res_down: float = 0.0) -> float:
    char_level = min(max(_num(char.get("level"), 90), 1), 90)
    enemy_level = min(max(float(ctx.get("enemy_level") or (95 if char.get("game") == "sr" else 90)), 1), 120)
    ignore = min(max(float(ctx.get("def_ignore") or 0) + extra_def_ignore, 0), 0.95)
    reduce = min(max(float(ctx.get("def_reduce") or 0), 0), 0.95)
    defense_factor = (char_level + 100) / ((char_level + 100) + (enemy_level + 100) * (1 - ignore) * (1 - reduce))
    res = float(ctx.get("res") or 0.10) - extra_res_down
    if res < 0:
        res_factor = 1 - res / 2
    elif res < 0.75:
        res_factor = 1 - res
    else:
        res_factor = 1 / (4 * res + 1)
    vul = 1 + max(float(ctx.get("vulnerability") or 0), 0)
    return defense_factor * res_factor * vul


def _gear_modifiers(char: Dict[str, Any], game: str = "gs") -> Tuple[Dict[str, float], List[str]]:
    mods = {"bonus": 0.0, "cpct": 0.0, "cdmg": 0.0, "atk": 0.0, "hp": 0.0, "def": 0.0, "break": 0.0, "def_ignore": 0.0, "res_down": 0.0}
    notes: List[str] = []
    weapon = _weapon_name(char)
    sets = _set_names(char)
    blob = weapon + " " + " ".join(sets)
    if game != "sr":
        if any(x in weapon for x in ("薙草", "稻光")):
            mods["atk"] += 0.28
            notes.append("武器：薙草按充能转攻击简化计算")
        if "护摩" in weapon:
            mods["hp"] += 0.20
            mods["atk"] += 0.18
            notes.append("武器：护摩按半血攻击收益计算")
        if any(x in weapon for x in ("若水", "最初的大魔术", "赤月", "赤沙")):
            mods["bonus"] += 0.20
            notes.append("武器：五星专武增伤/收益已折算")
        if any(x in weapon for x in ("万世流涌", "流涌")):
            mods["hp"] += 0.16
            mods["bonus"] += 0.14
            notes.append("武器：万世流涌按生命与重击收益折算")
        if _count_text(sets, "绝缘") >= 4:
            recharge = _first_num(char.get("fight_props") or {}, ("充能效率", "元素充能", "recharge", "energy_recharge"), 100)
            mods["bonus"] += min(max(recharge, 100) * 0.0025, 0.75)
            notes.append("套装：绝缘4按充能转爆发增伤")
        if any(_count_text(sets, x) >= 4 for x in ("逐影", "猎人")):
            mods["cpct"] += 0.36
            notes.append("套装：逐影猎人4默认叠满36%暴击")
        if any(_count_text(sets, x) >= 4 for x in ("魔女", "渡火")):
            mods["bonus"] += 0.30
            notes.append("套装：火伤/反应套收益已折算")
    else:
        if any(x in weapon for x in ("沿途", "行于流逝", "专武", "只需等待", "烦恼着")):
            mods["bonus"] += 0.24
            notes.append("光锥：专武类增伤按常驻收益折算")
        if any(x in weapon for x in ("梦应归于何处", "梦应", "记一位星神")):
            mods["break"] += 0.36
            notes.append("光锥：击破/超击破收益已折算")
        if any(x in weapon for x in ("转瞬即燃", "偏偏希望无价", "拂晓之前")):
            mods["cdmg"] += 0.36
            notes.append("光锥：暴伤/追加收益已折算")
        if any(x in blob for x in ("死水", "大公", "毁烬", "繁星", "停转", "萨尔索图")):
            mods["bonus"] += 0.18
            notes.append("遗器：主流输出套装按触发后收益折算")
        if any(x in blob for x in ("铁骑", "盗匪", "机心")):
            mods["break"] += 0.32
            mods["def_ignore"] += 0.10
            notes.append("遗器：击破套按破韧/超击破收益折算")
    return mods, notes[:3]


def _base_damage(char: Dict[str, Any], scale: float, *, base_key: str = "atk", react: float = 1.0, extra_bonus: float = 0.0, extra_cdmg: float = 0.0, extra_cpct: float = 0.0, break_mul: float = 1.0, ctx: Dict[str, float | str | List[str]] | None = None, extra_def_ignore: float = 0.0, extra_res_down: float = 0.0) -> Tuple[float, float]:
    props = char.get("fight_props") or {}
    atk = _first_num(props, ("攻击力", "ATK", "atk", "attack"), 1000)
    hp = _first_num(props, ("生命值", "HP", "hp", "max_hp", "maxHp"), 0)
    defense = _first_num(props, ("防御力", "DEF", "def", "defense"), 0)
    ctx = ctx or {}
    gear, _ = _gear_modifiers(char, "sr" if char.get("game") == "sr" else "gs")
    team_atk = float(ctx.get("team_atk") or 0)
    atk_pct = 0.0 if team_atk > 2 else team_atk
    atk_flat = team_atk if team_atk > 2 else 0.0
    atk = atk * (1 + gear["atk"] + atk_pct) + atk_flat
    hp = hp * (1 + gear["hp"] + float(ctx.get("team_hp") or 0))
    defense = defense * (1 + gear["def"] + float(ctx.get("team_def") or 0))
    base = {"hp": hp, "def": defense, "atk": atk}.get(base_key, atk)
    crit = min(max(_pct_attr(props, ("暴击率", "cpct", "crit_rate", "critRate"), 5) + extra_cpct + gear["cpct"] + float(ctx.get("team_cpct") or 0), 0), 1)
    cdmg = max(_pct_attr(props, ("暴击伤害", "cdmg", "crit_dmg", "critDamage"), 50) + extra_cdmg + gear["cdmg"] + float(ctx.get("team_cdmg") or 0), 0)
    dmg_bonus = max(_pct_attr(props, ("伤害加成", "元素伤害加成", "dmg", "damage", "element_dmg"), 0) + extra_bonus + gear["bonus"] + float(ctx.get("team_bonus") or 0), 0)
    enemy = _enemy_factor(char, ctx, extra_def_ignore=extra_def_ignore + gear["def_ignore"], extra_res_down=extra_res_down + gear["res_down"])
    break_mul = break_mul * (1 + gear["break"] + float(ctx.get("break_bonus") or 0))
    no_crit = base * scale * (1 + dmg_bonus) * react * break_mul * enemy
    return no_crit * (1 + cdmg), no_crit * (1 + crit * cdmg)


def _fmt_damage(title: str, dmg: float, avg: float) -> Dict[str, float | str]:
    return {"title": title, "dmg": round(dmg), "avg": round(avg)}


def _char_damage_details(char: Dict[str, Any], game: str, ctx: Dict[str, float | str | List[str]] | None = None) -> Tuple[str, List[Dict[str, float | str]], List[str]]:
    name = _char_name_for_game(char, game)
    props = char.get("fight_props") or {}
    cons = int(_num(char.get("constellation"), 0))
    a_lv = _talent_level(char, 0)
    e_lv = _talent_level(char, 1)
    q_lv = _talent_level(char, 2)
    ctx = ctx or {"enemy_level": 95 if game == "sr" else 90, "res": 0.10, "tags": []}
    _, gear_notes = _gear_modifiers(char, game)
    notes: List[str] = [f"敌人Lv.{int(float(ctx.get('enemy_level') or 90))} · 抗性{float(ctx.get('res') or 0.1) * 100:.0f}% · 防御/抗性区已计入"]
    notes.extend(str(x) for x in (ctx.get("tags") or [])[:3])
    notes.extend(gear_notes)

    if game != "sr" and "胡桃" in name:
        hp = _first_num(props, ("生命值", "HP", "hp", "max_hp", "maxHp"), 0)
        atk = _first_num(props, ("攻击力", "ATK", "atk", "attack"), 1000)
        atk_plus = min(hp * (0.0384 + e_lv * 0.0022), atk * 4)
        tmp = dict(char)
        tmp["fight_props"] = dict(props, 攻击力=atk + atk_plus)
        notes.extend(["蝶引来生：按开E攻击力加成计算", "半血被动：默认获得33%火伤", "蒸发：重击蒸发按 miao-plugin 默认项展示"])
        ca_scale = 1.36 + a_lv * 0.126
        q_scale = 3.03 + q_lv * 0.29
        reaction = _reaction_mul(str(ctx.get("reaction") or "auto"), 1.5)
        d1, a1 = _base_damage(tmp, ca_scale, extra_bonus=0.33, ctx=ctx)
        d2, a2 = _base_damage(tmp, ca_scale, react=reaction, extra_bonus=0.33, ctx=ctx)
        d3, a3 = _base_damage(tmp, q_scale, extra_bonus=0.33, ctx=ctx)
        return "喵喵·胡桃半血开E模板", [_fmt_damage("半血开E重击", d1, a1), _fmt_damage("半血开E重击蒸发", d2, a2), _fmt_damage("半血开E后Q", d3, a3)], notes

    if game != "sr" and "那维莱特" in name:
        hp = _first_num(props, ("生命值", "HP", "hp", "max_hp", "maxHp"), 0)
        tmp = dict(char)
        tmp["fight_props"] = dict(props, 生命值=hp * 1.25)
        a2_multi = 1.6 if cons >= 1 else 1.25
        extra_cdmg = 0.42 if cons >= 2 else 0
        notes.extend(["古海孑遗：0命按两层125%，1命以上按三层160%", "至高仲裁：默认30%水伤", "双水：默认25%生命"])
        if cons >= 6:
            notes.append("6命：满水滴一轮重击加入额外生命倍率")
        ca = a2_multi * (0.072 + a_lv * 0.0068) * (30 if cons >= 6 else 8)
        if cons >= 6:
            ca += 1.2
        e = 0.128 + e_lv * 0.012
        q = 0.224 + q_lv * 0.021
        rows = []
        for title, scale in (("重击伤害", a2_multi * (0.072 + a_lv * 0.0068)), ("E伤害", e), ("Q释放伤害", q), ("满水滴一轮重击总伤害", ca)):
            d, a = _base_damage(tmp, scale, base_key="hp", extra_bonus=0.30, extra_cdmg=extra_cdmg, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·那维莱特生命重击模板", rows, notes

    if game != "sr" and ("雷电" in name or "雷神" in name):
        recharge = _first_num(props, ("充能效率", "元素充能", "recharge", "energy_recharge"), 100)
        extra_bonus = max(recharge - 100, 0) * 0.004
        extra_ignore = 1.18 if cons >= 2 else 1.0
        notes.extend(["恶曜开眼：默认开E后计算元素爆发伤害", "梦想真说：按满愿力60层计算", "被动：基于元素充能折算雷伤"])
        if cons >= 2:
            notes.append("2命：大招无视防御，折算为伤害提升")
        first = (4.01 + q_lv * 0.37 + 0.06 * 60) * extra_ignore
        ca = (1.10 + q_lv * 0.10 + 0.012 * 60) * extra_ignore
        rows = []
        for title, scale in (("零愿力Q首刀", 4.01 + q_lv * 0.37), ("满愿力Q首刀", first), ("满愿力Q后重击", ca)):
            d, a = _base_damage(char, scale, extra_bonus=extra_bonus, ctx=ctx, extra_def_ignore=0.18 if cons >= 2 else 0)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·雷电将军满愿力模板", rows, notes

    if game != "sr" and "夜兰" in name:
        hp = _first_num(props, ("生命值", "HP", "hp", "max_hp", "maxHp"), 0)
        tmp = dict(char)
        tmp["fight_props"] = dict(props, 生命值=hp * 1.25)
        notes.extend(["玄掷玲珑：默认后台协同三箭", "双水：默认25%生命", "若水/绝缘会自动折算到增伤区"])
        rows = []
        for title, scale in (("E命中伤害", 0.25 + e_lv * 0.025), ("Q首段伤害", 0.13 + q_lv * 0.012), ("协同攻击三箭", (0.087 + q_lv * 0.008) * 3)):
            d, a = _base_damage(tmp, scale, base_key="hp", extra_bonus=0.30, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·夜兰后台协同模板", rows, notes

    if game != "sr" and "芙宁娜" in name:
        hp = _first_num(props, ("生命值", "HP", "hp", "max_hp", "maxHp"), 0)
        tmp = dict(char)
        tmp["fight_props"] = dict(props, 生命值=hp * 1.25)
        fanfare = 0.75 if cons >= 1 else 0.55
        notes.extend(["孤心沙龙：默认三成员持续攻击", "气氛值：按常用中高层数折算增伤", "双水：默认25%生命"])
        rows = []
        for title, scale in (("沙龙成员·夫人", 0.145 + e_lv * 0.014), ("沙龙成员·骑士", 0.075 + e_lv * 0.007), ("沙龙成员·螃蟹", 0.205 + e_lv * 0.019)):
            d, a = _base_damage(tmp, scale, base_key="hp", extra_bonus=fanfare, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·芙宁娜沙龙模板", rows, notes

    if game != "sr" and ("阿蕾奇诺" in name or "仆人" in name):
        bond = 1.45 if cons >= 1 else 1.20
        notes.extend(["生命之契：默认高契约普攻循环", "血偿勒令：按回收后输出窗口计算", "蒸发参数可用“蒸发/万班”指令追加"])
        react = _reaction_mul(str(ctx.get("reaction") or "auto"), 1.0)
        rows = []
        for title, scale in (("强化普攻一段", (0.92 + a_lv * 0.086) * bond), ("强化普攻循环", (0.92 + a_lv * 0.086) * bond * 5.2), ("元素爆发", 3.7 + q_lv * 0.34)):
            d, a = _base_damage(char, scale, react=react, extra_bonus=0.18, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·阿蕾奇诺生命之契模板", rows, notes

    if game != "sr" and "玛薇卡" in name:
        notes.extend(["战意：默认满战意骑乘爆发", "夜魂：按持续输出状态折算", "蒸发/融化可在指令中追加"])
        react = _reaction_mul(str(ctx.get("reaction") or "auto"), 1.0)
        rows = []
        for title, scale in (("夜魂战技斩击", 1.4 + e_lv * 0.13), ("满战意爆发首段", 6.0 + q_lv * 0.55), ("骑乘普攻循环", 1.15 + a_lv * 0.11)):
            d, a = _base_damage(char, scale, react=react, extra_bonus=0.35, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·玛薇卡满战意模板", rows, notes

    if game == "sr" and "黄泉" in name:
        extra_bonus = 0.90
        extra_cpct = 0.18 if cons >= 1 else 0
        extra_mul = 1.6
        extra_kx = 1.2 if cons >= 6 else 1.0
        notes.extend(["行迹-奈落：普攻、战技、终结技按160%独立倍率", "行迹-雷心：默认90%增伤并按终结技对单模板", "终结技：默认敌方全抗降低"])
        if cons >= 1:
            notes.append("1魂：负面状态敌人暴击率提高18%")
        if cons >= 6:
            notes.append("6魂：终结技全属性抗性穿透，并使普攻/战技视为终结技")
        rows = []
        for title, scale in (("普攻伤害", 1.0 + a_lv * 0.10), ("战技伤害·主目标", 1.6 + e_lv * 0.16), ("终结技伤害·对单", 3.7 + q_lv * 0.36 + 1.5)):
            d, a = _base_damage(char, scale * extra_mul * extra_kx, extra_bonus=extra_bonus, extra_cpct=extra_cpct, ctx=ctx, extra_res_down=0.20 if cons >= 6 else 0.10)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·黄泉终结技模板", rows, notes

    if game == "sr" and "流萤" in name:
        stance = _first_num(props, ("击破特攻", "stance", "break_effect", "breakEffect"), 0)
        break_bonus = 1 + max(stance, 0) / 180
        atk = _first_num(props, ("攻击力", "ATK", "atk", "attack"), 1000)
        stance_gain = max(atk - 1800, 0) / 10 * 0.008
        notes.extend(["终结技：默认完全燃烧状态，强化战技计算", "过载核心：按攻击力折算击破特攻", "破韧后：叠加超击破伤害"])
        if cons >= 1:
            notes.append("1魂：强化战技无视目标防御，折算为伤害提升")
        scale = 1.8 + e_lv * 0.18 + min(stance * 0.002, 0.72) + stance_gain
        ignore = 1.12 if cons >= 1 else 1.0
        rows = []
        for title, mul in (("强化战技伤害", 1.0), ("破韧后战技主目标伤害", break_bonus), ("破韧后战技副目标伤害", break_bonus * 0.56)):
            d, a = _base_damage(char, scale * mul * ignore, break_mul=1 + max(stance, 0) / 500, ctx=ctx, extra_def_ignore=0.15 if cons >= 1 else 0)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·流萤超击破模板", rows, notes

    if game == "sr" and "镜流" in name:
        extra_cpct = 0.50
        extra_cdmg = (0.24 if cons >= 1 else 0) + (0.50 if cons >= 6 else 0)
        extra_bonus = 0.20 + (0.80 if cons >= 2 else 0)
        atk = _first_num(props, ("攻击力", "ATK", "atk", "attack"), 1000)
        tmp = dict(char)
        tmp["fight_props"] = dict(props, 攻击力=atk * (1.35 if cons < 4 else 1.65))
        notes.extend(["澹月转魄：默认转魄状态，加入暴击率和攻击力提升", "霜魄：转魄状态终结技增伤20%"])
        if cons >= 1:
            notes.append("1魂：强化战技/终结技暴伤提高24%")
        if cons >= 2:
            notes.append("2魂：终结技后强化战技增伤80%")
        rows = []
        for title, scale in (("普攻伤害", 1.0 + a_lv * 0.09), ("战技伤害", 2.0 + e_lv * 0.20), ("转魄状态·战技伤害(扩散)", 3.0 + e_lv * 0.30), ("转魄状态·终结技伤害(扩散)", 4.0 + q_lv * 0.38)):
            bonus = extra_bonus if "转魄" in title or "终结技" in title else 0
            d, a = _base_damage(tmp, scale, extra_bonus=bonus, extra_cpct=extra_cpct, extra_cdmg=extra_cdmg, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·镜流转魄模板", rows, notes

    if game == "sr" and "飞霄" in name:
        notes.extend(["终结技：默认叠满飞黄并按单体核爆", "追加攻击：默认触发追击增伤", "知更鸟/花火等同谐可在指令中追加"])
        rows = []
        for title, scale in (("战技伤害", 1.5 + e_lv * 0.15), ("天赋追击", 1.1 + a_lv * 0.11), ("终结技·斩击总伤", 5.2 + q_lv * 0.48)):
            d, a = _base_damage(char, scale, extra_bonus=0.42, extra_cpct=0.12, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·飞霄追击终结技模板", rows, notes

    if game == "sr" and "砂金" in name:
        defense = _first_num(props, ("防御力", "DEF", "def", "defense"), 0)
        tmp = dict(char)
        tmp["fight_props"] = dict(props, 防御力=defense * 1.24)
        notes.extend(["防御转暴击：按4000防御收益折算", "追加攻击：默认盲注叠满触发", "终结技易伤按单体目标折算"])
        rows = []
        for title, scale in (("普攻伤害", 0.75 + a_lv * 0.07), ("追加攻击七段", 1.75 + e_lv * 0.16), ("终结技伤害", 2.7 + q_lv * 0.25)):
            d, a = _base_damage(tmp, scale, base_key="def", extra_bonus=0.24, extra_cpct=0.24, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·砂金防御追击模板", rows, notes

    if game == "sr" and ("饮月" in name or "丹恒" in name):
        notes.extend(["强化普攻：默认饮月三段强化", "逆鳞：按常规三豆循环", "虚数弱点默认10%抗性"])
        rows = []
        for title, scale in (("强化普攻·跃动", 2.6 + a_lv * 0.25), ("强化普攻·盘拏耀跃", 5.0 + a_lv * 0.46), ("终结技伤害", 3.0 + q_lv * 0.28)):
            d, a = _base_damage(char, scale, extra_bonus=0.32, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·饮月三豆强化普攻模板", rows, notes

    if game == "sr" and "波提欧" in name:
        stance = _first_num(props, ("击破特攻", "stance", "break_effect", "breakEffect"), 0)
        notes.extend(["优势口袋：默认三层并锁定弱点击破", "击破伤害：按击破特攻与超击破折算", "阮梅/同谐主可在指令中追加"])
        rows = []
        for title, scale in (("强化普攻直伤", 1.8 + a_lv * 0.16), ("物理击破伤害", 2.2 + stance / 120), ("优势口袋总伤", 3.4 + stance / 90)):
            d, a = _base_damage(char, scale, extra_bonus=0.20, break_mul=1 + stance / 360, ctx=ctx)
            rows.append(_fmt_damage(title, d, a))
        return "喵喵·波提欧击破模板", rows, notes

    dmg = estimate_character_damage(char)
    burst_name = "终结技" if game == "sr" else "爆发"
    return "MiHoYoUID 通用伤害模板", [
        _fmt_damage("普攻伤害", dmg["normal"], dmg["normal"]),
        _fmt_damage("战技伤害", dmg["skill"], dmg["skill"]),
        _fmt_damage(f"{burst_name}伤害", dmg["burst"], dmg["burst"]),
    ], notes + [f"核心属性：{dmg.get('core_type', '攻击')}；该角色暂未接入独立 calc.js 规则"]


def _core_scaling(char: Dict[str, Any]) -> Tuple[str, float]:
    props = char.get("fight_props") or {}
    atk = _first_num(props, ("攻击力", "ATK", "atk", "attack"), 1000)
    hp = _first_num(props, ("生命值", "HP", "hp", "max_hp", "maxHp"), 0)
    defense = _first_num(props, ("防御力", "DEF", "def", "defense"), 0)
    name = _char_name_for_game(char, char.get("game", "gs"))
    hp_chars = ("夜兰", "芙宁娜", "那维莱特", "妮露", "心海", "胡桃", "白露", "符玄", "藿藿", "刃")
    def_chars = ("荒泷一斗", "阿贝多", "诺艾尔", "云堇", "砂金", "杰帕德", "三月七")
    if any(x in name for x in hp_chars) and hp > 0:
        return "生命", hp * 0.072 + atk * 0.45
    if any(x in name for x in def_chars) and defense > 0:
        return "防御", defense * 0.92 + atk * 0.35
    return "攻击", atk


def estimate_character_damage(char: Dict[str, Any]) -> Dict[str, float]:
    props = char.get("fight_props") or {}
    game = "sr" if char.get("game") in {"sr", "starrail", "hkrpg"} else "gs"
    core_type, core = _core_scaling(char)
    crit = _pct(_first_num(props, ("暴击率", "cpct", "crit_rate", "critRate"), 5))
    crit_dmg = _pct(_first_num(props, ("暴击伤害", "cdmg", "crit_dmg", "critDamage"), 50))
    mastery = _first_num(props, ("元素精通", "mastery", "element_mastery"), 0)
    recharge = _first_num(props, ("充能效率", "元素充能", "recharge", "energy_recharge"), 100)
    dmg_bonus = _pct(_first_num(props, ("伤害加成", "元素伤害加成", "dmg", "damage", "element_dmg"), 0))
    speed = _first_num(props, ("速度", "speed", "spd"), 100 if game == "sr" else 0)
    break_effect = _first_num(props, ("击破特攻", "stance", "break_effect", "breakEffect"), 0)
    skill_levels = char.get("skill_levels") or []
    talent_factor = 1 + sum(_num(x, 1) for x in skill_levels[:3]) / (34 if game == "sr" else 30)
    crit_expect = 1 + min(max(crit, 0), 1) * max(crit_dmg, 0)
    reaction_bonus = 1 + mastery / (mastery + 1400) * 2.78 if mastery > 0 else 1
    recharge_bonus = 1 + max(recharge - 100, 0) / (900 if game == "sr" else 1000)
    bonus_factor = 1 + max(dmg_bonus, 0)
    speed_factor = 1 + max(speed - 100, 0) / 520 if game == "sr" else 1
    break_bonus = 1 + max(break_effect, 0) / 500 if game == "sr" else 1
    name = _char_name_for_game(char, game)
    burst_bias = 1.0
    if any(x in name for x in ("雷电", "雷神", "优菈", "神里绫华", "黄泉", "景元", "银枝", "镜流", "黑天鹅")):
        burst_bias = 1.22
    if any(x in name for x in ("流萤", "波提欧", "乱破", "雪衣")):
        break_bonus *= 1.35
    normal = core * 1.08 * talent_factor * crit_expect * bonus_factor * speed_factor
    skill = core * 2.25 * talent_factor * crit_expect * reaction_bonus * bonus_factor * speed_factor
    burst = core * 3.85 * talent_factor * crit_expect * reaction_bonus * recharge_bonus * bonus_factor * speed_factor * break_bonus * burst_bias
    return {
        "normal": round(normal),
        "skill": round(skill),
        "burst": round(burst),
        "expect": round((normal + skill + burst) / 3),
        "core": round(core),
        "core_type": core_type,
    }


def _char_name(char: Dict[str, Any]) -> str:
    avatar_id = char.get("avatar_id") or char.get("avatarId")
    try:
        mapped = CHARACTER_ID_NAMES.get(int(avatar_id))
    except (TypeError, ValueError):
        mapped = None
    if mapped:
        return mapped
    name = str(char.get("name") or char.get("avatar_name") or "").strip()
    return resolve_alias(name) or name or f"角色ID {avatar_id or '?'}"


def _char_name_for_game(char: Dict[str, Any], game: str = "gs") -> str:
    if game != "sr":
        return _char_name(char)
    name = str(char.get("name") or char.get("avatar_name") or "").strip()
    avatar_id = char.get("avatar_id") or char.get("avatarId")
    return resolve_alias(name, game="sr") or name or f"角色ID {avatar_id or '?'}"


def _char_match_text(char: Dict[str, Any]) -> str:
    return " ".join([
        _char_name(char),
        str(char.get("name") or ""),
        str(char.get("avatar_name") or ""),
        str(char.get("avatar_id") or char.get("avatarId") or ""),
    ]).lower()


def _char_match_text_for_game(char: Dict[str, Any], game: str = "gs") -> str:
    return " ".join([
        _char_name_for_game(char, game),
        str(char.get("name") or ""),
        str(char.get("avatar_name") or ""),
        str(char.get("avatar_id") or char.get("avatarId") or ""),
    ]).lower()


def collect_damage_rows(result: PanelResult, character_query: str = "") -> Tuple[List[Dict[str, Any]], str]:
    characters: List[Dict[str, Any]] = result.characters or []
    parsed_query, ctx = _parse_damage_query(character_query, result.game)
    character_query = parsed_query
    if character_query:
        q = character_query.strip().lower()
        resolved = (resolve_alias(character_query, game=result.game) or character_query).strip().lower()
        matched = [c for c in characters if q in _char_match_text_for_game(c, result.game) or resolved in _char_match_text_for_game(c, result.game)]
        if not matched:
            available = "、".join(_char_name_for_game(c, result.game) for c in characters[:8]) or "无角色"
            return [], f"未在公开面板中找到角色：{character_query}。当前可见角色：{available}"
        characters = matched
    if not characters:
        source_tip = "Mihomo/Avocado/EnkaHSR" if result.game == "sr" else "Enka"
        return [], f"当前数据源没有返回可计算的角色详情。建议使用 {source_tip} 且公开角色展柜。"
    rows: List[Dict[str, Any]] = []
    for char in characters[:8]:
        item = dict(char)
        item.setdefault("game", result.game)
        template, details, notes = _char_damage_details(item, result.game, ctx)
        rows.append({
            "name": _char_name_for_game(item, result.game),
            "template": template,
            "details": details,
            "notes": notes,
            "level": item.get("level") or "?",
            "constellation": item.get("constellation") or 0,
            "skills": item.get("skill_levels") or [],
            "context": ctx,
        })
    return rows, ""


def render_damage_text(result: PanelResult, character_query: str = "") -> str:
    is_sr = result.game == "sr"
    title = "【喵喵崩铁伤害估算】" if is_sr else "【喵喵原神伤害估算】"
    lines = [title, f"UID：{result.uid}", f"数据源：{result.source}"]
    rows, error = collect_damage_rows(result, character_query)
    if error:
        lines.append(error)
        return "\n".join(lines)

    for index, row in enumerate(rows, start=1):
        details = row.get("details") or []
        notes = row.get("notes") or []
        summary = " / ".join(f"{d['title']} {int(float(d['avg']))}" for d in details[:4])
        lines.append(f"{index}. {row.get('name')}：{summary}")
        lines.append(f"   模板：{row.get('template')}")
        if notes:
            lines.append(f"   Buff：{'；'.join(notes[:3])}")
    return "\n".join(lines)