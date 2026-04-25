from __future__ import annotations

import json
from datetime import datetime
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
SR_RELIC_SLOT_ICONS = ["头", "手", "躯", "脚", "球", "绳"]

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
    "speed": "速度",
    "spd": "速度",
    "break_effect": "击破特攻",
    "breakEffect": "击破特攻",
    "stance": "击破特攻",
    "effect_hit": "效果命中",
    "effectHitRate": "效果命中",
    "effPct": "效果命中",
    "effect_res": "效果抵抗",
    "effectRes": "效果抵抗",
    "effDef": "效果抵抗",
    "energy_recharge": "能量恢复效率",
    "recharge": "能量恢复效率",
    "break_dmg": "击破特攻",
    "breakDamage": "击破特攻",
    "crit_rate": "暴击率",
    "critRate": "暴击率",
    "crit_dmg": "暴击伤害",
    "critDamage": "暴击伤害",
    "effect_hit_rate": "效果命中",
    "effect_resistance": "效果抵抗",
    "dmg": "伤害加成",
    "phy": "物理伤害",
    "fire": "火伤加成",
    "ice": "冰伤加成",
    "elec": "雷伤加成",
    "wind": "风伤加成",
    "quantum": "量子伤害",
    "imaginary": "虚数伤害",
    "cpct": "暴击率",
    "cdmg": "暴击伤害",
    "hp": "生命值",
    "atk": "攻击力",
    "def": "防御力",
    "hpPlus": "生命值",
    "atkPlus": "攻击力",
    "defPlus": "防御力",
    "hpplus": "生命值",
    "atkplus": "攻击力",
    "defplus": "防御力",
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
    "speed": "速度",
    "stance": "击破",
    "effPct": "命中",
    "effDef": "抵抗",
    "heal": "治疗",
    "shield": "护盾",
}


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _append_resource_dir(dirs: List[Path], path: Path | None) -> None:
    if not path:
        return
    resource_dir = path if path.name == "resources" else path / "resources"
    try:
        resource_dir = resource_dir.resolve()
    except Exception:
        pass
    if resource_dir.exists() and resource_dir not in dirs:
        dirs.append(resource_dir)


@lru_cache(maxsize=1)
def _resource_dirs() -> Tuple[Path, ...]:
    dirs: List[Path] = []

    # 优先使用本插件自带资源，避免要求用户额外 clone Yunzai miao-plugin。
    root = _plugin_root()
    _append_resource_dir(dirs, root)
    _append_resource_dir(dirs, root / "gscore_miao_plugin")

    configured = str(MiaoConfig.get_config("MiaoPluginResourcePath").data or "").strip()
    if configured:
        _append_resource_dir(dirs, Path(configured))

    # 兼容旧配置/旧部署：仅当本插件资源不存在或缺素材时再回退外部 miao-plugin。
    _append_resource_dir(dirs, root.parent / "miao-plugin")
    _append_resource_dir(dirs, Path("E:/gsuid_core/gsuid_core/plugins/miao-plugin"))
    return tuple(dirs)


def _font(size: int, bold: bool = False, miao: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if miao:
        candidates.extend(str(resource_dir / "common" / "font" / miao) for resource_dir in _resource_dirs())
    candidates.extend([
        "msyhbd.ttc" if bold else "msyh.ttc",
        "Microsoft YaHei UI Bold.ttf" if bold else "Microsoft YaHei UI.ttf",
        "simhei.ttf",
        "arial.ttf",
    ])
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
FONT_PROFILE_TITLE = _font(42, True, "NZBZ.ttf")
FONT_PROFILE_UID = _font(21, True, "NZBZ.ttf")
FONT_PROFILE_LABEL = _font(18, True, "HYWH-65W.ttf")
FONT_PROFILE_SMALL = _font(13, False, "HYWH-65W.ttf")
FONT_PROFILE_NAME = _font(18, True, "HYWH-65W.ttf")
FONT_PROFILE_CONS = _font(12, True, "HYWH-65W.ttf")
FONT_PROFILE_CREDIT = _font(18, True, "NZBZ.ttf")


def _text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: Any, fill: Color, font: ImageFont.ImageFont) -> None:
    draw.text(xy, str(text), fill=fill, font=font)


def _shadow_text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: Any, fill: Color, font: ImageFont.ImageFont, shadow: Color = (0, 0, 0)) -> None:
    x, y = xy
    draw.text((x + 2, y + 2), str(text), fill=shadow, font=font)
    draw.text((x, y), str(text), fill=fill, font=font)


def _miao_root() -> Path | None:
    dirs = _resource_dirs()
    return dirs[0].parent if dirs else None


def _resource_path(*parts: str) -> Path | None:
    rel = Path(*parts)
    for resource_dir in _resource_dirs():
        path = resource_dir / rel
        if path.exists():
            return path
    return None


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


def _avatar_circle(path: Path | None, size: int) -> Image.Image | None:
    if not path or not path.exists():
        return None
    try:
        src = Image.open(path).convert("RGBA")
    except Exception:
        return None
    scale = max(size / src.width, size / src.height)
    avatar = src.resize((max(size, int(src.width * scale)), max(size, int(src.height * scale))), Image.Resampling.LANCZOS)
    left = max((avatar.width - size) // 2, 0)
    top = max((avatar.height - size) // 2, 0)
    avatar = avatar.crop((left, top, left + size, top + size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    avatar.putalpha(mask)
    return avatar


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
    target = str(item_id)
    for resource_dir in _resource_dirs():
        root_dir = resource_dir / Path(base)
        if not root_dir.exists():
            continue
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


@lru_cache(maxsize=4096)
def _find_sr_artifact_by_item_id(item_id: str) -> Dict[str, Any]:
    data = _load_json(_resource_path("meta-sr", "artifact", "data.json"))
    target = str(item_id or "")
    if not target:
        return {}
    for set_item in data.values():
        if not isinstance(set_item, dict):
            continue
        idxs = set_item.get("idxs") or {}
        for idx, item in idxs.items():
            if not isinstance(item, dict):
                continue
            ids = item.get("ids") or {}
            if str(target) in {str(k) for k in ids.keys()}:
                return {
                    "set_name": str(set_item.get("name") or ""),
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


def _fmt_attr_value(label: str, value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, dict):
        value = value.get("display") or value.get("value_str") or value.get("valueStr") or value.get("formatted") or value.get("value") or value.get("val") or value.get("total")
    text = str(value).strip()
    if not text:
        return "-"
    if text.endswith("%"):
        return text
    try:
        num = float(text)
    except (TypeError, ValueError):
        return text
    pct_labels = ("暴击", "伤害加成", "击破", "效果", "充能", "恢复", "治疗")
    if any(key in label for key in pct_labels):
        if 0 < abs(num) < 1:
            num *= 100
        return _fmt(num, "%")
    return _fmt(num)


def _first_prop(props: Dict[str, Any], *keys: str) -> Any:
    aliases = {
        "生命值": ("生命值", "HP", "hp", "max_hp", "maxHp"),
        "攻击力": ("攻击力", "ATK", "atk", "attack"),
        "防御力": ("防御力", "DEF", "def", "defense"),
        "速度": ("速度", "speed", "spd"),
        "暴击率": ("暴击率", "cpct", "crit_rate", "critRate"),
        "暴击伤害": ("暴击伤害", "cdmg", "crit_dmg", "critDamage"),
        "伤害加成": ("伤害加成", "元素伤害加成", "dmg", "damage", "element_dmg"),
        "击破特攻": ("击破特攻", "stance", "break_effect", "breakEffect", "break_dmg", "breakDamage"),
        "效果命中": ("效果命中", "effPct", "effect_hit", "effectHitRate", "effect_hit_rate"),
        "效果抵抗": ("效果抵抗", "effDef", "effect_res", "effectRes", "effect_resistance"),
        "元素精通": ("元素精通", "mastery", "element_mastery"),
        "充能效率": ("充能效率", "元素充能", "recharge", "energy_recharge"),
    }
    for key in keys:
        for candidate in aliases.get(key, (key,)):
            if candidate in props and props[candidate] not in (None, ""):
                return props[candidate]
    return None


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
    is_sr = char.get("game") == "sr"
    lines = [
        _stat_line("行迹" if is_sr else "天赋", skill_levels),
        _stat_line("光锥" if is_sr else "武器", f"{weapon_name} Lv.{weapon_level}"),
        _stat_line("遗器" if is_sr else "圣遗物", f"{reliq_count}/{6 if is_sr else 5}"),
        _stat_line("双暴", f"{_safe(crit)}% / {_safe(crit_dmg)}%" if crit is not None or crit_dmg is not None else "-"),
        _stat_line("充能", f"{recharge}%" if recharge is not None else "-"),
        _stat_line("攻击/精通", f"{_safe(atk)} / {_safe(mastery)}"),
    ]
    for row, line in enumerate(lines):
        col_x = left + (row % 2) * 330
        row_y = top + (row // 2) * 42
        _text(draw, (col_x, row_y), line, (220, 226, 238), FONT_TEXT)


def _draw_profile_list_card(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], fill: Color = (16, 26, 42), outline: Color = (74, 92, 124)) -> None:
    _rounded_r(draw, box, 12, (*fill, 214), (*outline, 190), 1)


def _char_rank_info(char: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rank = char.get("groupRank") or char.get("group_rank")
    if not isinstance(rank, dict):
        return None
    rank_value = rank.get("rank")
    try:
        rank_value = int(rank_value)
    except (TypeError, ValueError):
        return None
    rank_type = str(rank.get("rankType") or rank.get("rank_type") or "dmg")
    frame = rank_value if rank_value <= 3 else 4
    return {"rank": rank_value, "rank_type": rank_type, "frame": frame}


def _rank_sprite(char: Dict[str, Any], size: int) -> Optional[Image.Image]:
    rank = _char_rank_info(char)
    if not rank:
        return None
    path = _resource_path("character", "imgs", "mark-rank-bg.png" if rank["rank_type"] == "mark" else "dmg-rank-bg.png")
    sprite = _open_image(path)
    if sprite:
        frame_w = sprite.width // 5
        rank_index = int(rank["frame"])
        return sprite.crop((frame_w * rank_index, 0, frame_w * (rank_index + 1), sprite.height)).resize((size, size), Image.Resampling.BICUBIC)


def _draw_rank_sprite(img: Image.Image, char: Dict[str, Any], x: int, y: int, size: int) -> None:
    crop = _rank_sprite(char, size)
    if crop:
        img.alpha_composite(crop, (x, y))
    rank = _char_rank_info(char)
    if not rank or int(rank["frame"]) != 4:
        return
    draw = ImageDraw.Draw(img)
    text = str(rank["rank"])
    tw = draw.textbbox((0, 0), text, font=FONT_PROFILE_CONS)[2]
    _shadow_text(draw, (x + (size - tw) // 2, y + size - 23), text, (255, 238, 212), FONT_PROFILE_CONS)


def _draw_avatar_orange_base(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    pad = 6
    box = (x - pad, y - pad, x + size + pad, y + size + pad)
    draw.ellipse(box, fill=(185, 121, 63), outline=(255, 238, 201), width=3)
    inner = (x - 2, y - 2, x + size + 2, y + size + 2)
    draw.ellipse(inner, outline=(126, 79, 42), width=2)


def _draw_profile_avatar(img: Image.Image, draw: ImageDraw.ImageDraw, char: Dict[str, Any], x: int, y: int, is_new: bool) -> None:
    name = _char_name(char)
    size = 82
    face = _avatar_circle(_char_face_path(name, char.get("game", "gs")), size)
    rank_size = 94
    rank_x = x - 6
    rank_y = y - 6
    rank_bg = _rank_sprite(char, rank_size)
    rank_info = _char_rank_info(char)
    if rank_bg:
        img.alpha_composite(rank_bg, (rank_x, rank_y))
    else:
        _draw_avatar_orange_base(draw, x, y, size)
    draw.ellipse((x, y, x + size, y + size), fill=_star_color(_char_star(char)), outline=(255, 255, 255), width=2)
    if face:
        img.alpha_composite(face, (x, y))
    else:
        _text(draw, (x + 25, y + 20), name[:1] or "?", (255, 245, 225), FONT_CARD_TITLE)
    if rank_bg:
        label_h = 31
        label = rank_bg.crop((0, rank_size - label_h, rank_size, rank_size))
        img.alpha_composite(label, (rank_x, rank_y + rank_size - label_h))
    if rank_info and int(rank_info["frame"]) == 4:
        text = str(rank_info["rank"])
        tb = draw.textbbox((0, 0), text, font=FONT_PROFILE_CONS)
        _shadow_text(draw, (x + (size - (tb[2] - tb[0])) // 2, y + size - 22), text, (255, 238, 212), FONT_PROFILE_CONS)
    name_text = _fit_text(name, 5)
    cons = _safe(char.get("constellation"), "0")
    ny = y + size + 7
    name_x = x
    if is_new:
        draw.ellipse((x - 1, ny + 7, x + 9, ny + 17), fill=(144, 232, 0))
        name_x += 11
    _shadow_text(draw, (name_x, ny), name_text, (248, 248, 248), FONT_PROFILE_NAME)
    nb = draw.textbbox((0, 0), name_text, font=FONT_PROFILE_NAME)
    cons_x = name_x + (nb[2] - nb[0]) + 3
    cons_color = (76, 184, 198) if str(cons) not in {"0", "-"} else (92, 98, 110)
    if str(cons) == "6":
        cons_color = (230, 70, 30)
    _rounded_r(draw, (cons_x, ny + 5, cons_x + 20, ny + 23), 5, cons_color)
    _text(draw, (cons_x + 6, ny + 5), str(cons), (255, 255, 255), FONT_PROFILE_CONS)


def _draw_profile_list_image(result: PanelResult, characters: List[Dict[str, Any]], updated: bool) -> Image.Image:
    is_sr = result.game == "sr"
    scale = 1.6
    width = 1040
    cols = 8
    rows = max(1, (len(characters) + cols - 1) // cols)
    header_h = 178
    rank_h = 58
    list_h = 34 + rows * 145 + 22
    footer_h = 56
    height = header_h + rank_h + list_h + footer_h + 74
    img = Image.new("RGBA", (width, height), (10, 18, 32, 255))
    bg = _cover_image(_resource_path("common", "theme", "bg-01.jpg") or _resource_path("character", "imgs", "bg-01.jpg"), (width, height))
    if bg:
        img.alpha_composite(bg)
    img.alpha_composite(Image.new("RGBA", (width, height), (4, 13, 30, 54)))
    draw = ImageDraw.Draw(img)

    _shadow_text(draw, (48, 32), "#星铁面板列表" if is_sr else "#面板列表", (255, 255, 255), FONT_PROFILE_TITLE)
    _shadow_text(draw, (332, 70), f"UID:{result.uid}", (255, 255, 255), FONT_PROFILE_UID)
    msg = "获取角色面板数据成功" if updated else "当前已缓存角色面板数据"
    _shadow_text(draw, (49, 105), msg, (255, 255, 255), FONT_PROFILE_LABEL)
    demo = _char_name(characters[0]) if characters else "角色"
    hint_y = 132
    _shadow_text(draw, (49, hint_y), "你可以使用", (255, 255, 255), FONT_PROFILE_LABEL)
    prefix = "#星铁" if is_sr else "#"
    _shadow_text(draw, (161, hint_y), f"{prefix}{demo}面板", (246, 199, 74), FONT_PROFILE_LABEL)
    _shadow_text(draw, (293, hint_y), "、", (255, 255, 255), FONT_PROFILE_LABEL)
    _shadow_text(draw, (318, hint_y), f"{prefix}{demo}伤害", (246, 199, 74), FONT_PROFILE_LABEL)
    _shadow_text(draw, (450, hint_y), "、", (255, 255, 255), FONT_PROFILE_LABEL)
    _shadow_text(draw, (475, hint_y), f"{prefix}{demo}{'遗器' if is_sr else '圣遗物'}", (246, 199, 74), FONT_PROFILE_LABEL)
    _shadow_text(draw, (628, hint_y), "命令来查看面板信息了", (255, 255, 255), FONT_PROFILE_LABEL)

    y = header_h
    _draw_profile_list_card(draw, (16, y, width - 16, y + rank_h), (14, 24, 39), (81, 98, 132))
    icon = _open_image(_resource_path("character", "imgs", "mark-icon.png"))
    if icon:
        img.alpha_composite(icon.crop((0, 0, 16, 16)).resize((22, 22), Image.Resampling.BICUBIC), (42, y + 18))
        img.alpha_composite(icon.crop((16, 0, 32, 16)).resize((22, 22), Image.Resampling.BICUBIC), (196, y + 18))
    else:
        draw.ellipse((42, y + 19, 63, y + 40), fill=(244, 68, 58))
        draw.ellipse((196, y + 19, 217, y + 40), fill=(247, 185, 53))
    _text(draw, (71, y + 17), "综合练度排名", (255, 255, 255), FONT_PROFILE_LABEL)
    _text(draw, (225, y + 17), "遗器评分排名" if is_sr else "圣遗物评分排名", (255, 255, 255), FONT_PROFILE_LABEL)
    time_text = datetime.now().strftime("%m-%d %H:%M")
    _text(draw, (388, y + 21), f"排名：本群内 {time_text} 后，通过 #面板 命令查看过的角色数据", (170, 178, 193), FONT_PROFILE_SMALL)

    y += rank_h + 10
    _draw_profile_list_card(draw, (16, y, width - 16, y + list_h + footer_h), (18, 33, 50), (84, 102, 136))
    start_x = 43
    start_y = y + 26
    for idx, char in enumerate(characters):
        col = idx % cols
        row = idx // cols
        _draw_profile_avatar(img, draw, char, start_x + col * 123, start_y + row * 145, updated)
    footer_y = y + list_h
    draw.rectangle((16, footer_y, width - 16, footer_y + footer_h), fill=(0, 0, 0, 126))
    draw.ellipse((43, footer_y + 21, 56, footer_y + 34), fill=(144, 232, 0))
    _shadow_text(draw, (63, footer_y + 14), "本次更新角色" if updated else "已缓存角色", (255, 255, 255), FONT_PROFILE_LABEL)
    serv = f"当前更新服务：{_source_display_name(result.source)}"
    sb = draw.textbbox((0, 0), serv, font=FONT_PROFILE_LABEL)
    _shadow_text(draw, (width - 48 - (sb[2] - sb[0]), footer_y + 14), serv, (255, 255, 255), FONT_PROFILE_LABEL)
    from .version import PLUGIN_VERSION
    credit = f"Created By Miao-Plugin & gscore_miao-plugin {PLUGIN_VERSION} By MeowAndy"
    cb = draw.textbbox((0, 0), credit, font=FONT_PROFILE_CREDIT)
    _shadow_text(draw, ((width - (cb[2] - cb[0])) // 2, height - 42), credit, (255, 255, 255), FONT_PROFILE_CREDIT)
    return img


def _char_name(char: Dict[str, Any]) -> str:
    if char.get("game") == "sr":
        name = char.get("name") or char.get("avatar_name")
        if name and not str(name).isdigit():
            return str(name)
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
    base = "meta-sr/character" if char.get("game") == "sr" else "meta-gs/character"
    folder, data = _find_meta_by_id(base, str(avatar_id or ""))
    return str(data.get("name") or folder or "未知角色")


def _char_match_text(char: Dict[str, Any]) -> str:
    parts = [
        _char_name(char),
        str(char.get("name") or ""),
        str(char.get("avatar_name") or ""),
        str(char.get("avatar_id") or char.get("avatarId") or ""),
    ]
    return " ".join(x for x in parts if x).lower()


def _similar_char_names(query: str, characters: Iterable[Dict[str, Any]], limit: int = 3) -> List[str]:
    q = (query or "").strip().lower()
    if not q:
        return []
    scored: List[Tuple[float, str]] = []
    seen: set[str] = set()
    for char in characters:
        name = _char_name(char)
        if not name or name in seen:
            continue
        seen.add(name)
        lower = name.lower()
        score = SequenceMatcher(None, q, lower).ratio()
        if q[:1] and lower[:1] == q[:1]:
            score += 0.12
        if q[-1:] and lower[-1:] == q[-1:]:
            score += 0.08
        if q in lower or lower in q:
            score += 0.2
        scored.append((score, name))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [name for score, name in scored[:limit] if score >= 0.35]


def _raise_unknown_character(result: PanelResult, character_query: str, characters: List[Dict[str, Any]]) -> None:
    available = "、".join(_char_name(c) for c in characters[:8]) or "无角色"
    suggestions = _similar_char_names(character_query, characters)
    suggestion_text = f"\n是不是想查：{'、'.join(suggestions)}？" if suggestions else ""
    example = "喵喵崩铁黄泉面板" if result.game == "sr" else "喵喵原神基尼奇面板"
    raise ValueError(
        f"角色名称好像打错啦：{character_query}。{suggestion_text}\n"
        f"请检查角色名或别名后重试，例如：{example}。\n"
        f"当前 UID {result.uid} 可见角色：{available}"
    )


def _char_meta(name: str, game: str = "gs") -> Dict[str, Any]:
    return _load_json(_resource_path("meta-sr" if game == "sr" else "meta-gs", "character", name, "data.json"))


def _character_weapon_type(name: str, game: str = "gs") -> str:
    meta = _char_meta(name, game)
    weapon = str(meta.get("weapon") or "sword").strip().lower()
    return weapon if weapon in {"sword", "claymore", "polearm", "bow", "catalyst"} else "sword"


def _talent_icon_path(name: str, key: str, game: str = "gs") -> Path | None:
    if key == "a":
        fallback = _resource_path("common", "item", f"atk-{_character_weapon_type(name, game)}.webp")
        if fallback:
            return fallback

    meta = _char_meta(name, game)
    talent_cons = meta.get("talentCons") or {}
    cons_idx = 0
    if isinstance(talent_cons, dict):
        try:
            cons_idx = int(talent_cons.get(key) or 0)
        except (TypeError, ValueError):
            cons_idx = 0
    if cons_idx > 0:
        cons_path = _resource_path("meta-sr" if game == "sr" else "meta-gs", "character", name, "icons", f"cons-{cons_idx}.webp")
        if cons_path:
            return cons_path
    return _resource_path("meta-sr" if game == "sr" else "meta-gs", "character", name, "imgs" if game == "sr" else "icons", f"talent-{key}.webp")


def _cons_icon_path(name: str, idx: int, game: str = "gs") -> Path | None:
    base = "meta-sr" if game == "sr" else "meta-gs"
    folders = ("imgs", "icons") if game == "sr" else ("icons", "imgs")
    for folder in folders:
        path = _resource_path(base, "character", name, folder, f"cons-{idx}.webp")
        if path:
            return path
    if game != "sr":
        return None
    meta = _char_meta(name, game)
    talent_cons = meta.get("talentCons") or {}
    if isinstance(talent_cons, dict):
        mapped = talent_cons.get(str(idx))
        if mapped:
            path = _resource_path(base, "character", name, "imgs", f"talent-{mapped}.webp")
            if path:
                return path
    return None


def _char_image(name: str, kind: str = "splash", game: str = "gs") -> Path | None:
    for file in (f"{kind}.webp", f"{kind}0.webp", f"{kind}.png"):
        path = _resource_path("meta-sr" if game == "sr" else "meta-gs", "character", name, "imgs", file)
        if path:
            return path
    return None


def _char_face_path(name: str, game: str = "gs") -> Path | None:
    for file in ("face-q.webp", "face.webp", "card.webp", "side.webp"):
        path = _resource_path("meta-sr" if game == "sr" else "meta-gs", "character", name, "imgs", file)
        if path:
            return path
    return None


def _char_star(char: Dict[str, Any]) -> int:
    for key in ("rarity", "star", "rank"):
        try:
            value = int(char.get(key) or 0)
            if value:
                return value
        except (TypeError, ValueError):
            pass
    data = _char_meta(_char_name(char), char.get("game", "gs"))
    try:
        return int(data.get("star") or data.get("rarity") or 5)
    except (TypeError, ValueError):
        return 5


def _source_display_name(source: str) -> str:
    text = str(source or "").strip()
    key = text.lower()
    if key in {"minigg", "mgg", "minigg-api", "minigg_api"}:
        return "MiniGG-Api"
    if key in {"miao", "miao-api", "miao_api"}:
        return "Miao-Api"
    if key in {"enka", "enka-api", "enka_api"}:
        return "Enka-Api"
    if key in {"mys", "mihoyo", "hoyolab", "米游社"}:
        return "米游社"
    return text or "MiniGG-Api"


def _find_named_resource(base: str, name: str, filename: str) -> Path | None:
    if not name or name.isdigit():
        return None
    target = str(name).strip()
    for resource_dir in _resource_dirs():
        root_dir = resource_dir / Path(base)
        if not root_dir.exists():
            continue
        direct = root_dir / target / filename
        if direct.exists():
            return direct
        for path in root_dir.rglob(filename):
            if path.parent.name == target:
                return path
    return None


def _weapon_game(weapon: Dict[str, Any]) -> str:
    game = str(weapon.get("game") or "").lower()
    if game in {"sr", "starrail", "hkrpg"}:
        return "sr"
    item_id = str(weapon.get("item_id") or weapon.get("itemId") or weapon.get("id") or weapon.get("tid") or "")
    if item_id.startswith("2") or weapon.get("tid"):
        return "sr"
    return "gs"


def _weapon_meta(weapon: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    item_id = str(weapon.get("item_id") or weapon.get("itemId") or weapon.get("id") or weapon.get("tid") or "")
    base = "meta-sr/weapon" if _weapon_game(weapon) == "sr" else "meta-gs/weapon"
    return _find_meta_by_id(base, item_id)


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
    base = "meta-sr/weapon" if _weapon_game(weapon) == "sr" else "meta-gs/weapon"
    path = _find_named_resource(base, name, "icon.webp")
    if path:
        return path
    folder, _ = _weapon_meta(weapon)
    return _find_named_resource(base, folder, "icon.webp")


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
    by_sr_id = _find_sr_artifact_by_item_id(str(rel.get("item_id") or rel.get("itemId") or rel.get("id") or rel.get("tid") or ""))
    if by_sr_id.get("set_name"):
        return str(by_sr_id["set_name"])
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
    by_sr_id = _find_sr_artifact_by_item_id(str(rel.get("item_id") or rel.get("itemId") or rel.get("id") or rel.get("tid") or ""))
    if by_sr_id.get("idx"):
        return int(by_sr_id["idx"])
    try:
        num = int(pos)
        if 1 <= num <= 6:
            return num
    except (TypeError, ValueError):
        pass
    return fallback_idx + 1


def _artifact_icon(rel: Dict[str, Any], fallback_idx: int) -> Path | None:
    is_sr = rel.get("game") == "sr" or fallback_idx >= 5
    if is_sr:
        by_sr_id = _find_sr_artifact_by_item_id(str(rel.get("item_id") or rel.get("itemId") or rel.get("id") or rel.get("tid") or ""))
        set_name = str(by_sr_id.get("set_name") or _artifact_set_name(rel))
        idx = int(by_sr_id.get("idx") or _artifact_pos_index(rel, fallback_idx))
        if set_name:
            for name in (f"arti-{idx - 1}.webp", f"arti-{idx}.webp", f"{idx}.webp"):
                path = _resource_path("meta-sr", "artifact", set_name, name)
                if path:
                    return path
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


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    try:
        box = draw.textbbox((0, 0), text, font=font)
        return box[2] - box[0]
    except Exception:
        return len(str(text)) * 12


def _fit_font_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, fonts: List[ImageFont.ImageFont], min_chars: int = 4) -> Tuple[str, ImageFont.ImageFont]:
    text = str(text or "")
    for font in fonts:
        if _text_width(draw, text, font) <= max_width:
            return text, font
    font = fonts[-1]
    ret = text
    while len(ret) > min_chars and _text_width(draw, ret + "…", font) > max_width:
        ret = ret[:-1]
    return (ret + "…" if ret != text else ret), font


def _wrap_text_by_width(draw: ImageDraw.ImageDraw, text: str, max_width: int, font: ImageFont.ImageFont, max_lines: int = 2) -> List[str]:
    text = str(text or "").strip()
    if not text:
        return []
    lines: List[str] = []
    current = ""
    for ch in text:
        test = current + ch
        if current and _text_width(draw, test, font) > max_width:
            lines.append(current)
            current = ch
            if len(lines) >= max_lines:
                break
        else:
            current = test
    if len(lines) < max_lines and current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if lines and "".join(lines) != text:
        while lines[-1] and _text_width(draw, lines[-1] + "…", font) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines


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
        value = value.get("appendPropId") or value.get("prop_id") or value.get("key") or value.get("field") or value.get("mainPropId") or value.get("name") or value.get("title") or value.get("type")
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
    raw = value.get("display") or value.get("value_str") or value.get("valueStr") or value.get("formatted") or value.get("value") or value.get("val") or value.get("statValue") or value.get("base") or value.get("final")
    if raw is None or raw == "":
        return ""
    raw_text = str(raw).strip()
    if raw_text.endswith("%"):
        return raw_text
    try:
        num = float(raw)
    except (TypeError, ValueError):
        return str(raw)
    key = str(value.get("appendPropId") or value.get("prop_id") or value.get("key") or value.get("field") or value.get("mainPropId") or value.get("type") or value.get("name") or "").upper()
    suffix = "%" if any(x in key for x in ["PERCENT", "CRITICAL", "CRIT", "HURT", "CHARGE", "HEAL", "CPCT", "CDMG", "RECHARGE", "DMG", "DAMAGE", "EFFECT", "EFF", "BREAK", "STANCE"]) or any(x in key for x in ["暴击", "伤害", "击破", "效果", "充能", "治疗"]) else ""
    if suffix and 0 < abs(num) < 1:
        num *= 100
    if abs(num - round(num)) < 0.01:
        return f"{round(num)}{suffix}"
    return f"{num:.1f}{suffix}"


def _artifact_prop_score_text(prop: Any, weight: Dict[str, float], game: str = "gs") -> str:
    if not isinstance(prop, dict):
        return ""
    try:
        from .artifact_service import _prop_key, _prop_score
        key = _prop_key(prop.get("appendPropId") or prop.get("prop_id") or prop.get("key") or prop.get("field") or prop.get("type") or prop.get("mainPropId") or prop.get("name"))
        score = prop.get("score")
        if score in (None, ""):
            from .artifact_service import MAX_SUB_VALUE, SR_MAX_SUB_VALUE
            score = _prop_score(prop, weight, max_values=SR_MAX_SUB_VALUE if game == "sr" else MAX_SUB_VALUE)
        score_num = float(score)
        if not key or weight.get(key, 0) <= 0:
            score_num = 0.0
        return f"+{max(score_num, 0.0):.1f}分"
    except Exception:
        return "+0.0分"


def _artifact_prop_parts(prop: Any, weight: Dict[str, float] | None = None, game: str = "gs") -> Tuple[str, str]:
    if not isinstance(prop, dict):
        return _prop_name(prop), ""
    pn = _prop_name(prop)
    pv = _prop_value(prop)
    left = f"{pn}+{pv}" if pv else pn
    score = _artifact_prop_score_text(prop, weight or {}, game) if weight else ""
    return left, score.strip()


def _artifact_prop_line(prop: Any, weight: Dict[str, float] | None = None, game: str = "gs") -> str:
    if isinstance(prop, dict):
        left, score = _artifact_prop_parts(prop, weight, game)
        return f"{left} {score}" if score else left
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

    splash = _open_image(_char_image(name, "splash", result.game), (760, 520), contain=True)
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
    is_sr = result.game == "sr"
    x, y, w, h = 25, 392, 550, 196
    _rounded_r(draw, (x, y, x + w, y + h), 14, (31, 30, 34), (221, 191, 135), 2)
    name = _char_name(char)
    meta = _char_meta(name, result.game)
    cons = char.get("constellation")
    level = _safe(char.get("level"), "?")
    _text(draw, (x + 20, y + 16), name, (245, 228, 183), FONT_TITLE)
    _text(draw, (x + 22, y + 68), f"UID {result.uid} - Lv.{level}", (232, 232, 232), FONT_TEXT)
    if cons is not None:
        _rounded_r(draw, (x + 300, y + 68, x + 360, y + 96), 8, (150, 48, 42))
        _text(draw, (x + 315, y + 72), f"{cons}{'魂' if is_sr else '命'}", (255, 245, 225), FONT_SMALL)

    skills = list(char.get("skill_levels") or [])[:3]
    labels = ["普攻", "战技", "终结"] if is_sr else ["普攻", "战技", "爆发"]
    for idx, label in enumerate(labels):
        lv = skills[idx] if idx < len(skills) else "-"
        cx = x + 28 + idx * 82
        cy = y + 112
        draw.ellipse((cx, cy, cx + 52, cy + 52), fill=(42, 43, 48), outline=(214, 183, 112), width=2)
        icon_key = ["a", "e", "q"][idx]
        icon_path = _talent_icon_path(name, icon_key, result.game)
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
        row = idx // 3
        col = idx % 3
        size = 40 if is_sr else 36
        cx = x + 324 + col * 58
        cy = y + 108 + row * 42
        icon_path = _cons_icon_path(name, idx + 1, result.game)
        icon = _open_image(icon_path, (size, size), contain=True)
        active = cons is not None and idx < int(cons)
        draw.ellipse((cx, cy, cx + size, cy + size), fill=(42, 43, 48), outline=(245, 230, 190), width=2 if active else 1)
        if icon:
            if not active:
                icon.putalpha(82)
            _paste(img, icon, (cx, cy))
        else:
            fill = (221, 191, 135) if active else (75, 75, 78)
            draw.ellipse((cx + 4, cy + 4, cx + size - 4, cy + size - 4), fill=fill)
    return y + h + 16


def _draw_section_title(draw: ImageDraw.ImageDraw, y: int, title: str, right: str = "") -> int:
    _rounded_r(draw, (25, y, 575, y + 44), 8, (37, 37, 41), (72, 66, 55), 1)
    _text(draw, (45, y + 10), title, (211, 188, 142), FONT_TEXT)
    if right:
        _text(draw, (385, y + 12), right, (160, 160, 160), FONT_TINY)
    return y + 54


def _draw_attrs(draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    props = char.get("fight_props") or {}
    is_sr = char.get("game") == "sr"
    if is_sr:
        attrs = [
            ("生命值", _fmt_attr_value("生命值", _first_prop(props, "生命值"))),
            ("攻击力", _fmt_attr_value("攻击力", _first_prop(props, "攻击力"))),
            ("防御力", _fmt_attr_value("防御力", _first_prop(props, "防御力"))),
            ("速度", _fmt_attr_value("速度", _first_prop(props, "速度"))),
            ("暴击率", _fmt_attr_value("暴击率", _first_prop(props, "暴击率"))),
            ("暴击伤害", _fmt_attr_value("暴击伤害", _first_prop(props, "暴击伤害"))),
            ("伤害加成", _fmt_attr_value("伤害加成", _first_prop(props, "伤害加成"))),
            ("击破特攻", _fmt_attr_value("击破特攻", _first_prop(props, "击破特攻"))),
            ("效果命中", _fmt_attr_value("效果命中", _first_prop(props, "效果命中"))),
            ("效果抵抗", _fmt_attr_value("效果抵抗", _first_prop(props, "效果抵抗"))),
        ]
    else:
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
    return y + ((len(attrs) + 1) // 2) * row_h + 16


def _draw_weapon(img: Image.Image, draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    is_sr = char.get("game") == "sr"
    weapon = char.get("weapon") or {}
    if not isinstance(weapon, dict):
        weapon = {}
    if is_sr:
        weapon = dict(weapon)
        weapon.setdefault("game", "sr")
    rarity = int(weapon.get("rarity") or 5)
    y = _draw_section_title(draw, y, "光锥" if is_sr else "武器")
    _rounded_r(draw, (25, y, 575, y + 144), 12, (38, 37, 42), (92, 81, 62), 1)
    name = _weapon_name(weapon)
    draw.rounded_rectangle((42, y + 18, 118, y + 94), radius=12, fill=_star_color(rarity))
    icon = _open_image(_weapon_icon(weapon), (72, 72), contain=True)
    if icon:
        _paste(img, icon, (44, y + 20))
    else:
        _text(draw, (66, y + 40), "锥" if is_sr else "武", (255, 247, 230), FONT_CARD_TITLE)
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


def _reliq_label(index: int, is_sr: bool = False) -> str:
    if is_sr:
        labels = ["头部", "手部", "躯干", "脚部", "位面球", "连结绳"]
        return labels[index] if index < len(labels) else "遗器"
    return ["生之花", "死之羽", "时之沙", "空之杯", "理之冠"][index] if index < 5 else "圣遗物"


def _draw_artifacts(img: Image.Image, draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    from .artifact_service import (_weight_for_char, artifact_rank,
                                   character_artifact_score, score_reliquary)

    is_sr = char.get("game") == "sr"
    max_count = 6 if is_sr else 5
    reliqs = [r for r in (char.get("reliquaries") or []) if isinstance(r, dict)][:max_count]
    _, weight = _weight_for_char(char)
    total, scores, title = character_artifact_score(char)
    rank_score = total / max_count if is_sr and total > 0 else total
    y = _draw_section_title(draw, y, "遗器" if is_sr else "圣遗物", f"{len(reliqs)}/{max_count}")
    _rounded_r(draw, (25, y, 575, y + 96), 12, (42, 39, 42), (92, 81, 62), 1)
    _text(draw, (45, y + 15), "遗器总分" if is_sr else "圣遗物总分", (210, 210, 210), FONT_SMALL)
    _text(draw, (170, y + 9), f"{total}", (255, 232, 170), FONT_CARD_TITLE)
    _text(draw, (278, y + 15), "评级", (210, 210, 210), FONT_SMALL)
    _text(draw, (330, y + 9), artifact_rank(rank_score), (144, 232, 74), FONT_CARD_TITLE)
    _text(draw, (45, y + 48), f"评分规则：{_fit_text(title, 40)}", (170, 164, 145), FONT_TINY)
    useful = [k for k, v in weight.items() if v > 0]
    names = {"atk": "攻击", "hp": "生命", "def": "防御", "speed": "速度", "cpct": "暴率", "cdmg": "爆伤", "dmg": "增伤", "stance": "击破", "effPct": "命中", "effDef": "抵抗", "recharge": "充能", "heal": "治疗"}
    _text(draw, (45, y + 70), "有效词条：" + " / ".join(names.get(k, k) for k in useful[:8]), (188, 196, 210), FONT_TINY)
    y += 114
    card_w, card_h = 176, 238
    relic_name_font = _font(13, False, "HYWH-65W.ttf")
    relic_line_fonts = [_font(13, False, "HYWH-65W.ttf"), _font(12, False, "HYWH-65W.ttf"), _font(11, False, "HYWH-65W.ttf")]
    relic_score_fonts = [_font(12, False, "HYWH-65W.ttf"), _font(11, False, "HYWH-65W.ttf")]
    for idx in range(max_count):
        col = idx % 3
        row = idx // 3
        x = 25 + col * 187
        yy = y + row * 250
        rel = reliqs[idx] if idx < len(reliqs) else {}
        if is_sr and rel:
            rel = dict(rel)
            rel.setdefault("game", "sr")
        level = _artifact_level(rel.get("level"))
        rarity = int(rel.get("rarity") or 5)
        _rounded_r(draw, (x, yy, x + card_w, yy + card_h), 12, (42, 39, 42), _star_color(rarity), 1)
        draw.rounded_rectangle((x + 12, yy + 12, x + 58, yy + 58), radius=10, fill=_star_color(rarity))
        icon = _open_image(_artifact_icon(rel, idx), (46, 46), contain=True)
        if icon:
            _paste(img, icon, (x + 12, yy + 12))
        else:
            _text(draw, (x + 24, yy + 23), (SR_RELIC_SLOT_ICONS if is_sr else ARTIFACT_SLOT_ICONS)[idx], (255, 247, 230), FONT_SMALL)
        title = _artifact_name(rel, _reliq_label(idx, is_sr))
        title_lines = _wrap_text_by_width(draw, title, 96, relic_name_font, 2)
        for t_idx, title_line in enumerate(title_lines[:2]):
            _text(draw, (x + 68, yy + 12 + t_idx * 17), title_line, (245, 228, 183), relic_name_font)
        main = _prop_name(rel.get("main_prop") or rel.get("main"))
        main_value = _prop_value(rel.get("main_prop") or rel.get("main"))
        main_line, main_font = _fit_font_text(draw, f"{main}+{main_value}" if main_value else main, 148, relic_line_fonts, 5)
        _text(draw, (x + 14, yy + 66), main_line, (210, 210, 210), main_font)
        score = scores[idx] if idx < len(scores) else (score_reliquary(rel, weight, idx) if rel else 0)
        score_text = f"{score:.1f} {artifact_rank(score)}" if rel else "-"
        _text(draw, (x + 14, yy + 88), f"+{level}", (255, 232, 170), relic_line_fonts[0])
        score_fit, score_font = _fit_font_text(draw, score_text, 94, relic_line_fonts, 3)
        _text(draw, (x + card_w - 14 - _text_width(draw, score_fit, score_font), yy + 88), score_fit, (255, 232, 170), score_font)
        if rel:
            for s_idx, prop in enumerate((rel.get("sub_props") or [])[:4]):
                left, score_part = _artifact_prop_parts(prop, weight, "sr" if is_sr else "gs")
                line_y = yy + 116 + s_idx * 27
                left_text, left_font = _fit_font_text(draw, left, 108 if score_part else 148, relic_line_fonts, 5)
                _text(draw, (x + 14, line_y), left_text, (188, 196, 210), left_font)
                if score_part:
                    score_text_fit, score_font = _fit_font_text(draw, score_part, 58, relic_score_fonts, 3)
                    _text(draw, (x + card_w - 14 - _text_width(draw, score_text_fit, score_font), line_y), score_text_fit, (255, 167, 72), score_font)
    return y + 512


def _draw_artifact_detail(img: Image.Image, draw: ImageDraw.ImageDraw, y: int, char: Dict[str, Any]) -> int:
    from .artifact_service import (_weight_for_char, artifact_rank,
                                   character_artifact_score, score_reliquary)

    title, weight = _weight_for_char(char)
    is_sr = char.get("game") == "sr"
    max_count = 6 if is_sr else 5
    reliqs = [r for r in (char.get("reliquaries") or []) if isinstance(r, dict)][:max_count]
    total, scores, _ = character_artifact_score(char)
    rank_score = total / max_count if is_sr and total > 0 else total
    y = _draw_section_title(draw, y, "遗器评分详情" if is_sr else "圣遗物评分详情", f"{total} 分 [{artifact_rank(rank_score)}]")
    _text(draw, (38, y), f"评分规则：{title}", (210, 200, 176), FONT_TINY)
    y += 26
    for idx in range(max_count):
        rel = reliqs[idx] if idx < len(reliqs) else {}
        if is_sr and rel:
            rel = dict(rel)
            rel.setdefault("game", "sr")
        score = scores[idx] if idx < len(scores) else (score_reliquary(rel, weight, idx) if rel else 0)
        x, h = 25, 112
        _rounded_r(draw, (x, y, 575, y + h), 12, (42, 39, 42), _star_color(int(rel.get("rarity") or 5)), 1)
        icon = _open_image(_artifact_icon(rel, idx), (66, 66), contain=True)
        draw.rounded_rectangle((x + 14, y + 20, x + 80, y + 86), radius=12, fill=_star_color(int(rel.get("rarity") or 5)))
        if icon:
            _paste(img, icon, (x + 14, y + 20))
        else:
            _text(draw, (x + 35, y + 39), (SR_RELIC_SLOT_ICONS if is_sr else ARTIFACT_SLOT_ICONS)[idx], (255, 247, 230), FONT_TEXT)
        name = _artifact_name(rel, _reliq_label(idx, is_sr))
        main_prop = rel.get("main_prop") or rel.get("main")
        main = _prop_name(main_prop)
        main_value = _prop_value(main_prop)
        level = _artifact_level(rel.get("level"))
        name_text, name_font = _fit_font_text(draw, name, 330, [FONT_SMALL, FONT_TINY, _font(16)], 8)
        _text(draw, (x + 96, y + 16), name_text, (245, 228, 183), name_font)
        main_line = f"{_reliq_label(idx, is_sr)}  +{level}  主词条：{main}+{main_value}" if main_value else f"{_reliq_label(idx, is_sr)}  +{level}  主词条：{main}"
        main_line, main_font = _fit_font_text(draw, main_line, 340, [FONT_TINY, _font(16), _font(15)], 8)
        _text(draw, (x + 96, y + 44), main_line, (218, 218, 218), main_font)
        detail_props = list((rel.get("sub_props") or [])[:4])
        if detail_props:
            detail_left_fonts = [_font(13, False, "HYWH-65W.ttf"), _font(12, False, "HYWH-65W.ttf"), _font(11, False, "HYWH-65W.ttf")]
            detail_score_fonts = [_font(12, False, "HYWH-65W.ttf"), _font(11, False, "HYWH-65W.ttf")]
            for s_idx, prop in enumerate(detail_props):
                left, score_part = _artifact_prop_parts(prop, weight, "sr" if is_sr else "gs")
                px = x + 96 + (s_idx % 2) * 178
                py = y + 72 + (s_idx // 2) * 19
                left_text, left_font = _fit_font_text(draw, left, 118 if score_part else 160, detail_left_fonts, 5)
                _text(draw, (px, py), left_text, (188, 196, 210), left_font)
                if score_part:
                    score_right = x + 264 if s_idx % 2 == 0 else x + 442
                    score_text_fit, score_font = _fit_font_text(draw, score_part, 56, detail_score_fonts, 3)
                    _text(draw, (score_right - _text_width(draw, score_text_fit, score_font), py), score_text_fit, (255, 167, 72), score_font)
        else:
            _text(draw, (x + 96, y + 72), "无副词条", (188, 196, 210), FONT_TINY)
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


def _iter_cards(cards: Iterable[Dict[str, Any]], game: str = "gs") -> Iterable[Dict[str, Any]]:
    for card in cards:
        if not isinstance(card, dict):
            continue
        item = dict(card)
        item.setdefault("game", game)
        yield item


def _crop_panel_canvas(img: Image.Image, content_bottom: int, footer: str) -> Image.Image:
    final_height = max(content_bottom + 74, 760)
    final_height = min(final_height, img.height)
    cropped = img.crop((0, 0, img.width, final_height))
    draw = ImageDraw.Draw(cropped)
    _text(draw, (30, final_height - 38), footer, (150, 145, 132), FONT_TINY)
    return cropped


async def render_panel_list_image(result: PanelResult, updated: bool = False) -> bytes:
    characters = list(_iter_cards(result.characters or result.avatars or [], result.game))[:32]
    img = _draw_profile_list_image(result, characters, updated)
    return await convert_img(img)


async def render_panel_image(result: PanelResult) -> bytes:
    characters = list(_iter_cards((result.characters or [])[:8], result.game))
    if len(characters) == 1:
        width = 600
        height = 1880
        img = Image.new("RGBA", (width, height), (22, 23, 27, 255))
        draw = ImageDraw.Draw(img)
        bottom = _draw_miao_profile(img, draw, result, characters[0], width, height)
        img = _crop_panel_canvas(img, bottom, "Created by gscore_miao-plugin · layout inspired by miao-plugin")
        return await convert_img(img)

    return await render_panel_list_image(result, False)


async def render_single_panel_image(result: PanelResult, character_query: str = "") -> bytes:
    characters = list(_iter_cards(result.characters or [], result.game))
    if character_query:
        q = character_query.strip().lower()
        resolved = q
        try:
            from .alias_data import resolve_alias

            resolved = (resolve_alias(character_query, game=result.game) or character_query).strip().lower()
        except Exception:
            pass
        filtered = [
            c for c in characters
            if q in _char_match_text(c) or resolved in _char_match_text(c)
        ]
        if not filtered:
            _raise_unknown_character(result, character_query, characters)
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
            game=result.game,
        )
    return await render_panel_image(result)


async def render_artifact_image(result: PanelResult, character_query: str = "") -> bytes:
    characters = list(_iter_cards(result.characters or [], result.game))
    if character_query:
        q = character_query.strip().lower()
        try:
            from .alias_data import resolve_alias

            resolved = (resolve_alias(character_query, game=result.game) or character_query).strip().lower()
        except Exception:
            resolved = q
        characters = [c for c in characters if q in _char_match_text(c) or resolved in _char_match_text(c)]
        if not characters:
            _raise_unknown_character(result, character_query, list(_iter_cards(result.characters or [], result.game)))
    if not characters:
        raise ValueError("当前数据源没有返回可渲染的角色详情")
    char = characters[0]
    width = 600
    height = 1640
    img = Image.new("RGBA", (width, height), (22, 23, 27, 255))
    draw = ImageDraw.Draw(img)
    _draw_miao_header(img, draw, result, char, width)
    y = _draw_basic_panel(img, draw, result, char)
    y = _draw_artifact_detail(img, draw, y, char)
    img = _crop_panel_canvas(img, y, "Created by gscore_miao-plugin · artifact detail inspired by miao-plugin")
    return await convert_img(img)


async def render_artifact_list_image(result: PanelResult) -> bytes:
    from .artifact_service import artifact_rank, character_artifact_score

    chars = list(_iter_cards(result.characters or [], result.game))
    rows = []
    for char in chars:
        total, scores, title = character_artifact_score(char)
        rows.append((total, char, scores, title))
    rows.sort(key=lambda x: x[0], reverse=True)
    width = 900
    height = 170 + max(1, len(rows[:16])) * 74 + 80
    img = _gradient_bg(width, height).convert("RGBA")
    draw = ImageDraw.Draw(img)
    is_sr = result.game == "sr"
    _text(draw, (52, 42), "喵喵崩铁遗器列表" if is_sr else "喵喵原神圣遗物列表", (255, 247, 220), FONT_TITLE)
    _text(draw, (56, 100), f"UID {result.uid} · 数据源 {result.source} · 按总评分排序", (199, 210, 230), FONT_SMALL)
    if not rows:
        _rounded_r(draw, (52, 160, width - 52, 280), 14, (31, 39, 61), (70, 83, 120), 1)
        _text(draw, (82, 200), "当前数据源没有返回遗器详情。" if is_sr else "当前数据源没有返回圣遗物详情。", (248, 244, 232), FONT_TEXT)
    for idx, (total, char, scores, title) in enumerate(rows[:16], start=1):
        y = 160 + (idx - 1) * 74
        _rounded_r(draw, (52, y, width - 52, y + 60), 12, (31, 39, 61), (70, 83, 120), 1)
        _text(draw, (72, y + 16), f"{idx}", (255, 232, 170), FONT_TEXT)
        _text(draw, (120, y + 12), _char_name(char), (248, 244, 232), FONT_TEXT)
        _text(draw, (300, y + 14), " / ".join(f"{x:.1f}" for x in scores[:6 if is_sr else 5]) or ("无遗器" if is_sr else "无圣遗物"), (190, 201, 221), FONT_TINY)
        rank_score = total / (6 if is_sr else 5) if is_sr and total > 0 else total
        _text(draw, (650, y + 12), f"{total:.1f} [{artifact_rank(rank_score)}]", (144, 232, 74), FONT_TEXT)
        _text(draw, (120, y + 38), _fit_text(title, 28), (160, 171, 190), FONT_TINY)
    _text(draw, (54, height - 42), "评分权重使用 gscore_miao-plugin 内置适配规则", (145, 158, 186), FONT_TINY)
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

    _text(draw, (68, 54), title or "喵喵原神帮助", (255, 247, 222), FONT_HELP_TITLE)
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
        _text(draw, (84, y), f"- {group.get('group') or '命令'}", (255, 232, 174), FONT_HELP_GROUP)
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


async def render_calendar_image(cal_data: Dict[str, Any]) -> bytes:
    items = list(cal_data.get("items") or [])
    game = str(cal_data.get("game") or "sr")
    page = int(cal_data.get("page") or 1)
    total_pages = int(cal_data.get("total_pages") or 1)
    total_items = int(cal_data.get("total_items") or len(items))
    title = "喵喵崩铁活动日历" if game == "sr" else "喵喵原神活动日历"
    subtitle = "星穹铁道公告与跃迁日程" if game == "sr" else "原神公告与祈愿日程"
    width = 1080
    row_h = 92
    height = max(720, 230 + max(len(items), 1) * row_h + 90)
    img = _gradient_bg(width, height).convert("RGBA")
    bg = _cover_image(_help_bg_path(), (width, height))
    if bg:
        bg.putalpha(80)
        img.alpha_composite(bg)
    img.alpha_composite(Image.new("RGBA", (width, height), (10, 14, 24, 145)))
    draw = ImageDraw.Draw(img)
    draw.ellipse((width - 360, -180, width + 160, 280), fill=(231, 184, 99, 58))
    draw.ellipse((-220, 120, 320, 660), fill=(88, 123, 190, 42))
    _text(draw, (64, 50), title, (255, 247, 222), FONT_HELP_TITLE)
    _text(draw, (68, 116), subtitle, (220, 228, 244), FONT_SUBTITLE)
    page_info = f"第 {page}/{total_pages} 页 · 共 {total_items} 条"
    _text(draw, (68, 154), f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} · {page_info} · 数据来自米游社公告", (170, 182, 207), FONT_SMALL)

    y = 220
    if not items:
        _rounded_r(draw, (64, y, width - 64, y + 120), 22, (28, 34, 54), (76, 91, 129), 1)
        _text(draw, (96, y + 38), "暂未获取到当前活动日程", (248, 244, 232), FONT_HELP_CMD)
    for item in items:
        _rounded_r(draw, (64, y, width - 64, y + 72), 18, (28, 34, 54), (76, 91, 129), 1)
        status = str(item.get("status") or "-")
        type_name = str(item.get("type") or "活动")
        tag_color = (84, 150, 255) if status == "进行中" else (228, 178, 86) if status == "未开始" else (130, 140, 160)
        _rounded_r(draw, (86, y + 16, 190, y + 54), 12, tag_color, None)
        _text(draw, (106, y + 23), status, (255, 255, 255), FONT_HELP_DESC)
        _text(draw, (214, y + 12), _fit_text(str(item.get("title") or "活动"), 34), (248, 244, 232), FONT_HELP_CMD)
        start = item.get("start")
        end = item.get("end")
        start_text = start.strftime("%m-%d %H:%M") if hasattr(start, "strftime") else str(start or "-")
        end_text = end.strftime("%m-%d %H:%M") if hasattr(end, "strftime") else str(end or "-")
        _text(draw, (216, y + 44), f"{type_name} · {start_text} ~ {end_text}", (185, 197, 220), FONT_HELP_DESC)
        y += row_h
    _text(draw, (64, height - 44), "提示：日历已按页完整输出，列表模式会保留近期已结束条目", (150, 163, 190), FONT_TINY)
    return await convert_img(img)


async def render_calendar_images(cal_data: Dict[str, Any], page_size: int = 12) -> List[bytes]:
    items = list(cal_data.get("items") or [])
    page_size = max(int(page_size or 12), 1)
    pages = [items[i:i + page_size] for i in range(0, len(items), page_size)] or [[]]
    images: List[bytes] = []
    for idx, page_items in enumerate(pages, start=1):
        page_data = {
            **cal_data,
            "items": page_items,
            "page": idx,
            "total_pages": len(pages),
            "total_items": len(items),
        }
        images.append(await render_calendar_image(page_data))
    return images