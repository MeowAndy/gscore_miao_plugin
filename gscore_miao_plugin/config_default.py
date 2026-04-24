from typing import Dict

from gsuid_core.utils.plugins_config.models import (GSC, GsBoolConfig,
                                                    GsIntConfig,
                                                    GsListStrConfig,
                                                    GsStrConfig)

CONFIG_DEFAULT: Dict[str, GSC] = {
    "EnableHelp": GsBoolConfig(
        "开启帮助指令",
        "关闭后将不响应 帮助/菜单 指令",
        True,
    ),
    "EnableVersion": GsBoolConfig(
        "开启版本指令",
        "关闭后将不响应 版本 指令",
        True,
    ),
    "EnableMiaoSetting": GsBoolConfig(
        "开启喵喵设置",
        "开启后可用 #喵喵设置 查看与修改本插件配置",
        True,
    ),
    "HelpTitle": GsStrConfig(
        "帮助标题",
        "帮助页主标题",
        "喵喵帮助（GsCore）",
    ),
    "HelpSubTitle": GsStrConfig(
        "帮助副标题",
        "帮助页副标题",
        "Yunzai miao-plugin 的 GsCore 迁移版",
    ),
    "AllowedPanelServers": GsListStrConfig(
        "可选面板服务",
        "展示给用户可选择的面板服务列表",
        ["auto", "miao", "enka", "mgg", "hutao", "mys"],
        options=["auto", "miao", "enka", "mgg", "hutao", "mys"],
    ),
    "DefaultPanelServer": GsStrConfig(
        "默认面板服务",
        "用户未设置时使用的默认服务",
        "auto",
        options=["auto", "miao", "enka", "mgg", "hutao", "mys"],
    ),
    "PanelSourcePriority": GsListStrConfig(
        "面板数据源优先级",
        "auto 模式下按顺序尝试，留空项会自动忽略",
        ["miao", "enka", "mys"],
        options=["miao", "enka", "mys", "mgg", "hutao"],
    ),
    "PanelRequestTimeout": GsIntConfig(
        "面板请求超时秒数",
        "请求第三方面板数据源的超时时间",
        15,
        max_value=60,
    ),
    "EnablePanelQuery": GsBoolConfig(
        "开启面板查询",
        "关闭后将不响应 面板/角色面板/角色卡片 指令",
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
        options=["gs"],
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
        "miao-plugin资源目录",
        "本地 Yunzai miao-plugin 目录；填好后面板会直接复用其角色立绘、武器、圣遗物素材",
        "E:/gsuid_core/gsuid_core/plugins/miao-plugin",
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
        "#喵喵设置逗号 的最大允许值",
        8,
        max_value=12,
    ),
}
