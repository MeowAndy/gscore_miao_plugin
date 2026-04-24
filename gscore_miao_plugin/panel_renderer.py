from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from gsuid_core.utils.image.convert import convert_img
from PIL import Image, ImageDraw, ImageFont

from .config import MiaoConfig
from .panel_models import PanelResult

Color = Tuple[int, int, int]

CHARACTER_ID_NAMES: Dict[int, str] = {
    10000002: "神里绫华",
    10000003: "琴",
    10000005: "旅行者",
    10000006: "丽莎",
    10000007: "旅行者",
    10000014: "芭芭拉",
    10000015: "凯亚",
    10000016: "迪卢克",
    10000020: "雷泽",
    10000021: "安柏",
    10000022: "温迪",
    10000023: "香菱",
    10000024: "北斗",
    10000025: "行秋",
    10000026: "魈",
    10000027: "凝光",
    10000029: "可莉",
    10000030: "钟离",
    10000031: "菲谢尔",
    10000032: "班尼特",
    10000033: "达达利亚",
    10000034: "诺艾尔",
    10000035: "七七",
    10000036: "重云",
    10000037: "甘雨",
    10000038: "阿贝多",
    10000039: "迪奥娜",
    10000041: "莫娜",
    10000042: "刻晴",
    10000043: "砂糖",
    10000044: "辛焱",
    10000045: "罗莎莉亚",
    10000046: "胡桃",
    10000047: "枫原万叶",
    10000048: "烟绯",
    10000049: "宵宫",
    10000050: "托马",
    10000051: "优菈",
    10000052: "雷电将军",
    10000053: "早柚",
    10000054: "珊瑚宫心海",
    10000055: "五郎",
    10000056: "九条裟罗",
    10000057: "荒泷一斗",
    10000058: "八重神子",
    10000059: "鹿野院平藏",
    10000060: "夜兰",
    10000062: "埃洛伊",
    10000063: "申鹤",
    10000064: "云堇",
    10000065: "久岐忍",
    10000066: "神里绫人",
    10000067: "柯莱",
    10000068: "多莉",
    10000069: "提纳里",
    10000070: "妮露",
    10000071: "赛诺",
    10000072: "坎蒂丝",
    10000073: "纳西妲",
    10000074: "莱依拉",
    10000075: "流浪者",
    10000076: "珐露珊",
    10000077: "瑶瑶",
    10000078: "艾尔海森",
    10000079: "迪希雅",
    10000080: "米卡",
    10000081: "卡维",
    10000082: "白术",
    10000083: "琳妮特",
    10000084: "林尼",
    10000085: "菲米尼",
    10000086: "莱欧斯利",
    10000087: "那维莱特",
    10000088: "夏洛蒂",
    10000089: "芙宁娜",
    10000090: "夏沃蕾",
    10000091: "娜维娅",
    10000092: "嘉明",
    10000093: "闲云",
    10000094: "千织",
    10000095: "希格雯",
    10000096: "阿蕾奇诺",
    10000097: "赛索斯",
    10000098: "克洛琳德",
    10000099: "艾梅莉埃",
    10000100: "卡齐娜",
    10000101: "基尼奇",
    10000102: "玛拉妮",
    10000103: "希诺宁",
    10000104: "恰斯卡",
    10000105: "欧洛伦",
    10000106: "玛薇卡",
    10000107: "茜特菈莉",
}

ARTIFACT_SLOT_ICONS = ["花", "羽", "沙", "杯", "冠"]

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

PROP_NAME_MAP: Dict[str, str] = {
    "FIGHT_PROP_HP": "生命值",
    "FIGHT_PROP_ATTACK": "攻击力",
    "FIGHT_PROP_DEFENSE": "防御力",
    "FIGHT_PROP_HP_PERCENT": "生命值%",
    "FIGHT_PROP_ATTACK_PERCENT": "攻击力%",
    "FIGHT_PROP_DEFENSE_PERCENT": "防御力%",
    "FIGHT_PROP_ELEMENT_MASTERY": "元素精通",
    "FIGHT_PROP_CRITICAL": "暴击率",
    "FIGHT_PROP_CRITICAL_HURT": "暴击伤害",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "元素充能",
    "FIGHT_PROP_HEAL_ADD": "治疗加成",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "物理伤害",
    "FIGHT_PROP_FIRE_ADD_HURT": "火伤加成",
    "FIGHT_PROP_ELEC_ADD_HURT": "雷伤加成",
    "FIGHT_PROP_WATER_ADD_HURT": "水伤加成",
    "FIGHT_PROP_GRASS_ADD_HURT": "草伤加成",
    "FIGHT_PROP_WIND_ADD_HURT": "风伤加成",
    "FIGHT_PROP_ROCK_ADD_HURT": "岩伤加成",
    "FIGHT_PROP_ICE_ADD_HURT": "冰伤加成",
}

WEAPON_PROP_NAME_MAP: Dict[str, str] = {
    "FIGHT_PROP_BASE_ATTACK": "基础攻击",
    "FIGHT_PROP_ATTACK": "攻击",
    "FIGHT_PROP_ATTACK_PERCENT": "攻击",
    "FIGHT_PROP_HP": "生命",
    "FIGHT_PROP_HP_PERCENT": "生命",
    "FIGHT_PROP_DEFENSE": "防御",
    "FIGHT_PROP_DEFENSE_PERCENT": "防御",
    "FIGHT_PROP_ELEMENT_MASTERY": "精通",
    "FIGHT_PROP_CRITICAL": "暴击",
    "FIGHT_PROP_CRITICAL_HURT": "爆伤",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "充能",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "物伤",
    "FIGHT_PROP_FIRE_ADD_HURT": "火伤",
    "FIGHT_PROP_ELEC_ADD_HURT": "雷伤",
    "FIGHT_PROP_WATER_ADD_HURT": "水伤",
    "FIGHT_PROP_GRASS_ADD_HURT": "草伤",
    "FIGHT_PROP_WIND_ADD_HURT": "风伤",
    "FIGHT_PROP_ROCK_ADD_HURT": "岩伤",
    "FIGHT_PROP_ICE_ADD_HURT": "冰伤",
    "atkBase": "攻击",
    "atkPct": "攻击",
    "hpPct": "生命",
    "defPct": "防御",
    "mastery": "精通",
    "cpct": "暴击",
    "cdmg": "爆伤",
    "dmg": "伤害",
    "phy": "物伤",
    "recharge": "充能",
    "heal": "治疗",
    "shield": "护盾",
}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "msyhbd.ttc" if bold else "msyh.ttc",
        "Microsoft YaHei UI Bold.ttf" if bold else "Microsoft YaHei UI.ttf",
        "simhei.ttf",
        "arial.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


FONT_TITLE = _font(42, True)
FONT_SUBTITLE = _font(22)
FONT_CARD_TITLE = _font(26, True)
FONT_TEXT = _font(20)
FONT_SMALL = _font(16)
FONT_TINY = _font(14)
FONT_HELP_TITLE = _font(48, True)
FONT_HELP_GROUP = _font(28, True)
FONT_HELP_CMD = _font(22, True)
FONT_HELP_DESC = _font(16)


def _text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: Any, fill: Color, font: ImageFont.ImageFont) -> None:
    draw.text(xy, str(text), fill=fill, font=font)


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _miao_root() -> Path | None:
    configured = str(MiaoConfig.get_config("MiaoPluginResourcePath").data or "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend([
        _plugin_root().parent / "miao-plugin",
        Path("E:/gsuid_core/gsuid_core/plugins/miao-plugin"),
    ])
    for path in candidates:
        if (path / "resources").exists():
            return path
    return None


def _resource_path(*parts: str) -> Path | None:
    root = _miao_root()
    if not root:
        return None
    path = root / "resources" / Path(*parts)
    return path if path.exists() else None


def _open_image(path: Path | None, size: Tuple[int, int] | None = None, contain: bool = True) -> Image.Image | None:
    if not path or not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGBA")
        if size:
            if contain:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", size, (0, 0, 0, 0))
                canvas.alpha_composite(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
                return canvas
            return img.resize(size, Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None


def _cover_image(path: Path | None, size: Tuple[int, int]) -> Image.Image | None:
    if not path or not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGBA")
        scale = max(size[0] / img.width, size[1] / img.height)
        resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
        left = max((resized.width - size[0]) // 2, 0)
        top = max((resized.height - size[1]) // 2, 0)
        return resized.crop((left, top, left + size[0], top + size[1]))
    except Exception:
        return None


def _help_bg_path() -> Path | None:
    for path in [
        _resource_path("help", "theme", "default", "bg.jpg"),
        _resource_path("common", "theme", "bg-01.jpg"),
        Path("e:/ceshi/XutheringWavesUID/WutheringWavesUID/wutheringwaves_help/texture2d/bg.jpg"),
    ]:
        if path and path.exists():
            return path
    return None


def _paste(img: Image.Image, overlay: Image.Image | None, xy: Tuple[int, int]) -> None:
    if overlay:
        img.alpha_composite(overlay, xy)


def _load_json(path: Path | None) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=4096)
def _find_meta_by_id(base: str, item_id: str) -> Tuple[str, Dict[str, Any]]:
    if not item_id:
        return "", {}
    root = _miao_root()
    if not root:
        return "", {}
    root_dir = root / "resources" / Path(base)
    if not root_dir.exists():
        return "", {}
    target = str(item_id)
    for data_file in root_dir.rglob("data.json"):
        data = _load_json(data_file)
        if str(data.get("id") or "") == target:
            return data_file.parent.name, data
        for item in data.values():
            if not isinstance(item, dict):
                continue
            if str(item.get("id") or "") != target:
                continue
            name = str(item.get("name") or item.get("sName") or "").strip()
            merged = dict(item)
            if name:
                detail = _load_json(data_file.parent / name / "data.json")
                if detail:
                    merged = {**merged, **detail}
                return name, merged
            return data_file.parent.name, merged
    return "", {}


@lru_cache(maxsize=4096)
def _find_artifact_by_item_id(item_id: str) -> Dict[str, Any]:
    data = _load_json(_resource_path("meta-gs", "artifact", "data.json"))
    target = str(item_id or "")
    if not target:
        return {}
    targets = {target}
    if target.isdigit():
        num = int(target)
        targets.update({str(num + delta) for delta in range(-5, 6) if num + delta > 0})
    for art in data.values():
        if not isinstance(art, dict):
            continue
        idxs = art.get("idxs") or {}
        for idx, item in idxs.items():
            if isinstance(item, dict) and str(item.get("id") or "") in targets:
                return {
                    "set_name": str(art.get("name") or ""),
                    "name": str(item.get("name") or ""),
                    "idx": int(idx) if str(idx).isdigit() else 0,
                }
    return {}


def _rounded(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], fill: Color, outline: Color | None = None) -> None:
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=2 if outline else 1)


def _rounded_r(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], radius: int, fill: Color, outline: Color | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _gradient_bg(width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height), "#121826")
    px = img.load()
    for y in range(height):
        ratio = y / max(height - 1, 1)
        r = int(18 + 22 * ratio)
        g = int(24 + 18 * ratio)
        b = int(38 + 38 * ratio)
        for x in range(width):
            glow = int(18 * (x / max(width - 1, 1)))
            px[x, y] = (min(r + glow, 70), min(g + glow // 2, 70), min(b + glow, 100))
    return img


def _safe(value: Any, default: str = "-") -> str:
    if value is None or value == "":
        return default
    return str(value)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt(value: Any, suffix: str = "") -> str:
    if value is None or value == "":
        return "-"
    number = _num(value, None)  # type: ignore[arg-type]
    if number is None:
        return str(value)
    if abs(number - round(number)) < 0.01:
        return f"{round(number)}{suffix}"
    return f"{number:.1f}{suffix}"


def _stat_line(label: str, value: Any) -> str:
    return f"{label} {_safe(value)}"


def _iter_cards(characters: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for char in characters:
        if isinstance(char, dict):
            yield char


def _draw_character_card(draw: ImageDraw.ImageDraw, char: Dict[str, Any], index: int, x: int, y: int, w: int, h: int) -> None:
    rarity = 5
    weapon = char.get("weapon") or {}
    if isinstance(weapon, dict):
        rarity = int(weapon.get("rarity") or 5)
    accent = (231, 184, 99) if rarity >= 5 else (174, 133, 229)
    _rounded(draw, (x, y, x + w, y + h), (31, 39, 61), (70, 83, 120))
    draw.rounded_rectangle((x + 18, y + 18, x + 82, y + 82), radius=20, fill=accent)
    _text(draw, (x + 38, y + 32), str(index), (35, 28, 18), FONT_CARD_TITLE)

    avatar_name = _char_name(char)
    _text(draw, (x + 96, y + 18), avatar_name, (248, 244, 232), FONT_CARD_TITLE)
    cons = char.get("constellation")
    level = _safe(char.get("level"), "?")
    friendship = char.get("friendship")
    sub = f"Lv.{level}"
    if cons is not None:
        sub += f"  C{cons}"
    if friendship:
        sub += f"  好感 {friendship}"
    _text(draw, (x + 96, y + 55), sub, (190, 201, 221), FONT_SMALL)

    skill_levels = "/".join(str(v) for v in char.get("skill_levels") or []) or "-"
    reliq_count = len(char.get("reliquaries") or [])
    weapon_name = "未知武器"
    weapon_level = "?"
    if isinstance(weapon, dict):
        weapon_name = _weapon_name(weapon)
        weapon_level = _safe(weapon.get("level"), "?")

    props = char.get("fight_props") or {}
    crit = props.get("暴击率") if isinstance(props, dict) else None
    crit_dmg = props.get("暴击伤害") if isinstance(props, dict) else None
    recharge = props.get("充能效率") if isinstance(props, dict) else None
    atk = props.get("攻击力") if isinstance(props, dict) else None
    mastery = props.get("元素精通") if isinstance(props, dict) else None

    left = x + 30
    top = y + 112
    lines = [
        _stat_line("天赋", skill_levels),
        _stat_line("武器", f"{weapon_name} Lv.{weapon_level}"),
        _stat_line("圣遗物", f"{reliq_count}/5"),
        _stat_line("双暴", f"{_safe(crit)}% / {_safe(crit_dmg)}%" if crit is not None or crit_dmg is not None else "-"),
        _stat_line("充能", f"{recharge}%" if recharge is not None else "-"),
        _stat_line("攻击/精通", f"{_safe(atk)} / {_safe(mastery)}"),
    ]
    for row, line in enumerate(lines):
        col_x = left + (row % 2) * 330
        row_y = top + (row // 2) * 42
        _text(draw, (col_x, row_y), line, (220, 226, 238), FONT_TEXT)


def _char_name(char: Dict[str, Any]) -> str:
    avatar_id = char.get("avatar_id") or char.get("avatarId")
    try:
        mapped = CHARACTER_ID_NAMES.get(int(avatar_id))
    except (TypeError, ValueError):
        mapped = None
    if mapped:
        return mapped
    name = char.get("name") or char.get("avatar_name")
    if name and not str(name).isdigit():
        return str(name)
    folder, data = _find_meta_by_id("meta-gs/character", str(avatar_id or ""))
    return str(data.get("name") or folder or "未知角色")


def _char_match_text(char: Dict[str, Any]) -> str:
    parts = [
        _char_name(char),
        str(char.get("name") or ""),
        str(char.get("avatar_name") or ""),
        str(char.get("avatar_id") or char.get("avatarId") or ""),
    ]
    return " ".join(x for x in parts if x).lower()


def _char_meta(name: str) -> Dict[str, Any]:
    return _load_json(_resource_path("meta-gs", "character", name, "data.json"))


def _character_weapon_type(name: str) -> str:
    meta = _char_meta(name)
    weapon = str(meta.get("weapon") or "sword").strip().lower()
    return weapon if weapon in {"sword", "claymore", "polearm", "bow", "catalyst"} else "sword"


def _talent_icon_path(name: str, key: str) -> Path | None:
    if key == "a":
        return _resource_path("common", "item", f"atk-{_character_weapon_type(name)}.webp")

    meta = _char_meta(name)
    talent_cons = meta.get("talentCons") or {}
    cons_idx = 0
    if isinstance(talent_cons, dict):
        try:
            cons_idx = int(talent_cons.get(key) or 0)
        except (TypeError, ValueError):
            cons_idx = 0
    if cons_idx > 0:
        cons_path = _resource_path("meta-gs", "character", name, "icons", f"cons-{cons_idx}.webp")
        if cons_path:
            return cons_path
    return _resource_path("meta-gs", "character", name, "icons", f"talent-{key}.webp")


def _char_image(name: str, kind: str = "splash") -> Path | None:
    for file in (f"{kind}.webp", f"{kind}0.webp", f"{kind}.png"):
        path = _resource_path("meta-gs", "character", name, "imgs", file)
        if path:
            return path
    return None


def _find_named_resource(base: str, name: str, filename: str) -> Path | None:
    if not name or name.isdigit():
        return None
    root = _miao_root()
    if not root:
        return None
    target = str(name).strip()
    root_dir = root / "resources" / Path(base)
    if not root_dir.exists():
        return None
    direct = root_dir / target / filename
    if direct.exists():
        return direct
    for path in root_dir.rglob(filename):
        if path.parent.name == target:
            return path
    return None


def _weapon_meta(weapon: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    item_id = str(weapon.get("item_id") or weapon.get("itemId") or weapon.get("id") or "")
    return _find_meta_by_id("meta-gs/weapon", item_id)


def _weapon_name(weapon: Dict[str, Any]) -> str:
    folder, data = _weapon_meta(weapon)
    if data.get("name") or folder:
        return str(data.get("name") or folder)
    name = _display_name(weapon.get("name"), "")
    if name:
        return name
    return "未知武器"


def _weapon_icon(weapon: Dict[str, Any]) -> Path | None:
    name = _weapon_name(weapon)
    path = _find_named_resource("meta-gs/weapon", name, "icon.webp")
    if path:
        return path
    folder, _ = _weapon_meta(weapon)
    return _find_named_resource("meta-gs/weapon", folder, "icon.webp")


def _fmt_weapon_attr(key: str, value: Any) -> str:
    text = str(value)
    if text.endswith("%"):
        return text
    try:
        num = float(value)
    except (TypeError, ValueError):
        return text
    upper = key.upper()
    if abs(num) < 1 and any(x in upper for x in ["PERCENT", "CRITICAL", "HURT", "CHARGE", "DMG", "DAMAGE", "PCT"]):
        num *= 100
    suffix = "%" if any(x in upper for x in ["PERCENT", "CRITICAL", "HURT", "CHARGE", "DMG", "DAMAGE", "PCT", "CPCT", "CDMG", "RECHARGE", "HEAL", "SHIELD"]) else ""
    if abs(num - round(num)) < 0.01:
        return f"{round(num)}{suffix}"
    return f"{num:.1f}{suffix}"


def _weapon_attr_items(weapon: Dict[str, Any]) -> List[Tuple[str, str]]:
    _, data = _weapon_meta(weapon)
    attrs = weapon.get("attrs") if isinstance(weapon.get("attrs"), dict) else None
    raw_attrs = attrs or data.get("attrs") or data.get("main") or {}
    items: List[Tuple[str, str]] = []
    if isinstance(raw_attrs, dict):
        for key, value in raw_attrs.items():
            if value in (None, "", 0, "0"):
                continue
            label = WEAPON_PROP_NAME_MAP.get(str(key), PROP_NAME_MAP.get(str(key), str(key)))
            items.append((label, _fmt_weapon_attr(str(key), value)))
    elif isinstance(raw_attrs, list):
        for item in raw_attrs:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or item.get("prop") or item.get("appendPropId") or item.get("name") or "")
            value = item.get("value") or item.get("val") or item.get("statValue")
            if value in (None, "", 0, "0"):
                continue
            label = WEAPON_PROP_NAME_MAP.get(key, PROP_NAME_MAP.get(key, key or "属性"))
            items.append((label, _fmt_weapon_attr(key, value)))
    if not items and isinstance(data.get("attr"), dict):
        data_attr = data.get("attr") or {}
        level = str(weapon.get("level") or "90")
        promote = str(weapon.get("promote_level") or "")
        level_key = f"{level}+" if promote and promote not in {"0", "1"} and f"{level}+" in (data_attr.get("atk") or {}) else level
        atk_map = data_attr.get("atk") if isinstance(data_attr.get("atk"), dict) else {}
        if level_key in atk_map or level in atk_map:
            items.append(("攻击", _fmt_weapon_attr("atkBase", atk_map.get(level_key, atk_map.get(level)))))
        bonus_key = str(data_attr.get("bonusKey") or "")
        bonus_map = data_attr.get("bonusData") if isinstance(data_attr.get("bonusData"), dict) else {}
        if bonus_key and (level_key in bonus_map or level in bonus_map):
            label = WEAPON_PROP_NAME_MAP.get(bonus_key, PROP_NAME_MAP.get(bonus_key, bonus_key))
            items.append((label, _fmt_weapon_attr(bonus_key, bonus_map.get(level_key, bonus_map.get(level)))))
    if not items and weapon.get("item_id"):
        return [("武器ID", str(weapon.get("item_id")))]
    return items[:4]


def _artifact_set_name(rel: Dict[str, Any]) -> str:
    set_name = _display_name(rel.get("set_name"), "")
    if set_name:
        return set_name
    set_id = str(rel.get("set_id") or rel.get("setId") or "")
    if set_id:
        data = _load_json(_resource_path("meta-gs", "artifact", "data.json"))
        for art_id, item in data.items():
            if not isinstance(item, dict):
                continue
            if str(art_id) == set_id or str(item.get("id") or "") == set_id:
                return str(item.get("name") or "")
    by_id = _find_artifact_by_item_id(str(rel.get("item_id") or rel.get("itemId") or rel.get("id") or ""))
    if by_id.get("set_name"):
        return str(by_id["set_name"])
    name = _display_name(rel.get("name"), "")
    data = _load_json(_resource_path("meta-gs", "artifact", "data.json"))
    for item in data.values():
        if not isinstance(item, dict):
            continue
        idxs = item.get("idxs") or {}
        if any(isinstance(x, dict) and x.get("name") == name for x in idxs.values()):
            return str(item.get("name") or "")
    return ""


def _artifact_pos_index(rel: Dict[str, Any], fallback_idx: int) -> int:
    pos = rel.get("pos")
    if pos in ARTIFACT_SLOT_INDEX:
        return ARTIFACT_SLOT_INDEX[pos]
    by_id = _find_artifact_by_item_id(str(rel.get("item_id") or rel.get("itemId") or rel.get("id") or ""))
    if by_id.get("idx"):
        return int(by_id["idx"])
    try:
        num = int(pos)
        if 1 <= num <= 5:
            return num
    except (TypeError, ValueError):
        pass
    return fallback_idx + 1


def _artifact_icon(rel: Dict[str, Any], fallback_idx: int) -> Path | None:
    set_name = _artifact_set_name(rel)
    idx = _artifact_pos_index(rel, fallback_idx)
    if set_name:
        path = _resource_path("meta-gs", "artifact", "imgs", set_name, f"{idx}.webp")
        if path:
            return path
    by_id = _find_artifact_by_item_id(str(rel.get("item_id") or rel.get("itemId") or rel.get("id") or ""))
    set_name = str(by_id.get("set_name") or "")
    idx = int(by_id.get("idx") or idx)
    if set_name:
        path = _resource_path("meta-gs", "artifact", "imgs", set_name, f"{idx}.webp")
        if path:
            return path
    return None


def _fit_text(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: max(limit - 1, 1)] + "…"


def _display_name(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text or text.isdigit():
        return fallback
    return text


def _artifact_name(rel: Dict[str, Any], fallback: str) -> str:
    name = _display_name(rel.get("name"), "")
    if name:
        return name
    by_id = _find_artifact_by_item_id(str(rel.get("item_id") or rel.get("itemId") or rel.get("id") or ""))
    return str(by_id.get("name") or fallback)


def _prop_name(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("appendPropId") or value.get("prop_id") or value.get("key") or value.get("mainPropId")
    text = str(value or "").strip()
    if not text:
        return "主词条"
    upper = text.upper()
    if text in PROP_NAME_MAP:
        return PROP_NAME_MAP[text]
    if upper in PROP_NAME_MAP:
        return PROP_NAME_MAP[upper]
    return text.replace("FIGHT_PROP_", "").replace("_", " ")[:16]


def _prop_value(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    raw = value.get("value") or value.get("val") or value.get("statValue")
    if raw is None or raw == "":
        return ""
    try:
        num = float(raw)
    except (TypeError, ValueError):
        return str(raw)
    key = str(value.get("appendPropId") or value.get("prop_id") or value.get("key") or value.get("mainPropId") or "").upper()
    suffix = "%" if "PERCENT" in key or "CRITICAL" in key or "HURT" in key or "CHARGE" in key or "ADD" in key or "HEAL" in key else ""
    if abs(num - round(num)) < 0.01:
        return f"{round(num)}{suffix}"
    return f"{num:.1f}{suffix}"


def _artifact_prop_line(prop: Any) -> str:
    if isinstance(prop, dict):
        pn = _prop_name(prop)
        pv = _prop_value(prop)
        return f"{pn}+{pv}" if pv else pn
    return _prop_name(prop)


def _artifact_level(value: Any) -> str:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return "-"
    if level <= 0:
        return "-"
    return str(max(level - 1, 0)) if level > 20 else str(level)


def _star_color(rarity: int) -> Color:
    if rarity >= 5:
        return (211, 160, 85)
    if rarity == 4:
        return (139, 105, 190)
    return (82, 128, 166)


def _element_color(name: str) -> Color:
    text = name or ""
    if any(x in text for x in ["雷电", "雷神", "八重", "刻晴", "赛诺", "克洛琳德"]):
        return (116, 83, 184)
    if any(x in text for x in ["胡桃", "宵宫", "香菱", "可莉", "迪卢克", "班尼特", "玛薇卡", "仆人"]):
        return (170, 69, 56)
    if any(x in text for x in ["夜兰", "行秋", "芙宁娜", "心海", "那维莱特", "妮露"]):
        return (55, 123, 181)
    if any(x in text for x in ["纳西妲", "艾尔海森", "提纳里", "瑶瑶", "白术"]):
        return (88, 142, 76)
    if any(x in text for x in ["钟离", "岩", "娜维娅", "一斗", "凝光", "阿贝多"]):
        return (176, 132, 62)
    if any(x in text for x in ["甘雨", "绫华", "优菈", "申鹤", "莱欧斯利"]):
        return (76, 147, 177)
    if any(x in text for x in ["温迪", "万叶", "魈", "流浪者", "闲云"]):
        return (72, 151, 134)
    return (95, 113, 150)


def _draw_miao_header(img: Image.Image, draw: ImageDraw.ImageDraw, result: PanelResult, char: Dict[str, Any], width: int) -> None:
    name = _char_name(char)
    elem = _element_color(name)
    draw.rectangle((0, 0, width, 520), fill=(34, 34, 38))
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((0, 0, width, 520), fill=(*elem, 80))
    overlay_draw.ellipse((-260, -180, 420, 500), fill=(*elem, 95))
    overlay_draw.ellipse((260, -260, 900, 420), fill=(255, 255, 255, 22))
    img.alpha_composite(overlay)
    draw.polygon([(0, 500), (width, 410), (width, 560), (0, 560)], fill=(22, 23, 27))

    splash = _open_image(_char_image(name, "splash"), (760, 520), contain=True)
    if splash:
        _paste(img, splash, (-80, 8))
        shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(shade).rectangle((0, 0, width, 520), fill=(0, 0, 0, 45))
        img.alpha_composite(shade)
    else:
        draw.ellipse((112, 54, 488, 430), fill=(255, 255, 255, 35), outline=(255, 255, 255, 80), width=3)
        draw.ellipse((190, 88, 410, 308), fill=(255, 255, 255, 48))
        draw.rounded_rectangle((154, 278, 446, 572), radius=145, fill=(255, 255, 255, 42))
        first = name[:1] if name else "?"
        _text(draw, (262, 165), first, (255, 246, 220), _font(120, True))

    _rounded_r(draw, (18, 22, 160, 54), 10, (0, 0, 0, 90))
    _text(draw, (30, 27), f"UID {result.uid}", (235, 230, 216), FONT_TINY)
    src = f"数据源：{result.source}"
    _rounded_r(draw, (width - 170, 22, width - 18, 54), 10, (0, 0, 0, 90))
    _text(draw, (width - 158, 27), src[:12], (235, 230, 216), FONT_TINY)


def _draw_basic_panel(img: Image.Image, draw: ImageDraw.ImageDraw, result: PanelResult, char: Dict[str, Any]) -> int:
    x, y, w, h = 25, 392, 550, 196
    _rounded_r(draw, (x, y, x + w, y + h), 14, (31, 30, 34), (221, 191, 135), 2)
    name = _char_name(char)
    meta = _char_meta(name)
    cons = char.get("constellation")
    level = _safe(char.get("level"), "?")
    _text(draw, (x + 20, y + 16), name, (245, 228, 183), FONT_TITLE)
    _text(draw, (x + 22, y + 68), f"UID {result.uid} - Lv.{level}", (232, 232, 232), FONT_TEXT)
    if cons is not None:
        _rounded_r(draw, (x + 300, y + 68, x + 360, y + 96), 8, (150, 48, 42))
        _text(draw, (x + 315, y + 72), f"{cons}命", (255, 245, 225), FONT_SMALL)

    skills = list(char.get("skill_levels") or [])[:3]
    labels = ["普攻", "战技", "爆发"]
    for idx, label in enumerate(labels):
        lv = skills[idx] if idx < len(skills) else "-"
        cx = x + 28 + idx * 82
        cy = y + 112
        draw.ellipse((cx, cy, cx + 52, cy + 52), fill=(42, 43, 48), outline=(214, 183, 112), width=2)
        icon_key = ["a", "e", "q"][idx]
        icon_path = _talent_icon_path(name, icon_key)
        icon = _open_image(icon_path, (34, 34), contain=True)
        if icon:
            _paste(img, icon, (cx + 9, cy + 8))
        else:
            _text(draw, (cx + 19, cy + 13), lv, (255, 245, 220), FONT_TEXT)
        lv_text = str(lv)
        lv_w = draw.textbbox((0, 0), lv_text, font=FONT_TINY)[2]
        _rounded_r(draw, (cx + 31, cy + 32, cx + 53, cy + 54), 10, (18, 18, 20), (214, 183, 112), 1)
        _text(draw, (cx + 42 - lv_w // 2, cy + 35), lv_text, (255, 245, 220), FONT_TINY)
        _text(draw, (cx + 8, cy + 62), label, (202, 195, 180), FONT_TINY)

    for idx in range(6):
        cx = x + 326 + idx * 33
        cy = y + 122
        icon_path = _resource_path("meta-gs", "character", name, "icons", f"cons-{idx + 1}.webp")
        icon = _open_image(icon_path, (26, 26), contain=True)
        active = cons is not None and idx < int(cons)
        draw.ellipse((cx, cy, cx + 26, cy + 26), fill=(42, 43, 48), outline=(245, 230, 190), width=1)
        if icon:
            if not active:
                icon.putalpha(82)
            _paste(img, icon, (cx, cy))
        else:
            fill = (221, 191, 135) if active else (75, 75, 78)
            draw.ellipse((cx + 2, cy + 2, cx + 24, cy + 24), fill=fill)
    return y + h + 16


def _draw_section_title(draw: ImageDraw.ImageDraw, y: int, title: str, right: str = "") -> int:
    _rounded_r(draw, (25, y, 575, y + 44), 8, (37, 37, 41), (72, 66, 55), 1)
    _text(draw, (45, y + 10), title, (211, 188, 142), FONT_TEXT)
    if right:
        _text(draw, (385, y + 12), right, (160, 160, 160), FONT_TINY)
    return y + 54


def _draw_attrs(draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    props = char.get("fight_props") or {}
    attrs = [
        ("生命值", props.get("生命值") or props.get("HP")),
        ("攻击力", props.get("攻击力")),
        ("防御力", props.get("防御力")),
        ("元素精通", props.get("元素精通")),
        ("暴击率", _fmt(props.get("暴击率"), "%")),
        ("暴击伤害", _fmt(props.get("暴击伤害"), "%")),
        ("元素充能", _fmt(props.get("充能效率"), "%")),
        ("伤害加成", _fmt(props.get("元素伤害加成") or props.get("伤害加成"), "%")),
    ]
    y = _draw_section_title(draw, y, "角色属性")
    row_h = 38
    for idx, (label, value) in enumerate(attrs):
        row = idx // 2
        col = idx % 2
        x = 25 + col * 275
        yy = y + row * row_h
        fill = (42, 42, 46) if row % 2 == 0 else (35, 35, 39)
        draw.rectangle((x, yy, x + 275, yy + row_h), fill=fill)
        _text(draw, (x + 16, yy + 8), label, (210, 210, 210), FONT_SMALL)
        _text(draw, (x + 152, yy + 8), _safe(value), (144, 232, 74), FONT_SMALL)
    return y + 4 * row_h + 16


def _draw_weapon(img: Image.Image, draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    weapon = char.get("weapon") or {}
    if not isinstance(weapon, dict):
        weapon = {}
    rarity = int(weapon.get("rarity") or 5)
    y = _draw_section_title(draw, y, "武器")
    _rounded_r(draw, (25, y, 575, y + 144), 12, (38, 37, 42), (92, 81, 62), 1)
    name = _weapon_name(weapon)
    draw.rounded_rectangle((42, y + 18, 118, y + 94), radius=12, fill=_star_color(rarity))
    icon = _open_image(_weapon_icon(weapon), (72, 72), contain=True)
    if icon:
        _paste(img, icon, (44, y + 20))
    else:
        _text(draw, (66, y + 40), "武", (255, 247, 230), FONT_CARD_TITLE)
    refine = weapon.get("refine") or 1
    _text(draw, (134, y + 18), _fit_text(name, 13), (245, 228, 183), FONT_CARD_TITLE)
    _text(draw, (136, y + 58), f"精{_safe(refine, '1')}  Lv.{_safe(weapon.get('level'), '?')}  {'★' * min(rarity, 5)}", (226, 226, 226), FONT_SMALL)
    attrs = _weapon_attr_items(weapon)
    for idx, (label, value) in enumerate(attrs):
        col = idx % 2
        row = idx // 2
        ax = 136 + col * 170
        ay = y + 90 + row * 24
        _text(draw, (ax, ay), f"{label} +{value}", (206, 210, 220), FONT_TINY)
    return y + 160


def _reliq_label(index: int) -> str:
    return ["生之花", "死之羽", "时之沙", "空之杯", "理之冠"][index] if index < 5 else "圣遗物"


def _draw_artifacts(img: Image.Image, draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    from .artifact_service import (_weight_for_char, artifact_rank,
                                   character_artifact_score, score_reliquary)

    reliqs = [r for r in (char.get("reliquaries") or []) if isinstance(r, dict)][:5]
    _, weight = _weight_for_char(char)
    total, scores, title = character_artifact_score(char)
    y = _draw_section_title(draw, y, "圣遗物", f"{len(reliqs)}/5")
    _rounded_r(draw, (25, y, 575, y + 74), 12, (42, 39, 42), (92, 81, 62), 1)
    _text(draw, (45, y + 15), "圣遗物总分", (210, 210, 210), FONT_SMALL)
    _text(draw, (170, y + 9), f"{total}", (255, 232, 170), FONT_CARD_TITLE)
    _text(draw, (278, y + 15), "评级", (210, 210, 210), FONT_SMALL)
    _text(draw, (330, y + 9), artifact_rank(total), (144, 232, 74), FONT_CARD_TITLE)
    _text(draw, (45, y + 48), f"评分规则：{_fit_text(title, 40)}", (170, 164, 145), FONT_TINY)
    y += 92
    card_w, card_h = 176, 204
    for idx in range(5):
        col = idx % 3
        row = idx // 3
        x = 25 + col * 187
        yy = y + row * 216
        rel = reliqs[idx] if idx < len(reliqs) else {}
        level = _artifact_level(rel.get("level"))
        rarity = int(rel.get("rarity") or 5)
        _rounded_r(draw, (x, yy, x + card_w, yy + card_h), 12, (42, 39, 42), _star_color(rarity), 1)
        draw.rounded_rectangle((x + 12, yy + 12, x + 58, yy + 58), radius=10, fill=_star_color(rarity))
        icon = _open_image(_artifact_icon(rel, idx), (46, 46), contain=True)
        if icon:
            _paste(img, icon, (x + 12, yy + 12))
        else:
            _text(draw, (x + 24, yy + 23), ARTIFACT_SLOT_ICONS[idx], (255, 247, 230), FONT_SMALL)
        title = _artifact_name(rel, _reliq_label(idx))
        _text(draw, (x + 70, yy + 14), _fit_text(title, 6), (245, 228, 183), FONT_SMALL)
        main = _prop_name(rel.get("main_prop") or rel.get("main"))
        main_value = _prop_value(rel.get("main_prop") or rel.get("main"))
        _text(draw, (x + 14, yy + 66), _fit_text(f"{main} {main_value}".strip(), 11), (210, 210, 210), FONT_TINY)
        score = scores[idx] if idx < len(scores) else (score_reliquary(rel, weight, idx) if rel else 0)
        score_text = f"{score:.1f} {artifact_rank(score)}" if rel else "-"
        _text(draw, (x + 14, yy + 88), f"+{level}  {score_text}", (255, 232, 170), FONT_TINY)
        if rel:
            sub_lines = [_artifact_prop_line(prop) for prop in (rel.get("sub_props") or [])[:4]]
            for s_idx, line in enumerate(sub_lines):
                _text(draw, (x + 14, yy + 112 + s_idx * 20), _fit_text(line, 15), (188, 196, 210), FONT_TINY)
    return y + 444


def _draw_artifact_detail(img: Image.Image, draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    from .artifact_service import (_weight_for_char, artifact_rank,
                                   character_artifact_score, score_reliquary)

    title, weight = _weight_for_char(char)
    reliqs = [r for r in (char.get("reliquaries") or []) if isinstance(r, dict)][:5]
    total, scores, _ = character_artifact_score(char)
    y = _draw_section_title(draw, y, "圣遗物评分详情", f"{total} 分 [{artifact_rank(total)}]")
    _text(draw, (38, y), f"评分规则：{title}", (210, 200, 176), FONT_TINY)
    y += 26
    for idx in range(5):
        rel = reliqs[idx] if idx < len(reliqs) else {}
        score = scores[idx] if idx < len(scores) else (score_reliquary(rel, weight, idx) if rel else 0)
        x, h = 25, 112
        _rounded_r(draw, (x, y, 575, y + h), 12, (42, 39, 42), _star_color(int(rel.get("rarity") or 5)), 1)
        icon = _open_image(_artifact_icon(rel, idx), (66, 66), contain=True)
        draw.rounded_rectangle((x + 14, y + 20, x + 80, y + 86), radius=12, fill=_star_color(int(rel.get("rarity") or 5)))
        if icon:
            _paste(img, icon, (x + 14, y + 20))
        else:
            _text(draw, (x + 35, y + 39), ARTIFACT_SLOT_ICONS[idx], (255, 247, 230), FONT_TEXT)
        name = _artifact_name(rel, _reliq_label(idx))
        main = _prop_name(rel.get("main_prop") or rel.get("main"))
        level = _artifact_level(rel.get("level"))
        _text(draw, (x + 96, y + 16), _fit_text(name, 15), (245, 228, 183), FONT_SMALL)
        _text(draw, (x + 96, y + 44), f"{_reliq_label(idx)}  +{level}  主词条：{main}", (218, 218, 218), FONT_TINY)
        subs = []
        for prop in rel.get("sub_props") or []:
            if isinstance(prop, dict):
                prop_name = _prop_name(prop.get("appendPropId") or prop.get("prop_id") or prop.get("key"))
                prop_value = _prop_value(prop)
                subs.append(f"{prop_name}+{prop_value}" if prop_value else prop_name)
            else:
                subs.append(_prop_name(prop))
        _text(draw, (x + 96, y + 72), _fit_text(" / ".join(subs) or "无副词条", 34), (188, 196, 210), FONT_TINY)
        _rounded_r(draw, (x + 462, y + 22, x + 532, y + 62), 10, (80, 62, 36), (221, 191, 135), 1)
        _text(draw, (x + 472, y + 30), f"{score:.1f}", (255, 232, 170), FONT_TEXT)
        _text(draw, (x + 468, y + 70), artifact_rank(score), (144, 232, 74), FONT_TINY)
        y += h + 12
    return y


def _draw_miao_profile(img: Image.Image, draw: ImageDraw.ImageDraw, result: PanelResult, char: Dict[str, Any], width: int, height: int) -> int:
    _draw_miao_header(img, draw, result, char, width)
    y = _draw_basic_panel(img, draw, result, char)
    y = _draw_attrs(draw, y, char)
    y = _draw_weapon(img, draw, y, char)
    y = _draw_artifacts(img, draw, y, char)
    return y


def _crop_panel_canvas(img: Image.Image, content_bottom: int, footer: str) -> Image.Image:
    final_height = max(content_bottom + 74, 760)
    final_height = min(final_height, img.height)
    cropped = img.crop((0, 0, img.width, final_height))
    draw = ImageDraw.Draw(cropped)
    _text(draw, (30, final_height - 38), footer, (150, 145, 132), FONT_TINY)
    return cropped


async def render_panel_image(result: PanelResult) -> bytes:
    characters = list(_iter_cards((result.characters or [])[:8]))
    if len(characters) == 1:
        width = 600
        height = 1760
        img = Image.new("RGBA", (width, height), (22, 23, 27, 255))
        draw = ImageDraw.Draw(img)
        bottom = _draw_miao_profile(img, draw, result, characters[0], width, height)
        img = _crop_panel_canvas(img, bottom, "Created by gscore_miao-plugin · layout inspired by miao-plugin")
        return await convert_img(img)

    card_count = max(len(characters), 1)
    cols = 2
    rows = (card_count + cols - 1) // cols
    width = 1440
    header_h = 220
    card_w = 650
    card_h = 260
    gap = 32
    footer_h = 86
    height = header_h + rows * card_h + max(rows - 1, 0) * gap + footer_h + 60

    img = _gradient_bg(width, height).convert("RGBA")
    draw = ImageDraw.Draw(img)

    draw.ellipse((width - 420, -260, width + 180, 330), fill=(83, 112, 181, 55))
    draw.ellipse((-220, height - 360, 360, height + 180), fill=(231, 184, 99, 35))

    _text(draw, (64, 48), "喵喵角色面板", (255, 247, 220), FONT_TITLE)
    info = f"UID {result.uid}  ·  数据源 {result.source}"
    if result.nickname:
        info += f"  ·  {result.nickname}"
    if result.level is not None:
        info += f"  Lv.{result.level}"
    _text(draw, (68, 116), info, (199, 210, 230), FONT_SUBTITLE)
    if result.signature:
        _text(draw, (68, 154), result.signature[:58], (158, 171, 199), FONT_SMALL)

    if not characters:
        _rounded(draw, (64, header_h, width - 64, header_h + 180), (31, 39, 61), (70, 83, 120))
        _text(draw, (104, header_h + 58), "当前数据源没有返回可渲染的角色详情。", (248, 244, 232), FONT_CARD_TITLE)
        _text(draw, (104, header_h + 104), "请确认 Enka 展柜角色已公开，或切换 Miao/米游社数据源后重试。", (190, 201, 221), FONT_TEXT)
    else:
        for idx, char in enumerate(characters, start=1):
            col = (idx - 1) % cols
            row = (idx - 1) // cols
            x = 64 + col * (card_w + gap)
            y = header_h + row * (card_h + gap)
            _draw_character_card(draw, char, idx, x, y, card_w, card_h)

    footer = "Generated by gscore_miao-plugin · miao-plugin panel template for GsCore"
    _text(draw, (64, height - 62), footer, (145, 158, 186), FONT_SMALL)
    return await convert_img(img)


async def render_single_panel_image(result: PanelResult, character_query: str = "") -> bytes:
    characters = list(_iter_cards(result.characters or []))
    if character_query:
        q = character_query.strip().lower()
        resolved = q
        try:
            from .alias_data import resolve_alias

            resolved = (resolve_alias(character_query) or character_query).strip().lower()
        except Exception:
            pass
        filtered = [
            c for c in characters
            if q in _char_match_text(c) or resolved in _char_match_text(c)
        ]
        if not filtered:
            available = "、".join(_char_name(c) for c in characters[:8]) or "无角色"
            raise ValueError(f"未在 UID {result.uid} 的公开面板中找到角色：{character_query}。当前可见角色：{available}")
        if filtered:
            characters = filtered
    if characters:
        result = PanelResult(
            source=result.source,
            uid=result.uid,
            raw=result.raw,
            nickname=result.nickname,
            level=result.level,
            signature=result.signature,
            avatars=result.avatars,
            characters=characters[:1],
        )
    return await render_panel_image(result)


async def render_artifact_image(result: PanelResult, character_query: str = "") -> bytes:
    characters = list(_iter_cards(result.characters or []))
    if character_query:
        q = character_query.strip().lower()
        try:
            from .alias_data import resolve_alias

            resolved = (resolve_alias(character_query) or character_query).strip().lower()
        except Exception:
            resolved = q
        characters = [c for c in characters if q in _char_match_text(c) or resolved in _char_match_text(c)]
        if not characters:
            available = "、".join(_char_name(c) for c in list(_iter_cards(result.characters or []))[:8]) or "无角色"
            raise ValueError(f"未在 UID {result.uid} 的公开面板中找到角色：{character_query}。当前可见角色：{available}")
    if not characters:
        raise ValueError("当前数据源没有返回可渲染的角色详情")
    char = characters[0]
    width = 600
    height = 1520
    img = Image.new("RGBA", (width, height), (22, 23, 27, 255))
    draw = ImageDraw.Draw(img)
    _draw_miao_header(img, draw, result, char, width)
    y = _draw_basic_panel(img, draw, result, char)
    y = _draw_artifact_detail(img, draw, y, char)
    img = _crop_panel_canvas(img, y, "Created by gscore_miao-plugin · artifact detail inspired by miao-plugin")
    return await convert_img(img)


async def render_artifact_list_image(result: PanelResult) -> bytes:
    from .artifact_service import artifact_rank, character_artifact_score

    chars = list(_iter_cards(result.characters or []))
    rows = []
    for char in chars:
        total, scores, title = character_artifact_score(char)
        rows.append((total, char, scores, title))
    rows.sort(key=lambda x: x[0], reverse=True)
    width = 900
    height = 170 + max(1, len(rows[:16])) * 74 + 80
    img = _gradient_bg(width, height).convert("RGBA")
    draw = ImageDraw.Draw(img)
    _text(draw, (52, 42), "喵喵圣遗物列表", (255, 247, 220), FONT_TITLE)
    _text(draw, (56, 100), f"UID {result.uid} · 数据源 {result.source} · 按总评分排序", (199, 210, 230), FONT_SMALL)
    if not rows:
        _rounded_r(draw, (52, 160, width - 52, 280), 14, (31, 39, 61), (70, 83, 120), 1)
        _text(draw, (82, 200), "当前数据源没有返回圣遗物详情。", (248, 244, 232), FONT_TEXT)
    for idx, (total, char, scores, title) in enumerate(rows[:16], start=1):
        y = 160 + (idx - 1) * 74
        _rounded_r(draw, (52, y, width - 52, y + 60), 12, (31, 39, 61), (70, 83, 120), 1)
        _text(draw, (72, y + 16), f"{idx}", (255, 232, 170), FONT_TEXT)
        _text(draw, (120, y + 12), _char_name(char), (248, 244, 232), FONT_TEXT)
        _text(draw, (300, y + 14), " / ".join(f"{x:.1f}" for x in scores[:5]) or "无圣遗物", (190, 201, 221), FONT_TINY)
        _text(draw, (650, y + 12), f"{total:.1f} [{artifact_rank(total)}]", (144, 232, 74), FONT_TEXT)
        _text(draw, (120, y + 38), _fit_text(title, 28), (160, 171, 190), FONT_TINY)
    _text(draw, (54, height - 42), "评分权重读取本地 miao-plugin resources/meta-gs/artifact/artis-mark.js", (145, 158, 186), FONT_TINY)
    return await convert_img(img)


async def render_help_image(title: str, subtitle: str, groups: List[Dict[str, Any]], prefix: str) -> bytes:
    width = 1200
    cols = 2
    item_h = 86
    group_gap = 34
    content_h = 0
    for group in groups:
        count = len(group.get("items") or [])
        rows = (count + cols - 1) // cols
        content_h += 64 + rows * item_h + group_gap
    height = max(900, 230 + content_h + 72)
    img = _gradient_bg(width, height).convert("RGBA")

    bg = _cover_image(_help_bg_path(), (width, height))
    if bg:
        bg.putalpha(110)
        img.alpha_composite(bg)
    img.alpha_composite(Image.new("RGBA", (width, height), (10, 14, 24, 132)))

    draw = ImageDraw.Draw(img)
    draw.ellipse((width - 430, -250, width + 180, 360), fill=(231, 184, 99, 62))
    draw.ellipse((-260, 120, 360, 740), fill=(88, 123, 190, 48))

    _text(draw, (68, 54), title or "喵喵帮助", (255, 247, 222), FONT_HELP_TITLE)
    _text(draw, (72, 120), subtitle or "Yunzai miao-plugin 的 GsCore 迁移版", (220, 228, 244), FONT_SUBTITLE)
    _text(draw, (72, 158), f"当前命令前缀：{prefix} · 可在 WebUI 的 CommandPrefix 修改，重启后生效", (170, 182, 207), FONT_SMALL)

    y = 220
    card_w = 510
    left_x = 70
    right_x = 620
    for group in groups:
        items = list(group.get("items") or [])
        if not items:
            continue
        _rounded_r(draw, (58, y - 10, width - 58, y + 44), 18, (36, 43, 66), (92, 109, 150), 1)
        _text(draw, (84, y), f"✦ {group.get('group') or '命令'}", (255, 232, 174), FONT_HELP_GROUP)
        y += 64
        for idx, item in enumerate(items):
            col = idx % cols
            row = idx // cols
            x = left_x if col == 0 else right_x
            cy = y + row * item_h
            _rounded_r(draw, (x, cy, x + card_w, cy + 66), 16, (28, 34, 54), (76, 91, 129), 1)
            cmd = str(item.get("cmd") or "").replace("{prefix}", prefix)
            desc = str(item.get("desc") or "")
            _text(draw, (x + 22, cy + 12), _fit_text(cmd, 25), (248, 244, 232), FONT_HELP_CMD)
            _text(draw, (x + 24, cy + 42), _fit_text(desc, 30), (185, 197, 220), FONT_HELP_DESC)
        y += ((len(items) + cols - 1) // cols) * item_h + group_gap

    _text(draw, (70, height - 48), "Created by gscore_miao-plugin · help card inspired by XutheringWavesUID & miao-plugin", (150, 163, 190), FONT_TINY)
    return await convert_img(img)