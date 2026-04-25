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
            {"cmd": "{prefix}原神帮助 / {prefix}原神菜单", "desc": "查看原神插件帮助"},
            {"cmd": "{prefix}原神版本", "desc": "查看原神插件版本"},
            {"cmd": "{prefix}原神更新日志", "desc": "查看原神插件最近更新"},
            {"cmd": "{prefix}原神面板 <UID>", "desc": "查询原神角色面板数据（Miao/Enka/米游社等数据源）"},
            {"cmd": "{prefix}原神设置uid <UID>", "desc": "绑定原神 UID，之后面板/伤害/圣遗物可省略 UID"},
            {"cmd": "{prefix}登录", "desc": "米游社 App 扫码登录，并自动绑定原神 UID"},
            {"cmd": "{prefix}登录 <米游社Cookie>", "desc": "手动保存米游社登录 Cookie"},
            {"cmd": "{prefix}签到 [UID]", "desc": "使用已保存 Cookie 执行原神与崩铁每日签到"},
            {"cmd": "{prefix}查看登录 / {prefix}删除登录", "desc": "查看或删除本地米游社登录信息"},
            {"cmd": "{prefix}原神面板列表 [UID]", "desc": "查看原神公开角色面板列表图"},
            {"cmd": "{prefix}原神更新面板 [UID]", "desc": "重新拉取原神面板数据并刷新缓存"},
            {"cmd": "{prefix}原神删除面板 / {prefix}原神解绑UID", "desc": "删除本地绑定的原神 UID"},
            {"cmd": "{prefix}原神面板图 <UID> [角色]", "desc": "查询原神单角色完整图片面板"},
            {"cmd": "{prefix}原神圣遗物评分 <UID> [角色]", "desc": "查看原神公开角色圣遗物评分"},
            {"cmd": "{prefix}原神圣遗物列表 [UID]", "desc": "按评分查看原神公开角色圣遗物列表图"},
            {"cmd": "{prefix}原神伤害计算 <UID> [角色]", "desc": "查看原神公开角色通用伤害估算"},
            {"cmd": "{prefix}原神雷神面板/圣遗物/伤害 <UID>", "desc": "兼容 miao-plugin 原神角色指令风格"},
            {"cmd": "{prefix}原神角色别名 <角色/别名>", "desc": "查询原神角色别名映射"},
        ],
    },
    {
        "group": "设置命令",
        "items": [
            {"cmd": "{prefix}原神设置", "desc": "查看当前原神设置"},
            {
                "cmd": "{prefix}原神设置面板服务 <auto|miao|enka|mgg|hutao|mys>",
                "desc": "设置原神面板数据来源",
            },
            {"cmd": "{prefix}原神设置面板图 <开启|关闭>", "desc": "控制原神自定义面板图"},
            {"cmd": "{prefix}原神设置组队 <开启|关闭>", "desc": "控制原神组队伤害计算"},
            {"cmd": "{prefix}原神设置星级 <开启|关闭>", "desc": "控制原神角色星级显示"},
            {"cmd": "{prefix}原神设置逗号 <2-8>", "desc": "设置原神数字千分位分组"},
            {"cmd": "{prefix}原神设置历史", "desc": "查看最近原神设置历史"},
            {"cmd": "{prefix}原神设置重置", "desc": "恢复原神默认设置"},
            {"cmd": "{prefix}原神设置导出", "desc": "导出当前原神设置 JSON"},
        ],
    },
]


STAR_RAIL_HELP_GROUPS: List[HelpGroup] = [
    {
        "group": "基础与账号",
        "items": [
            {"cmd": "{prefix}崩铁帮助 / {prefix}崩铁菜单", "desc": "查看崩坏：星穹铁道功能导航"},
            {"cmd": "{prefix}登录", "desc": "米游社 App 扫码登录，保存原神/崩铁共用 Cookie"},
            {"cmd": "{prefix}登录 <米游社Cookie>", "desc": "手动保存米游社登录 Cookie"},
            {"cmd": "{prefix}签到 [UID]", "desc": "使用已保存 Cookie 执行原神与崩铁每日签到"},
            {"cmd": "{prefix}查看登录 / {prefix}删除登录", "desc": "查看或删除本地米游社登录信息"},
            {"cmd": "{prefix}崩铁设置uid <UID>", "desc": "绑定星铁 UID，面板/遗器/排行可省略 UID（规划）"},
            {"cmd": "{prefix}崩铁版本", "desc": "查看崩铁功能迁移版本（规划）"},
            {"cmd": "{prefix}崩铁日历 / {prefix}崩铁日历列表", "desc": "星穹铁道活动日历，对应 miao-plugin #星铁日历"},
        ],
    },
    {
        "group": "角色面板",
        "items": [
            {"cmd": "{prefix}崩铁面板 [UID]", "desc": "查看已获取面板数据的星铁角色列表"},
            {"cmd": "{prefix}崩铁角色面板 [UID]", "desc": "面板角色列表入口，对齐 #星铁角色面板"},
            {"cmd": "{prefix}崩铁更新面板 [UID]", "desc": "拉取星铁橱窗/公开角色详情并刷新缓存"},
            {"cmd": "{prefix}崩铁全部面板更新 [UID]", "desc": "批量更新星铁面板数据"},
            {"cmd": "{prefix}崩铁米游社更新面板 <UID>", "desc": "通过米游社接口刷新星铁面板数据"},
            {"cmd": "{prefix}崩铁重载面板 [UID]", "desc": "重新加载本地星铁面板缓存"},
            {"cmd": "{prefix}崩铁删除面板 [UID]", "desc": "删除本地星铁面板数据"},
            {"cmd": "{prefix}崩铁面板服务 <auto|miao|mihomo|avocado|enkahsr>", "desc": "星铁面板源：Miao、Mihomo、Avocado、EnkaHSR"},
        ],
    },
    {
        "group": "单角色详情",
        "items": [
            {"cmd": "{prefix}崩铁黄泉面板 <UID>", "desc": "查看单角色完整面板图，兼容 miao-plugin 风格"},
            {"cmd": "{prefix}崩铁黄泉详情 <UID>", "desc": "展示属性、光锥、行迹、遗器与星魂信息"},
            {"cmd": "{prefix}崩铁黄泉遗器 <UID>", "desc": "查看单角色遗器评分详情"},
            {"cmd": "{prefix}崩铁遗器列表 [UID]", "desc": "按评分查看公开角色遗器列表"},
            {"cmd": "{prefix}崩铁黄泉伤害 <UID>", "desc": "查看角色通用伤害估算/排名伤害项"},
            {"cmd": "{prefix}崩铁黄泉光锥1 <UID>", "desc": "面板计算中替换/模拟光锥（规划）"},
            {"cmd": "{prefix}崩铁黄泉满星魂满行迹", "desc": "模拟星魂、行迹、遗器套装等面板变化（规划）"},
            {"cmd": "{prefix}崩铁刷新行迹", "desc": "强制刷新星铁角色行迹/技能数据"},
        ],
    },
    {
        "group": "排行与练度",
        "items": [
            {"cmd": "{prefix}崩铁黄泉最强 / {prefix}崩铁黄泉最高分", "desc": "查询群内星铁角色面板/遗器排名"},
            {"cmd": "{prefix}崩铁黄泉排名 / {prefix}崩铁黄泉排行榜", "desc": "查看指定角色群内排名榜"},
            {"cmd": "{prefix}崩铁刷新排名", "desc": "刷新群内星铁面板排行数据"},
            {"cmd": "{prefix}崩铁重置排名", "desc": "重置群内星铁面板排名缓存"},
            {"cmd": "{prefix}崩铁练度统计", "desc": "星铁角色练度/养成统计"},
            {"cmd": "{prefix}崩铁刷新行迹", "desc": "刷新技能/行迹后更新练度统计"},
        ],
    },
    {
        "group": "抽卡统计",
        "items": [
            {"cmd": "{prefix}崩铁抽卡记录", "desc": "查看星铁抽卡记录，对齐 miao-plugin 星铁抽卡"},
            {"cmd": "{prefix}崩铁角色池分析", "desc": "按角色跃迁分析抽卡记录"},
            {"cmd": "{prefix}崩铁光锥池分析", "desc": "按光锥跃迁分析抽卡记录"},
            {"cmd": "{prefix}崩铁常驻池分析", "desc": "常驻跃迁记录分析"},
            {"cmd": "{prefix}崩铁全部池统计", "desc": "星铁全卡池抽卡统计"},
            {"cmd": "{prefix}崩铁版本池统计", "desc": "按版本统计星铁跃迁记录"},
        ],
    },
    {
        "group": "资料图鉴",
        "items": [
            {"cmd": "{prefix}崩铁黄泉行迹 / {prefix}崩铁黄泉技能", "desc": "查看角色行迹与技能资料"},
            {"cmd": "{prefix}崩铁黄泉星魂", "desc": "查看角色星魂资料"},
            {"cmd": "{prefix}崩铁黄泉资料 / {prefix}崩铁黄泉图鉴", "desc": "角色资料图鉴；原版 miao-plugin 暂不展示星铁角色图鉴页"},
            {"cmd": "{prefix}崩铁黄泉图片 / {prefix}崩铁黄泉照片", "desc": "查看角色图片资源"},
            {"cmd": "{prefix}崩铁黄泉养成 / {prefix}崩铁黄泉材料", "desc": "查看角色养成材料（规划）"},
            {"cmd": "{prefix}崩铁光锥图鉴", "desc": "星铁光锥资料与别名检索（规划）"},
        ],
    },
]
