from __future__ import annotations

import json
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

    avatar_name = char.get("name") or char.get("avatar_name") or f"角色ID {char.get('avatar_id') or '?'}"
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
        weapon_name = _display_name(weapon.get("name"), "未知武器")
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
    name = char.get("name") or char.get("avatar_name")
    if name:
        return str(name)
    avatar_id = char.get("avatar_id") or char.get("avatarId")
    try:
        mapped = CHARACTER_ID_NAMES.get(int(avatar_id))
    except (TypeError, ValueError):
        mapped = None
    return mapped or "未知角色"


def _char_meta(name: str) -> Dict[str, Any]:
    return _load_json(_resource_path("meta-gs", "character", name, "data.json"))


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


def _weapon_icon(name: str) -> Path | None:
    return _find_named_resource("meta-gs/weapon", name, "icon.webp")


def _artifact_set_name(rel: Dict[str, Any]) -> str:
    set_name = _display_name(rel.get("set_name"), "")
    if set_name:
        return set_name
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
    try:
        num = int(pos)
        if 1 <= num <= 5:
            return num
    except (TypeError, ValueError):
        pass
    return fallback_idx + 1


def _artifact_icon(rel: Dict[str, Any], fallback_idx: int) -> Path | None:
    set_name = _artifact_set_name(rel)
    if not set_name:
        return None
    idx = _artifact_pos_index(rel, fallback_idx)
    return _resource_path("meta-gs", "artifact", "imgs", set_name, f"{idx}.webp")


def _fit_text(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: max(limit - 1, 1)] + "…"


def _display_name(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text or text.isdigit():
        return fallback
    return text


def _prop_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "主词条"
    upper = text.upper()
    if text in PROP_NAME_MAP:
        return PROP_NAME_MAP[text]
    if upper in PROP_NAME_MAP:
        return PROP_NAME_MAP[upper]
    return text.replace("FIGHT_PROP_", "").replace("_", " ")[:16]


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
    draw.rectangle((0, 0, width, 520), fill=(*elem, 80))
    draw.ellipse((-260, -180, 420, 500), fill=(*elem, 95))
    draw.ellipse((260, -260, 900, 420), fill=(255, 255, 255, 22))
    draw.polygon([(0, 500), (width, 410), (width, 560), (0, 560)], fill=(22, 23, 27))

    splash = _open_image(_char_image(name, "splash"), (760, 520), contain=True)
    if splash:
        _paste(img, splash, (-80, 8))
        draw.rectangle((0, 0, width, 520), fill=(0, 0, 0, 45))
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
    x, y, w, h = 25, 392, 550, 178
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
        cy = y + 113
        draw.ellipse((cx, cy, cx + 52, cy + 52), fill=(42, 43, 48), outline=(214, 183, 112), width=2)
        icon_key = ["a", "e", "q"][idx]
        talent_ids = meta.get("talentId") or {}
        talent_file = "atk-sword.webp" if icon_key == "a" else f"talent-{icon_key}.webp"
        if icon_key == "a":
            icon_path = _resource_path("common", "item", talent_file)
        else:
            icon_path = _resource_path("meta-gs", "character", name, "icons", talent_file)
        icon = _open_image(icon_path, (34, 34), contain=True)
        if icon:
            _paste(img, icon, (cx + 9, cy + 8))
        else:
            _text(draw, (cx + 19, cy + 13), lv, (255, 245, 220), FONT_TEXT)
        _text(draw, (cx + 19, cy + 34), lv, (255, 245, 220), FONT_TINY)
        _text(draw, (cx + 8, cy + 56), label, (202, 195, 180), FONT_TINY)

    for idx in range(6):
        cx = x + 326 + idx * 33
        cy = y + 122
        fill = (221, 191, 135) if cons is not None and idx < int(cons) else (75, 75, 78)
        draw.ellipse((cx, cy, cx + 24, cy + 24), fill=fill, outline=(245, 230, 190), width=1)
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
    _rounded_r(draw, (25, y, 575, y + 112), 12, (38, 37, 42), (92, 81, 62), 1)
    name = _display_name(weapon.get("name"), "未知武器")
    draw.rounded_rectangle((42, y + 18, 118, y + 94), radius=12, fill=_star_color(rarity))
    icon = _open_image(_weapon_icon(name), (72, 72), contain=True)
    if icon:
        _paste(img, icon, (44, y + 20))
    else:
        _text(draw, (66, y + 40), "武", (255, 247, 230), FONT_CARD_TITLE)
    refine = weapon.get("refine") or 1
    _text(draw, (134, y + 18), _fit_text(name, 13), (245, 228, 183), FONT_CARD_TITLE)
    _text(draw, (136, y + 58), f"精{_safe(refine, '1')}  Lv.{_safe(weapon.get('level'), '?')}  {'★' * min(rarity, 5)}", (226, 226, 226), FONT_SMALL)
    return y + 128


def _reliq_label(index: int) -> str:
    return ["生之花", "死之羽", "时之沙", "空之杯", "理之冠"][index] if index < 5 else "圣遗物"


def _draw_artifacts(img: Image.Image, draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    reliqs = [r for r in (char.get("reliquaries") or []) if isinstance(r, dict)][:5]
    y = _draw_section_title(draw, y, "圣遗物", f"{len(reliqs)}/5")
    card_w, card_h = 176, 128
    for idx in range(5):
        col = idx % 3
        row = idx // 3
        x = 25 + col * 187
        yy = y + row * 140
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
        title = _display_name(rel.get("name"), _reliq_label(idx))
        _text(draw, (x + 70, yy + 14), _fit_text(title, 6), (245, 228, 183), FONT_SMALL)
        main = _prop_name(rel.get("main_prop") or rel.get("main"))
        _text(draw, (x + 14, yy + 68), main, (210, 210, 210), FONT_TINY)
        _text(draw, (x + 14, yy + 94), f"+{level}  {'★' * min(rarity, 5)}", (144, 232, 74), FONT_TINY)
    return y + 292


def _draw_miao_profile(img: Image.Image, draw: ImageDraw.ImageDraw, result: PanelResult, char: Dict[str, Any], width: int, height: int) -> None:
    _draw_miao_header(img, draw, result, char, width)
    y = _draw_basic_panel(img, draw, result, char)
    y = _draw_attrs(draw, y, char)
    y = _draw_weapon(img, draw, y, char)
    y = _draw_artifacts(img, draw, y, char)
    _text(draw, (30, height - 38), "Created by gscore_miao-plugin · layout inspired by miao-plugin", (150, 145, 132), FONT_TINY)


async def render_panel_image(result: PanelResult) -> bytes:
    characters = list(_iter_cards((result.characters or [])[:8]))
    if len(characters) == 1:
        width = 600
        height = 1180
        img = Image.new("RGBA", (width, height), (22, 23, 27, 255))
        draw = ImageDraw.Draw(img)
        _draw_miao_profile(img, draw, result, characters[0], width, height)
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
        q = character_query.lower()
        resolved = q
        try:
            from .alias_data import resolve_alias

            resolved = (resolve_alias(character_query) or character_query).lower()
        except Exception:
            pass
        filtered = [
            c for c in characters
            if q in str(c.get("name") or c.get("avatar_name") or c.get("avatar_id") or "").lower()
            or resolved in str(c.get("name") or c.get("avatar_name") or c.get("avatar_id") or "").lower()
        ]
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