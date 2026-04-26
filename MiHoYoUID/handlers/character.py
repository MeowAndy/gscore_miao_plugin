from __future__ import annotations

import re
from pathlib import Path

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..auth import can_use_plugin
from ..character_service import (delete_custom_image, get_last_image, get_wife,
                                 list_custom_images, list_wives,
                                 pick_character_image, resolve_character_name,
                                 save_remote_image, set_wife)
from ..panel_renderer import (render_character_photo_card,
                              render_image_gallery_card, render_status_card)

sv_character = SV("GsCoreMiao角色图库")


def _game(text: str) -> str:
    return "sr" if text.startswith(("崩铁", "星铁")) or "崩铁" in text or "星铁" in text else "gs"


def _relation(text: str) -> str:
    for word in ("老婆", "老公", "女朋友", "男朋友", "女儿", "儿子"):
        if word in text:
            return word
    return "老婆"


def _url(text: str) -> str:
    match = re.search(r"https?://\S+", text or "")
    return match.group(0) if match else ""


@sv_character.on_regex(r"^(?!更新图像$)(?!更新图片$)(?P<game>原神|崩铁|星铁)?(?P<name>.+?)(卡片|照片|写真|图片|图像)$", block=True)
async def send_character_photo(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    game = _game(getattr(ev, "raw_text", "") or "")
    name = resolve_character_name((data.get("name") or "").replace(data.get("game") or "", ""), game)
    result = pick_character_image(name, game, str(ev.user_id or ""))
    await bot.send(await render_character_photo_card(result))


@sv_character.on_regex(r"^(?P<game>原神|崩铁|星铁)?(?P<rel>老婆|老公|女朋友|男朋友|女儿|儿子)(?P<action>列表|照片|图片|写真)?\s*(?P<name>.*)$", block=True)
async def send_wife(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    text = getattr(ev, "raw_text", "") or ""
    data = ev.regex_dict or {}
    game = _game(text)
    rel = data.get("rel") or _relation(text)
    action = data.get("action") or ""
    name = (data.get("name") or "").strip()
    if action == "列表":
        rows = [f"{x.get('relation')}：{x.get('name')}" for x in list_wives(str(ev.user_id or ""), game)]
        return await bot.send(await render_image_gallery_card("喵喵关系列表", rows, "老婆/老公/家人设置"))
    if name:
        row = set_wife(str(ev.user_id or ""), game, rel, name)
        result = pick_character_image(str(row["name"]), game, str(ev.user_id or ""))
        return await bot.send(await render_character_photo_card(result))
    row = get_wife(str(ev.user_id or ""), game, rel)
    if not row:
        return await bot.send(await render_status_card("喵喵关系设置", [f"还没有设置{rel}。", f"示例：喵喵{rel} 雷电将军"], "角色互动"))
    result = pick_character_image(str(row.get("name") or ""), game, str(ev.user_id or ""))
    await bot.send(await render_character_photo_card(result))


@sv_character.on_regex(r"^(上传|添加)(?P<name>.+?)(照片|写真|图片|图像|面板图)\s*(?P<url>https?://\S+)?$", block=True)
async def upload_character_image(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    raw = getattr(ev, "raw_text", "") or ""
    url = data.get("url") or _url(raw)
    name = resolve_character_name(data.get("name") or "", _game(raw))
    kind = "profile" if "面板图" in raw else "images"
    if not url:
        return await bot.send(await render_status_card("喵喵图片上传", ["请在命令后附带图片 URL。", f"示例：喵喵上传{name}照片 https://.../1.jpg"], "图片管理"))
    try:
        result = await save_remote_image(url, name, kind=kind)
        await bot.send(await render_status_card("喵喵图片上传成功", [f"角色：{name}", f"类型：{'面板图' if kind == 'profile' else '写真'}", f"路径：{result.get('path')}"], "图片管理"))
    except Exception as e:
        await bot.send(await render_status_card("喵喵图片上传失败", [str(e)], "图片管理"))


@sv_character.on_regex(r"^(?P<name>.+?)(面板图列表|照片列表|写真列表|图片列表)$", block=True)
async def list_character_images(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    raw = getattr(ev, "raw_text", "") or ""
    name = resolve_character_name(data.get("name") or "", _game(raw))
    kind = "profile" if "面板图" in raw else "images"
    rows = [str(Path(x).name) for x in list_custom_images(name, kind)]
    await bot.send(await render_image_gallery_card(f"{name}图片列表", rows, "面板图" if kind == "profile" else "自定义写真"))


@sv_character.on_regex(r"^删除(?P<name>.+?)(?P<kind>面板图|照片|写真|图片)(?P<idx>\d+)$", block=True)
async def delete_character_image(bot: Bot, ev: Event):
    if not can_use_plugin(ev):
        return await bot.send("当前配置禁止游客使用，仅管理员可调用该指令")
    data = ev.regex_dict or {}
    raw = getattr(ev, "raw_text", "") or ""
    name = resolve_character_name(data.get("name") or "", _game(raw))
    kind = "profile" if data.get("kind") == "面板图" else "images"
    result = delete_custom_image(name, int(data.get("idx") or 0), kind=kind)
    lines = ["已删除。", f"剩余：{result.get('left', 0)}"] if result.get("ok") else [str(result.get("message"))]
    await bot.send(await render_status_card("喵喵图片删除", lines, "图片管理"))


@sv_character.on_regex(r"^原图$", block=True)
async def send_original_image(bot: Bot, ev: Event):
    item = get_last_image(str(ev.user_id or ""))
    if not item:
        return await bot.send("还没有最近生成的角色图。")
    await bot.send(f"{item.get('name')} 原图：{item.get('path')}")