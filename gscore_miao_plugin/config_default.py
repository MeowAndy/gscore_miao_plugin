from typing import Dict

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsBoolConfig,
    GsIntConfig,
    GsListStrConfig,
    GsStrConfig,
)

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
        ["auto", "miao", "enka", "mgg", "hutao"],
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
    "EnablePanelFallback": GsBoolConfig(
        "开启数据源降级",
        "当前数据源失败时，是否继续尝试下一个数据源",
        True,
    ),
    "MiaoApiBaseUrl": GsStrConfig(
        "Miao API地址",
        "自建或兼容 miao 面板接口的基础地址，留空则跳过",
        "",
    ),
    "MiaoApiToken": GsStrConfig(
        "Miao API密钥",
        "Miao API 鉴权 Token，没有可留空",
        "",
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
        "米游社面板接口基础地址，正式接入 Cookie/签名后使用",
        "",
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
    "MggApiBaseUrl": GsStrConfig(
        "Mgg API地址",
        "兼容 Mgg 面板数据源的基础地址，留空则跳过",
        "",
    ),
    "HutaoApiBaseUrl": GsStrConfig(
        "胡桃API地址",
        "兼容胡桃面板数据源的基础地址，留空则跳过",
        "",
    ),
    "PanelCacheTTL": GsIntConfig(
        "面板缓存秒数",
        "同一 UID 面板数据缓存时间，0 表示不缓存",
        300,
        max_value=86400,
    ),
    "PanelRenderMode": GsStrConfig(
        "面板渲染模式",
        "当前先支持文本摘要，后续迁移 miao 面板图渲染",
        "text",
        options=["text", "image"],
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
