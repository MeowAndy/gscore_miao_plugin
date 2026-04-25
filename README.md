# gscore_miao-plugin

将 Yunzai `miao-plugin` 迁移为可在 GsCore 运行的简化插件。

## 已移植能力（v0.15.3）

- 帮助：`喵喵原神帮助` / `喵喵原神菜单` / `喵喵崩铁帮助` / `喵喵崩铁菜单`
- 版本：`喵喵原神版本`
- 设置：`喵喵原神设置`
- 设置项：
  - `喵喵原神设置面板服务 <auto|miao|enka|mgg|hutao|mys|mihomo|avocado|enkahsr>`
  - `喵喵原神设置uid <UID>`
  - `喵喵原神设置面板图 <开启|关闭>`
  - `喵喵原神设置组队 <开启|关闭>`
  - `喵喵原神设置星级 <开启|关闭>`
  - `喵喵原神设置逗号 <2-8>`
  - `喵喵原神设置历史`
  - `喵喵原神设置导出`
  - `喵喵原神设置重置`
- 更新日志：`喵喵原神更新日志`（转发节点形式）
- UID 绑定：`喵喵原神设置uid <UID>`，绑定后面板/圣遗物/伤害/自然命令可省略 UID。
- 米游社登录与签到：`喵喵登录`、`喵喵扫码登录`、`喵喵签到`，签到同时尝试原神与崩坏：星穹铁道。
- 面板入口：`喵喵原神面板 [UID]` / `喵喵崩铁面板 [UID]`（已接入 Miao/Enka/米游社/Mgg/胡桃，以及星铁 Mihomo/Avocado/EnkaHSR 数据源；各源会尽量统一为角色详情模型；Enka 424/404 会友好提示并支持降级）
- 面板管理：`喵喵原神面板列表 [UID]` / `喵喵原神更新面板 [UID]` / `喵喵原神删除面板` / `喵喵原神解绑UID`
- 单角色面板图：`喵喵原神面板图 <UID> [角色]` / `喵喵崩铁面板图 <UID> [角色]`（优先使用插件内置适配资源，并可选复用本地 Yunzai `miao-plugin/resources` 素材）
- 圣遗物/遗器评分：`喵喵原神圣遗物评分 <UID> [角色]` / `喵喵崩铁遗器评分 <UID> [角色]`（内置 miao-plugin 风格评分权重，原神支持绝缘4/西风/薙草高精等常见规则；星铁支持 6 件遗器总评、单件分数与副词条评分展示）
- 伤害估算：`喵喵原神伤害计算 <UID> [角色]`
- miao-plugin 风格角色命令：`喵喵原神雷神面板 <UID>` / `喵喵原神雷神圣遗物 <UID>` / `喵喵原神雷神伤害 <UID>`；星铁命令域已开始铺设。
- 角色别名：`喵喵角色别名 <角色/别名>`
- 权限控制：支持游客开关（关闭后仅管理员可用）
- 状态页：注册 GsCore 插件状态统计
- WebUI 配置项（GsCore 网页控制台）：
  - EnableHelp
  - EnableVersion
  - EnableMiaoSetting
  - CommandPrefix
  - HelpTitle
  - HelpSubTitle
  - HelpRenderMode
  - AllowedPanelServers
  - DefaultPanelServer
  - PanelSourcePriority
  - PanelRequestTimeout
  - EnablePanelQuery
  - EnableAliasQuery
  - EnableArtifactScore
  - EnableDamageCalc
  - EnableMysLogin
  - EnableMysQrLogin
  - EnableDailySign
  - EnableAutoDailySign
  - AutoDailySignTime
  - PrivateSignReport
  - GroupSignReport
  - LoginHelpUrl
  - EnablePanelFallback
  - MiaoApiBaseUrl
  - MiaoApiQQ
  - MiaoApiToken
  - MiaoApiGame
  - EnkaApiBaseUrl
  - EnkaLocale
  - MysApiBaseUrl
  - MysCookie
  - MysDeviceId
  - MysDeviceFp
  - MysAppVersion
  - MysClientType
  - MysDsSalt
  - MggApiBaseUrl
  - HutaoApiBaseUrl
  - MihomoApiBaseUrl
  - AvocadoApiBaseUrl
  - EnkaHSRApiBaseUrl
  - MiaoPluginResourcePath
  - PanelCacheTTL
  - PanelRenderMode
  - AllowGuestUse
  - RecentHistoryLimit
  - UpdateLogLimit
  - EnableSettingExport
  - EnableSettingReset
  - MaxCommaGroup

## 目录

- `gscore_miao_plugin/` 插件主体
- `gscore_miao_plugin/config_default.py` WebUI 配置模型
- `gscore_miao_plugin/config.py` StringConfig 注册
- `gscore_miao_plugin/database.py` WebUI 数据表映射（用户配置/历史）
- `gscore_miao_plugin/status.py` GsCore 状态页注册

## 安装

将本目录放入 GsCore 插件目录，重启 GsCore 后即可加载：

- 插件名：`gscore_miao-plugin`
- 强制前缀：`喵喵` / `miao`
- 配置文件：GsCore 资源目录下的 `GsCoreMiao/config.json`

## 说明

原 `miao-plugin` 为 Yunzai 生态（Node.js）插件，和 GsCore（Python）运行时差异较大。
当前版本为 **功能语义迁移（v0.15.3）**，重点迁移命令形态、UID 绑定、面板管理入口、配置管理、更新日志、基础权限控制、面板数据源、图片模板、角色别名、圣遗物/遗器评分、登录签到与原神/星铁命令域。
Miao API 已对齐 `profile/data` 参数，米游社源已实现 `index` + `character/list` 与 DS 签名流程，Enka 源已解析角色详情摘要；星铁侧已接入 Mihomo、Avocado、EnkaHSR 数据源；`PanelRenderMode=image` 可输出 miao-plugin 风格角色面板图片。
插件默认使用内置适配资源集；如需调试或覆盖素材，可在 WebUI 将 `MiaoPluginResourcePath` 指向本地 Yunzai `miao-plugin` 目录，插件会尝试读取 `resources/meta-gs` 与 `resources/meta-sr` 下的角色立绘、武器/光锥图标、圣遗物/遗器图标、命座/星魂与天赋/行迹图标；素材缺失时会自动使用占位/文本回退，避免无响应。
圣遗物/遗器评分已迁移 miao-plugin 风格的常用角色权重和部分动态规则；星铁面板已按 miao-plugin 的 Mihomo/Avocado/EnkaHSR 适配思路补齐角色详情属性、光锥 hp/atk/def、遗器 mainAffixId/subAffixList 反算主副词条数值与副词条评分。伤害估算仍为首版通用算法，后续会继续逐角色对齐 miao-plugin 计算模板。
后续完整迁移路线见 `MIGRATION_PLAN.md`。

## 更新日志（内置）

完整变更记录见 `CHANGELOG.md`。

- v0.15.3
  - 修复星铁遗器固定值词条 `hpPlus` / `atkPlus` / `defPlus` 未转中文的问题
  - 固定生命、攻击、防御词条不再误显示百分号

- v0.15.2
  - 修复星铁 Mihomo/Avocado/EnkaHSR 面板源字段解析，角色详情不再只显示空属性
  - 星铁光锥补齐 hp/atk/def，遗器根据 `mainAffixId` / `subAffixList` 反算主副词条真实数值
  - 星铁遗器评分接入真实副词条数据，单件分与总分不再固定为 `0.0`

- v0.15.1
  - 新增 `喵喵崩铁帮助` / `喵喵崩铁菜单`，开始铺设崩坏：星穹铁道命令域
  - 星铁单角色面板补齐属性数值、星魂图标、遗器主副词条数值与副词条评分
  - 星铁遗器评分按 miao-plugin 风格展示 6 件总评、单件分数与评分规则

- v0.15.0
  - 原神功能命令统一增加 `喵喵原神...` 命令域，为后续 `喵喵崩铁...` 命令预留空间
  - miao-plugin 风格角色命令改为 `喵喵原神雷神面板/圣遗物/伤害`
  - `喵喵签到` 保持不变，继续统一处理原神与崩铁米游社签到

- v0.14.9
  - 内置资源改为 gscore_miao-plugin 适配资源集，外部 miao-plugin 目录仅作为可选覆盖
  - 面板素材保留当前渲染链路需要的 common、character、help 与 meta-gs 图片/JSON 数据
  - 圣遗物评分不再运行时读取原版 JS，改为使用插件内置 Python 评分权重与动态规则

- v0.14.8
  - 面板列表角色头像下方补齐橙色排名背景
  - 面板列表底部创建信息显示当前插件版本
  - `喵喵原神更新日志` 使用转发节点形式发送

- v0.14.7
  - `喵喵原神更新面板` 刷新成功后输出 Yunzai `miao-plugin` `profile-list` 风格图片
  - 面板列表复用星空背景、排名图标、圆形头像、命座角标和本次更新角色标记布局

- v0.14.6
  - 迁移崩坏：星穹铁道米游社签到接口
  - `喵喵签到` 同时尝试原神和崩铁；缺少其中一个账号时只回复已成功签到的游戏段落
  - 登录信息会保存和展示崩铁角色，支持仅绑定崩铁角色的 Cookie

- v0.14.5
  - 加长单角色面板画布高度，修复圣遗物卡片增高后底部被裁掉的问题
  - 战技和爆发图标按 Yunzai `miao-plugin` 的 `CharImg` 逻辑读取

- v0.14.4
  - 增强圣遗物图片反查，兼容 Enka 圣遗物 `item_id` 与本地 artifact 数据 ID 偏移
  - 单角色面板圣遗物区把总分、评级和评分规则独立放到圣遗物卡片上方
  - 圣遗物卡片展示最多四条副词条，Enka 刷新面板额外补齐元素/物理伤害加成

- v0.14.3
  - 修复多角色面板列表直接显示 `角色ID` 的问题
  - 面板列表武器名称复用单角色面板反查逻辑

- v0.14.2
  - 修复单角色面板普攻图标固定使用单手剑的问题
  - 单角色面板命座优先使用本地 `cons-1` 到 `cons-6` 素材
  - Enka 武器数值不再丢失，圣遗物区补充总分、评级和评分规则

- v0.14.1
  - 修复 `喵喵原神更新面板` 被通用角色面板命令误识别为角色“更新”的问题

- v0.14.0
  - 新增 `HelpRenderMode` WebUI 配置，默认以图片卡片模式输出帮助
  - 帮助命令统一使用 WebUI 的 `CommandPrefix` 动态展示前缀

- v0.11.0
  - 读取原版 `artis-mark.js` 角色圣遗物评分权重
  - 增加绝缘4、西风武器、薙草高精等常见动态评分规则
  - 评分档位改为 `MAX/ACE/SSS/SS/S/A/B/C` 风格，并显示当前规则

- v0.10.0
  - 接入本地 Yunzai `miao-plugin/resources` 素材路径，面板图优先显示原版角色立绘、武器图标、圣遗物图标
  - Miao/米游社/Mgg/Hutao 数据统一转换到角色详情模型，减少“没图/没详情”
  - 单角色图片渲染失败时回退文本摘要，避免命令无响应

- v0.8.2
  - 修复 Enka 数字 ID 在面板图中直接显示的问题
  - 圣遗物卡片图标由数字改为花/羽/沙/杯/冠
  - 补充基础角色 ID 到中文名映射，并将常见 Enka 词条 ID 中文化

- v0.8.1
  - 重做单角色面板图为更接近 Yunzai miao-plugin 的竖版布局
  - 新增大立绘占位、属性、天赋、命座、武器与圣遗物分区
  - 后续继续接入原版角色立绘素材与 HTML/CSS 模板

- v0.8.0
  - 新增 `喵喵雷神面板/圣遗物/伤害 <UID>` 这类 miao-plugin 风格自然角色命令
  - 新增迁移路线文档，明确后续要继续补齐的模块
  - 统一角色别名解析入口

- v0.7.0
  - 新增角色别名查询、圣遗物评分、伤害估算
  - 新增 `喵喵面板图 <UID> [角色]` 单角色图片面板
  - WebUI 增加别名、圣遗物、伤害计算功能开关

- v0.6.0
  - 新增 miao-plugin 风格角色面板图片模板
  - `PanelRenderMode=image` 时输出图片卡片，失败自动回退文本摘要
  - 图片面板展示等级、命座、天赋、武器、圣遗物、双暴与充能

- v0.5.1
  - Enka 源解析角色等级、命座、天赋、武器、圣遗物、双暴与充能
  - `喵喵面板 <UID>` 输出角色详情文本摘要

- v0.4.0
  - 新增 Miao/Enka/米游社/Mgg/胡桃面板数据源配置项
  - 新增面板数据查询客户端、auto 优先级与失败降级
  - `喵喵面板 <UID>` 输出面板文本摘要

- v0.5.0
  - 对齐 Miao API `profile/data` 参数与 token 校验
  - 新增米游社 `index` + `character/list` 请求流程和 DS 签名
  - 对齐 Enka、MiniGG、Hutao 默认地址与 User-Agent

- v0.3.1
  - 修正 GsCore 强制前缀下的命令匹配方式
  - 补充面板命令入口占位与 WebUI 用户配置字段
  - 增加 GsCore 状态页注册

- v0.3.0
  - 帮助改为结构化命令分组展示
  - 新增 `#喵喵设置星级` 与 `#喵喵设置逗号`
  - 新增 `#喵喵设置导出` 与 `#喵喵设置重置`
  - 设置读取支持默认值合并
- v0.2.0
  - 增加 `喵喵更新日志`
  - 增加 `#喵喵设置历史`
  - 增加游客开关与管理员限制
  - 统一版本信息源
