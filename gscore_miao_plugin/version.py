PLUGIN_VERSION = "0.6.0"

CHANGELOGS = [
    {
        "version": "0.6.0",
        "date": "2026-04-25",
        "items": [
            "迁移 miao-plugin 风格角色面板图片模板",
            "PanelRenderMode=image 时输出图片卡片，失败自动回退文本摘要",
            "面板图支持展示等级、命座、天赋、武器、圣遗物、双暴与充能",
        ],
    },
    {
        "version": "0.5.1",
        "date": "2026-04-25",
        "items": [
            "完善 Enka avatarInfoList 角色详情解析",
            "面板文本摘要新增角色等级、命座、天赋、武器、圣遗物与双暴信息",
            "为后续图片面板渲染补齐统一角色详情字段",
        ],
    },
    {
        "version": "0.5.0",
        "date": "2026-04-24",
        "items": [
            "对齐 Miao API profile/data 参数：uid、qq、token、version、game",
            "新增米游社 index 与 character/list 请求流程及 DS 签名",
            "对齐 Enka、MiniGG、Hutao 数据源默认地址与 User-Agent",
        ],
    },
    {
        "version": "0.4.0",
        "date": "2026-04-24",
        "items": [
            "新增 Miao/Enka/米游社/Mgg/胡桃面板数据源配置项",
            "新增面板数据查询客户端与 auto 降级逻辑",
            "喵喵面板 <UID> 接入数据查询并输出文本摘要",
        ],
    },
    {
        "version": "0.3.1",
        "date": "2026-04-24",
        "items": [
            "修正 GsCore force_prefix 下的命令匹配方式",
            "补充面板命令入口占位与 WebUI 用户配置字段",
            "对齐 XutheringWavesUID 的插件前缀写法",
        ],
    },
    {
        "version": "0.3.0",
        "date": "2026-04-24",
        "items": [
            "帮助改为结构化命令分组展示",
            "新增 #喵喵设置星级 与 #喵喵设置逗号",
            "新增 #喵喵设置导出 与 #喵喵设置重置",
            "设置读取支持默认值合并，提升兼容性",
        ],
    },
    {
        "version": "0.2.0",
        "date": "2026-04-24",
        "items": [
            "增加 #喵喵更新日志 指令",
            "增加游客开关与管理员权限控制",
            "设置项持久化增强，补充历史记录查询",
            "帮助命令补充快捷命令索引",
        ],
    },
    {
        "version": "0.1.0",
        "date": "2026-04-24",
        "items": [
            "完成 GsCore 版基础迁移结构",
            "实现 喵喵帮助 / 喵喵版本 / #喵喵设置",
            "提供 WebUI 配置项与管理表映射",
        ],
    },
]
