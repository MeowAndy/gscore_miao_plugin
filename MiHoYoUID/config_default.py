from typing import Dict

from gsuid_core.utils.plugins_config.models import (GSC, GsBoolConfig,
                                                    GsIntConfig,
                                                    GsListStrConfig,
                                                    GsStrConfig)

CONFIG_DEFAULT: Dict[str, GSC] = {
    "EnableHelp": GsBoolConfig(
        "开启帮助指令",
        "关闭后将不响应 帮助/菜单/原神帮助/原神菜单/崩铁帮助/崩铁菜单 指令",
        True,
    ),
    "EnableVersion": GsBoolConfig(
        "开启版本指令",
        "关闭后将不响应 原神版本 指令",
        True,
    ),
    "EnableMiaoSetting": GsBoolConfig(
        "开启喵喵原神设置",
        "开启后可用 喵喵原神设置 查看与修改原神插件配置",
        True,
    ),
    "CommandPrefix": GsStrConfig(
        "命令显示前缀",
        "插件中文命令前缀；帮助与设置文本会同步展示，修改后需重启 GsCore 生效",
        "喵喵",
    ),
    "HelpTitle": GsStrConfig(
        "帮助标题",
        "帮助页主标题",
        "喵喵原神帮助（GsCore）",
    ),
    "HelpSubTitle": GsStrConfig(
        "帮助副标题",
        "帮助页副标题",
        "Yunzai miao-plugin 的 GsCore 迁移版",
    ),
    "HelpRenderMode": GsStrConfig(
        "帮助渲染模式",
        "帮助输出模式：text 为文本，image 为图片卡片",
        "image",
        options=["text", "image"],
    ),
    "AllowedPanelServers": GsListStrConfig(
        "可选面板服务",
        "展示给用户可选择的面板服务列表",
        ["auto", "miao", "enka", "mgg", "hutao", "mys", "mihomo", "avocado", "enkahsr"],
        options=["auto", "miao", "enka", "mgg", "hutao", "mys", "mihomo", "avocado", "enkahsr"],
    ),
    "DefaultPanelServer": GsStrConfig(
        "默认面板服务",
        "用户未设置时使用的默认服务",
        "mys",
        options=["auto", "miao", "enka", "mgg", "hutao", "mys", "mihomo", "avocado", "enkahsr"],
    ),
    "PanelSourcePriority": GsListStrConfig(
        "面板数据源优先级",
        "auto 模式下按顺序尝试，留空项会自动忽略",
        ["mys", "miao", "enka"],
        options=["miao", "enka", "mys", "mgg", "hutao", "mihomo", "avocado", "enkahsr"],
    ),
    "PanelRequestTimeout": GsIntConfig(
        "面板请求超时秒数",
        "请求第三方面板数据源的超时时间",
        15,
        max_value=60,
    ),
    "EnablePanelQuery": GsBoolConfig(
        "开启面板查询",
        "关闭后将不响应 面板/角色面板 指令",
        True,
    ),
    "EnableAliasQuery": GsBoolConfig(
        "开启角色别名查询",
        "关闭后将不响应 角色别名/别名 指令",
        True,
    ),
    "EnableArtifactScore": GsBoolConfig(
        "开启圣遗物评分",
        "关闭后将不响应 圣遗物评分 指令",
        True,
    ),
    "EnableDamageCalc": GsBoolConfig(
        "开启伤害计算",
        "关闭后将不响应 伤害计算 指令",
        True,
    ),
    "EnableMysLogin": GsBoolConfig(
        "开启米游社登录",
        "允许用户通过 Cookie 登录并保存到本地配置；请只在可信私聊环境使用",
        True,
    ),
    "EnableMysQrLogin": GsBoolConfig(
        "开启米游社扫码登录",
        "允许用户通过米游社 App 扫码登录，自动获取并保存 Cookie",
        True,
    ),
    "EnableDailySign": GsBoolConfig(
        "开启米游社签到",
        "允许已登录用户执行原神/崩铁每日签到",
        True,
    ),
    "EnableAutoDailySign": GsBoolConfig(
        "开启自动签到",
        "允许用户开启每日自动签到；关闭后定时任务不会执行",
        True,
    ),
    "AutoDailySignTime": GsListStrConfig(
        "每日自动签到时间",
        "每日自动执行米游社签到的时间，格式为 [小时, 分钟]，默认 [0, 30] 表示 00:30",
        ["0", "30"],
    ),
    "PrivateSignReport": GsBoolConfig(
        "签到私聊报告",
        "关闭后将不再给私聊订阅者推送自动/全部签到统计",
        True,
    ),
    "GroupSignReport": GsBoolConfig(
        "签到群组报告",
        "关闭后将不再给群聊订阅者推送自动/全部签到统计",
        True,
    ),
    "LoginHelpUrl": GsStrConfig(
        "登录教程链接",
        "喵喵登录 未携带 Cookie 时展示的教程链接，可填自建登录页或说明文档",
        "请私聊发送：喵喵登录 cookie_token=xxx; account_id=xxx; ltuid=xxx; ltoken=xxx",
    ),
    "EnablePanelFallback": GsBoolConfig(
        "开启数据源降级",
        "当前数据源失败时，是否继续尝试下一个数据源",
        True,
    ),
    "MiaoApiBaseUrl": GsStrConfig(
        "Miao API地址",
        "Miao API 基础地址，默认对齐 miao-plugin 的 http://miao.games",
        "http://miao.games",
    ),
    "MiaoApiQQ": GsStrConfig(
        "Miao API绑定QQ",
        "Miao API token 绑定的机器人QQ；未配置时会传 none",
        "",
    ),
    "MiaoApiToken": GsStrConfig(
        "Miao API密钥",
        "Miao API 鉴权 Token，通常为32位；没有可留空跳过",
        "",
    ),
    "MiaoApiGame": GsStrConfig(
        "Miao API游戏类型",
        "请求 Miao API 时携带的 game 参数",
        "gs",
        options=["gs", "sr"],
    ),
    "EnkaApiBaseUrl": GsStrConfig(
        "Enka API地址",
        "Enka Network 接口基础地址",
        "https://enka.network/api/uid",
    ),
    "EnkaLocale": GsStrConfig(
        "Enka语言",
        "请求 Enka 时使用的语言参数",
        "zh-cn",
        options=["zh-cn", "zh-tw", "en", "ja", "ko"],
    ),
    "MysApiBaseUrl": GsStrConfig(
        "米游社API地址",
        "米游社记录接口基础地址，默认 api-takumi-record.mihoyo.com",
        "https://api-takumi-record.mihoyo.com",
    ),
    "MysCookie": GsStrConfig(
        "米游社Cookie",
        "用于查询米游社公开/授权角色数据，留空则跳过米游社源",
        "",
    ),
    "MysDeviceId": GsStrConfig(
        "米游社DeviceId",
        "米游社请求设备ID，留空时后续可自动生成",
        "",
    ),
    "MysDeviceFp": GsStrConfig(
        "米游社DeviceFp",
        "米游社风控设备指纹，留空则不主动携带",
        "",
    ),
    "MysAppVersion": GsStrConfig(
        "米游社App版本",
        "x-rpc-app_version，需与签名盐版本保持一致",
        "2.102.1",
    ),
    "MysClientType": GsStrConfig(
        "米游社ClientType",
        "x-rpc-client_type，国内米游社默认5",
        "5",
        options=["5", "2", "4"],
    ),
    "MysDsSalt": GsStrConfig(
        "米游社DS Salt",
        "留空使用内置盐；米游社接口变更时可在此覆盖",
        "",
    ),
    "MggApiBaseUrl": GsStrConfig(
        "Mgg API地址",
        "MiniGG 面板数据源基础地址",
        "http://profile.microgg.cn",
    ),
    "HutaoApiBaseUrl": GsStrConfig(
        "胡桃API地址",
        "Hutao Enka 代理基础地址",
        "http://enka-api.hut.ao",
    ),
    "MihomoApiBaseUrl": GsStrConfig(
        "Mihomo API地址",
        "星铁 Mihomo 面板数据源基础地址",
        "https://api.mihomo.me/sr_info",
    ),
    "AvocadoApiBaseUrl": GsStrConfig(
        "Avocado API地址",
        "星铁 Avocado 面板数据源基础地址",
        "https://avocado.wiki/v1/raw/info",
    ),
    "EnkaHSRApiBaseUrl": GsStrConfig(
        "EnkaHSR API地址",
        "星铁 Enka Network 面板数据源基础地址",
        "https://enka.network/api/hsr/uid",
    ),
    "PanelCacheTTL": GsIntConfig(
        "面板缓存秒数",
        "同一 UID 面板数据缓存时间，0 表示不缓存",
        300,
        max_value=86400,
    ),
    "PanelRenderMode": GsStrConfig(
        "面板渲染模式",
        "面板输出模式：text 为文本摘要，image 为图片卡片",
        "image",
        options=["text", "image"],
    ),
    "MiaoPluginResourcePath": GsStrConfig(
        "外部miao-plugin资源目录",
        "可选兼容项：默认使用本插件内置适配资源；仅在调试或覆盖素材时填写本地 miao-plugin 目录",
        "",
    ),
    "AllowGuestUse": GsBoolConfig(
        "允许游客使用",
        "关闭后，仅管理员可调用本插件命令",
        True,
    ),
    "RecentHistoryLimit": GsIntConfig(
        "历史记录保留条数",
        "每个用户最多保留多少条最近操作记录",
        20,
        max_value=200,
    ),
    "UpdateLogLimit": GsIntConfig(
        "更新日志展示条数",
        "每次显示最近多少条更新记录",
        5,
        max_value=30,
    ),
    "EnableSettingExport": GsBoolConfig(
        "开启设置导出",
        "允许用户通过命令导出当前设置JSON",
        True,
    ),
    "EnableSettingReset": GsBoolConfig(
        "开启设置重置",
        "允许用户通过命令重置个人设置",
        True,
    ),
    "MaxCommaGroup": GsIntConfig(
        "数字分组最大值",
        "喵喵原神设置逗号 的最大允许值",
        8,
        max_value=12,
    ),
}
