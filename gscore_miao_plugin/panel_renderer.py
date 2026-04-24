from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from gsuid_core.utils.image.convert import convert_img
from PIL import Image, ImageDraw, ImageFont

from .panel_models import PanelResult

Color = Tuple[int, int, int]


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


FONT_TITLE = _font(48, True)
FONT_SUBTITLE = _font(24)
FONT_CARD_TITLE = _font(28, True)
FONT_TEXT = _font(22)
FONT_SMALL = _font(18)


def _text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: Any, fill: Color, font: ImageFont.ImageFont) -> None:
    draw.text(xy, str(text), fill=fill, font=font)


def _rounded(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], fill: Color, outline: Color | None = None) -> None:
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=2 if outline else 1)


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
        weapon_name = str(weapon.get("name") or "未知武器")
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


async def render_panel_image(result: PanelResult) -> bytes:
    characters = list(_iter_cards((result.characters or [])[:8]))
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