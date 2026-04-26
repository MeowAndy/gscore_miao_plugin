from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .path import MAIN_PATH

POOL_MAP_GS = {
    "角色": ["301", "400"],
    "武器": ["302"],
    "常驻": ["200"],
    "集录": ["500"],
}
POOL_MAP_SR = {
    "角色": ["11"],
    "光锥": ["12"],
    "常驻": ["1", "2"],
}

FIVE_STAR_GS = {
    "神里绫华", "琴", "迪卢克", "温迪", "可莉", "钟离", "达达利亚", "魈", "甘雨", "阿贝多", "胡桃", "优菈", "枫原万叶", "宵宫", "雷电将军", "珊瑚宫心海", "荒泷一斗", "八重神子", "夜兰", "提纳里", "赛诺", "妮露", "纳西妲", "流浪者", "艾尔海森", "迪希雅", "白术", "林尼", "那维莱特", "莱欧斯利", "芙宁娜", "娜维娅", "闲云", "千织", "阿蕾奇诺", "克洛琳德", "希格雯", "艾梅莉埃", "玛拉妮", "基尼奇", "希诺宁", "恰斯卡", "玛薇卡", "茜特菈莉",
}
FIVE_STAR_SR = {
    "黄泉", "流萤", "卡芙卡", "刃", "丹恒•饮月", "镜流", "符玄", "花火", "知更鸟", "阮•梅", "砂金", "飞霄", "黑天鹅", "银狼", "景元", "希儿", "托帕&账账", "真理医生", "藿藿", "罗刹", "椒丘", "灵砂", "星期日", "大黑塔", "缇宝", "万敌", "遐蝶", "赛飞儿", "风堇", "阿格莱雅", "翡翠", "乱破", "波提欧", "云璃", "姬子", "瓦尔特", "布洛妮娅", "杰帕德", "克拉拉", "彦卿", "白露",
}


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _candidate_roots(game: str, user_id: str, uid: str) -> List[Path]:
    folder = "srJson" if game == "sr" else "gachaJson"
    roots = [
        MAIN_PATH / folder / user_id / uid,
        MAIN_PATH / folder / uid,
        _plugin_root() / "data" / folder / user_id / uid,
        _plugin_root().parent / "miao-plugin" / "data" / folder / user_id / uid,
        Path("E:/gsuid_core/gsuid_core/plugins/miao-plugin/data") / folder / user_id / uid,
    ]
    return list(dict.fromkeys(roots))


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return json.loads(path.read_text(encoding="utf-8-sig"))


def _iter_items(raw: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(raw, dict):
        for key in ("list", "data", "items", "gachaLog"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break
    if not isinstance(raw, list):
        return []
    return [x for x in raw if isinstance(x, dict)]


def _rank(item: Dict[str, Any], game: str) -> int:
    for key in ("rank_type", "rankType", "rank", "star", "rarity"):
        try:
            value = int(item.get(key) or 0)
            if value:
                return value
        except (TypeError, ValueError):
            pass
    name = str(item.get("name") or "")
    if name in (FIVE_STAR_SR if game == "sr" else FIVE_STAR_GS):
        return 5
    return 4 if name else 3


def _item_time(item: Dict[str, Any]) -> str:
    return str(item.get("time") or item.get("gacha_time") or item.get("date") or item.get("created_at") or "")


def _pool_name(pool: str, game: str) -> str:
    pool = str(pool)
    if game == "sr":
        return {"11": "角色跃迁", "12": "光锥跃迁", "1": "常驻跃迁", "2": "新手跃迁"}.get(pool, f"卡池 {pool}")
    return {"301": "角色祈愿", "400": "角色祈愿", "302": "武器祈愿", "200": "常驻祈愿", "500": "集录祈愿"}.get(pool, f"卡池 {pool}")


def _wanted_pools(game: str, query: str) -> Dict[str, List[str]]:
    pool_map = POOL_MAP_SR if game == "sr" else POOL_MAP_GS
    query = query or ""
    if "光锥" in query:
        return {"光锥": pool_map.get("光锥", [])}
    if "武器" in query:
        return {"武器": pool_map.get("武器", [])}
    if "常驻" in query:
        return {"常驻": pool_map.get("常驻", [])}
    if "集录" in query or "混池" in query:
        return {"集录": pool_map.get("集录", [])}
    if "角色" in query or "up" in query.lower():
        return {"角色": pool_map.get("角色", [])}
    return pool_map


def _read_pool_file(root: Path, pool: str) -> List[Dict[str, Any]]:
    paths = [root / f"{pool}.json", root / f"gacha-{pool}.json"]
    for path in paths:
        if path.exists():
            return list(_iter_items(_load_json(path)))
    return []


def _sort_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda x: (_item_time(x), str(x.get("id") or x.get("uid") or "")), reverse=True)


def analyze_gacha(game: str, user_id: str, uid: str, query: str = "") -> Dict[str, Any]:
    game = "sr" if game in {"sr", "starrail", "hkrpg"} else "gs"
    selected = _wanted_pools(game, query)
    roots = _candidate_roots(game, str(user_id or ""), str(uid or ""))
    used_root = next((root for root in roots if root.exists()), None)
    if not used_root:
        return {"ok": False, "game": game, "uid": uid, "message": "未找到本地抽卡记录 JSON", "searched": [str(x) for x in roots]}

    pools: List[Dict[str, Any]] = []
    all_items: List[Dict[str, Any]] = []
    for label, pool_ids in selected.items():
        items: List[Dict[str, Any]] = []
        for pool_id in pool_ids:
            pool_items = _read_pool_file(used_root, pool_id)
            for item in pool_items:
                item = dict(item)
                item["_pool"] = pool_id
                item["_pool_name"] = _pool_name(pool_id, game)
                item["_rank"] = _rank(item, game)
                items.append(item)
        items = _sort_items(items)
        all_items.extend(items)
        five_positions: List[int] = []
        pity = 0
        last_five_pity = 0
        five_items: List[Dict[str, Any]] = []
        four_count = 0
        for item in reversed(items):
            pity += 1
            rank = int(item.get("_rank") or 0)
            if rank >= 5:
                five_positions.append(pity)
                last_five_pity = pity
                five_items.append({**item, "_pity": pity})
                pity = 0
            elif rank == 4:
                four_count += 1
        current_pity = pity
        avg = round(sum(x.get("_pity", 0) for x in five_items) / len(five_items), 1) if five_items else 0
        pools.append(
            {
                "label": label,
                "pool_ids": pool_ids,
                "total": len(items),
                "five": len(five_items),
                "four": four_count,
                "avg_pity": avg,
                "current_pity": current_pity,
                "last_five_pity": last_five_pity,
                "five_items": list(reversed(five_items))[:12],
                "recent": items[:10],
            }
        )
    all_items = _sort_items(all_items)
    by_name = Counter(str(x.get("name") or "未知") for x in all_items if int(x.get("_rank") or 0) >= 5)
    by_pool = defaultdict(int)
    for item in all_items:
        by_pool[str(item.get("_pool_name") or "卡池")] += 1
    return {
        "ok": True,
        "game": game,
        "uid": uid,
        "root": str(used_root),
        "query": query,
        "total": len(all_items),
        "pools": pools,
        "recent": all_items[:16],
        "five_counter": by_name.most_common(10),
        "pool_counter": sorted(by_pool.items()),
    }


def extract_uid(text: str) -> str:
    match = re.search(r"\b\d{9,10}\b", text or "")
    return match.group(0) if match else ""