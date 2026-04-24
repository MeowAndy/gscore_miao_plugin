PLUGIN_VERSION = "0.13.3"

CHANGELOGS = [
    {
        "version": "0.13.3",
        "date": "2026-04-25",
        "items": [
            "修复 Enka 武器 itemId 位于 equip.itemId 时无法反查武器名与图标的问题",
            "补齐 Enka 圣遗物主词条与副词条数值解析，面板图圣遗物卡片开始显示单件评分与评级",
            "圣遗物评分不再把花/羽固定主词条计入，扁平生命/攻击/防御副词条会按等效百分比折算后评分",
            "圣遗物详情图副词条展示数值，继续对齐 Yunzai miao-plugin 的 artis-mark 评分展示",
        ],
    },
    {
        "version": "0.13.2",
        "date": "2026-04-25",
        "items": [
            "修复 Enka 数字武器 ID/nameTextMapHash 导致面板图武器名显示异常的问题",
            "兼容 Yunzai miao-plugin 的 weapon/<type>/data.json 聚合映射，按 item_id 反查具体武器目录与 icon.webp",
            "武器名称与图标优先使用本地 miao-plugin resources/meta-gs/weapon 素材，进一步贴近原版面板资源链路",
        ],
    },
    {
        "version": "0.13.1",
        "date": "2026-04-25",
        "items": [
            "新增米游社扫码登录：喵喵登录 不带 Cookie 时直接生成二维码，使用米游社 App 扫码确认后自动保存 Cookie",
            "新增 WebUI 开关 EnableMysQrLogin，可单独控制扫码登录能力",
            "对比确认原版 miao-plugin 本体只引用 Cookie 能力，扫码登录来自 Yunzai/GsCore 登录体系，已在 GsCore 版内置接入",
        ],
    },
    {
        "version": "0.13.0",
        "date": "2026-04-25",
        "items": [
            "新增米游社 Cookie 登录入口：喵喵登录 <Cookie>，可保存登录信息并自动绑定原神 UID",
            "新增登录信息管理：喵喵查看登录、喵喵删除登录",
            "新增原神每日签到入口：喵喵签到 [UID]，作为 miao-plugin 登录/签到能力的 GsCore 初步迁移",
            "新增 WebUI 开关 EnableMysLogin、EnableDailySign 与登录教程配置 LoginHelpUrl",
        ],
    },
    {
        "version": "0.12.0",
        "date": "2026-04-25",
        "items": [
            "新增圣遗物详情评分图与圣遗物列表图，继续对齐 Yunzai miao-plugin 的 artis-mark/artis-list 功能",
            "修复单角色面板图固定高度导致底部内容显示不完整的问题，改为按内容动态裁剪高度",
            "面板列表命令改为优先输出图片列表，并修正圣遗物列表命令被评分命令提前匹配的问题",
            "圣遗物与伤害文本回退路径指定角色未命中时不再错误回退第一个角色",
        ],
    },
    {
        "version": "0.11.0",
        "date": "2026-04-25",
        "items": [
            "迁移 Yunzai miao-plugin 的 resources/meta-gs/artifact/artis-mark.js 常用角色圣遗物评分权重",
            "圣遗物评分增加角色专属权重、绝缘4、西风武器、薙草高精等常见动态规则",
            "评分输出改为显示使用规则，并按 miao-plugin 风格 MAX/ACE/SSS/SS/S/A/B/C 档位划分",
        ],
    },
    {
        "version": "0.10.0",
        "date": "2026-04-25",
        "items": [
            "研究并接入 Yunzai miao-plugin 的 profile-detail 渲染资源链路：优先复用本地 miao-plugin 角色立绘、武器图标和圣遗物图标",
            "补齐 Miao/米游社/Mgg/Hutao 等 avatars 到统一 characters 模型转换，避免非 Enka 数据源无法出图",
            "单角色自然命令增加图片渲染异常回退，确保不会因为素材缺失导致无回复",
        ],
    },
    {
        "version": "0.9.0",
        "date": "2026-04-25",
        "items": [
            "新增 UID 绑定：喵喵设置uid <UID>，面板/圣遗物/伤害/自然命令可省略 UID",
            "新增面板列表、更新面板、删除面板/解绑UID 等 miao-plugin 常用管理入口",
            "更新面板会清理当前进程内面板缓存后重新拉取数据",
        ],
    },
    {
        "version": "0.8.3",
        "date": "2026-04-25",
        "items": [
            "优化 Enka 424/404 错误提示，说明未缓存或展柜未公开等原因",
            "显式选择 enka 时若开启数据源降级，也会继续尝试 Miao/米游社等后备源",
            "第三方 HTTP 错误统一改为更短的可读提示，避免直接甩出长异常链接",
        ],
    },
    {
        "version": "0.8.2",
        "date": "2026-04-25",
        "items": [
            "修复 Enka 仅返回数字 ID 时面板图显示一堆数字的问题",
            "圣遗物卡片图标由 1-5 数字占位改为花、羽、沙、杯、冠",
            "补充基础角色 ID 到中文名映射，并将常见 Enka 词条 ID 中文化",
        ],
    },
    {
        "version": "0.8.1",
        "date": "2026-04-25",
        "items": [
            "重做单角色面板图为更接近 Yunzai miao-plugin 的竖版布局",
            "面板图新增大立绘占位、角色基础信息、属性、天赋、命座、武器与圣遗物分区",
            "保留无素材环境下的纯 Pillow 渲染，后续继续接入原版资源与 HTML/CSS 模板",
        ],
    },
    {
        "version": "0.8.0",
        "date": "2026-04-25",
        "items": [
            "新增 miao-plugin 风格角色命令：喵喵雷神面板/圣遗物/伤害 <UID>",
            "补充迁移路线文档，按命令、数据、渲染、计算、素材与管理功能拆分后续任务",
            "统一角色名别名解析入口，降低自然命令匹配失败概率",
        ],
    },
    {
        "version": "0.7.0",
        "date": "2026-04-25",
        "items": [
            "新增角色别名查询入口与常用原神角色别名表",
            "新增圣遗物评分与通用伤害估算首版迁移",
            "新增单角色面板图命令，并补充对应 WebUI 开关",
        ],
    },
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
