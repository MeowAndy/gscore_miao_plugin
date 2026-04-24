from typing import Dict, List, TypedDict


class HelpItem(TypedDict):
    cmd: str
    desc: str


class HelpGroup(TypedDict):
    group: str
    items: List[HelpItem]


HELP_GROUPS: List[HelpGroup] = [
    {
        "group": "基础命令",
        "items": [
            {"cmd": "喵喵帮助 / 喵喵菜单", "desc": "查看插件帮助"},
            {"cmd": "喵喵版本", "desc": "查看插件版本"},
            {"cmd": "喵喵更新日志", "desc": "查看最近更新"},
            {"cmd": "喵喵面板 <UID>", "desc": "查询角色面板数据（Miao/Enka/米游社等数据源）"},
        ],
    },
    {
        "group": "设置命令",
        "items": [
            {"cmd": "#喵喵设置", "desc": "查看当前设置"},
            {
                "cmd": "#喵喵设置面板服务 <auto|miao|enka|mgg|hutao|mys>",
                "desc": "设置面板数据来源",
            },
            {"cmd": "#喵喵设置面板图 <开启|关闭>", "desc": "控制自定义面板图"},
            {"cmd": "#喵喵设置组队 <开启|关闭>", "desc": "控制组队伤害计算"},
            {"cmd": "#喵喵设置星级 <开启|关闭>", "desc": "控制角色星级显示"},
            {"cmd": "#喵喵设置逗号 <2-8>", "desc": "设置数字千分位分组"},
            {"cmd": "#喵喵设置历史", "desc": "查看最近设置历史"},
            {"cmd": "#喵喵设置重置", "desc": "恢复默认设置"},
            {"cmd": "#喵喵设置导出", "desc": "导出当前设置 JSON"},
        ],
    },
]
