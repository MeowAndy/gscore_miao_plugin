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
            {"cmd": "喵喵设置uid <UID>", "desc": "绑定 UID，之后面板/伤害/圣遗物可省略 UID"},
            {"cmd": "喵喵登录 <米游社Cookie>", "desc": "保存米游社登录 Cookie，并自动绑定原神 UID"},
            {"cmd": "喵喵签到 [UID]", "desc": "使用已保存 Cookie 执行原神每日签到"},
            {"cmd": "喵喵查看登录 / 喵喵删除登录", "desc": "查看或删除本地米游社登录信息"},
            {"cmd": "喵喵面板列表 [UID]", "desc": "查看公开角色面板列表图"},
            {"cmd": "喵喵更新面板 [UID]", "desc": "重新拉取面板数据并刷新缓存"},
            {"cmd": "喵喵删除面板 / 喵喵解绑UID", "desc": "删除本地绑定 UID"},
            {"cmd": "喵喵面板图 <UID> [角色]", "desc": "查询单角色完整图片面板"},
            {"cmd": "喵喵圣遗物评分 <UID> [角色]", "desc": "查看公开角色圣遗物评分"},
            {"cmd": "喵喵圣遗物列表 [UID]", "desc": "按评分查看公开角色圣遗物列表图"},
            {"cmd": "喵喵伤害计算 <UID> [角色]", "desc": "查看公开角色通用伤害估算"},
            {"cmd": "喵喵雷神面板/圣遗物/伤害 <UID>", "desc": "兼容 miao-plugin 角色指令风格"},
            {"cmd": "喵喵角色别名 <角色/别名>", "desc": "查询角色别名映射"},
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
