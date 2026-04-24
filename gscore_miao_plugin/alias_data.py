from __future__ import annotations

from typing import Dict, List

CHARACTER_ALIASES: Dict[str, List[str]] = {
    "神里绫华": ["绫华", "神里", "ayaka"],
    "琴": ["团长", "jean"],
    "丽莎": ["lisa"],
    "芭芭拉": ["内鬼", "barbara"],
    "凯亚": ["kaeya"],
    "迪卢克": ["卢姥爷", "姥爷", "diluc"],
    "雷泽": ["狼崽", "razor"],
    "安柏": ["amber"],
    "温迪": ["卖唱", "风神", "venti"],
    "香菱": ["锅巴", "xiangling"],
    "北斗": ["beidou"],
    "行秋": ["水神", "xingqiu"],
    "魈": ["xiao"],
    "凝光": ["ningguang"],
    "可莉": ["蹦蹦", "klee"],
    "钟离": ["帝君", "岩王爷", "zhongli"],
    "菲谢尔": ["皇女", "fischl"],
    "班尼特": ["班爷", "点赞哥", "bennett"],
    "达达利亚": ["公子", "childe", "tartaglia"],
    "诺艾尔": ["女仆", "noelle"],
    "七七": ["qiqi"],
    "重云": ["chongyun"],
    "甘雨": ["椰羊", "ganyu"],
    "阿贝多": ["albedo"],
    "迪奥娜": ["猫猫", "diona"],
    "莫娜": ["mona"],
    "刻晴": ["牛杂", "keqing"],
    "砂糖": ["sucrose"],
    "辛焱": ["xinyan"],
    "罗莎莉亚": ["修女", "rosaria"],
    "胡桃": ["堂主", "hutao", "hu tao"],
    "枫原万叶": ["万叶", "叶天帝", "kazuha"],
    "烟绯": ["yanfei"],
    "宵宫": ["yoimiya"],
    "托马": ["thoma"],
    "优菈": ["eula"],
    "雷电将军": ["雷神", "影", "将军", "raiden", "ei"],
    "早柚": ["sayu"],
    "珊瑚宫心海": ["心海", "kokomi"],
    "五郎": ["gorou"],
    "九条裟罗": ["九条", "sara"],
    "荒泷一斗": ["一斗", "itto"],
    "八重神子": ["神子", "狐狸", "yae", "miko"],
    "夜兰": ["富婆", "yelan"],
    "久岐忍": ["阿忍", "kuki", "shinobu"],
    "鹿野院平藏": ["平藏", "heizou"],
    "提纳里": ["tighnari"],
    "柯莱": ["collei"],
    "多莉": ["dori"],
    "纳西妲": ["草神", "小草神", "nahida"],
    "妮露": ["nilou"],
    "赛诺": ["cyno"],
    "坎蒂丝": ["candace"],
    "流浪者": ["散兵", "wanderer", "scara"],
    "珐露珊": ["faruzan"],
    "瑶瑶": ["yaoyao"],
    "艾尔海森": ["海哥", "alhaitham"],
    "迪希雅": ["dehya"],
    "米卡": ["mika"],
    "卡维": ["kaveh"],
    "白术": ["baizhu"],
    "琳妮特": ["lynette"],
    "林尼": ["lyney"],
    "菲米尼": ["freminet"],
    "那维莱特": ["龙王", "neuvillette"],
    "莱欧斯利": ["典狱长", "wriothesley"],
    "芙宁娜": ["水神", "芙芙", "furina"],
    "夏洛蒂": ["charlotte"],
    "娜维娅": ["navia"],
    "夏沃蕾": ["chevreuse"],
    "闲云": ["留云", "xianyun"],
    "嘉明": ["gaming"],
    "千织": ["chiori"],
    "阿蕾奇诺": ["仆人", "arlecchino"],
    "克洛琳德": ["clorinde"],
    "希格雯": ["sigewinne"],
    "艾梅莉埃": ["emilie"],
    "玛拉妮": ["mualani"],
    "基尼奇": ["kinich"],
    "希诺宁": ["xilonen"],
    "恰斯卡": ["chasca"],
    "欧洛伦": ["ororon"],
    "玛薇卡": ["火神", "mavuika"],
    "茜特菈莉": ["citlali"],
}


def alias_index() -> Dict[str, str]:
    index: Dict[str, str] = {}
    for name, aliases in CHARACTER_ALIASES.items():
        index[name.lower()] = name
        for alias in aliases:
            index[alias.lower()] = name
    return index


def resolve_alias(query: str) -> str | None:
    q = (query or "").strip().lower()
    if not q:
        return None
    index = alias_index()
    if q in index:
        return index[q]
    for key, name in index.items():
        if q in key or key in q:
            return name
    return None


def render_alias_text(query: str = "") -> str:
    if query:
        name = resolve_alias(query)
        if not name:
            return f"未找到角色别名：{query}"
        aliases = "、".join(CHARACTER_ALIASES.get(name, [])) or "暂无内置别名"
        return f"【喵喵角色别名】\n{query} => {name}\n别名：{aliases}"

    lines = ["【喵喵角色别名】", "当前已内置常用原神角色别名，可用：喵喵角色别名 <角色名/别名>", ""]
    for name in sorted(CHARACTER_ALIASES.keys())[:40]:
        aliases = "、".join(CHARACTER_ALIASES[name][:3])
        lines.append(f"{name}: {aliases}")
    lines.append("……更多角色请直接查询具体别名。")
    return "\n".join(lines)