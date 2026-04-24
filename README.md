# gscore_miao-plugin

将 Yunzai `miao-plugin` 迁移为可在 GsCore 运行的简化插件。

## 已移植能力（v0.7.0）

- 帮助：`喵喵帮助` / `喵喵菜单`
- 版本：`喵喵版本`
- 设置：`#喵喵设置`
- 设置项：
  - `#喵喵设置面板服务 <auto|miao|enka|mgg|hutao|mys>`
  - `#喵喵设置面板图 <开启|关闭>`
  - `#喵喵设置组队 <开启|关闭>`
  - `#喵喵设置星级 <开启|关闭>`
  - `#喵喵设置逗号 <2-8>`
  - `#喵喵设置历史`
  - `#喵喵设置导出`
  - `#喵喵设置重置`
- 更新日志：`喵喵更新日志`
- 面板入口：`喵喵面板 <UID>`（已接入 Miao/Enka/米游社/Mgg/胡桃数据源；Enka 已解析角色详情并支持图片面板）
- 单角色面板图：`喵喵面板图 <UID> [角色]`
- 圣遗物评分：`喵喵圣遗物评分 <UID> [角色]`
- 伤害估算：`喵喵伤害计算 <UID> [角色]`
- 角色别名：`喵喵角色别名 <角色/别名>`
- 权限控制：支持游客开关（关闭后仅管理员可用）
- 状态页：注册 GsCore 插件状态统计
- WebUI 配置项（GsCore 网页控制台）：
  - EnableHelp
  - EnableVersion
  - EnableMiaoSetting
  - HelpTitle
  - HelpSubTitle
  - AllowedPanelServers
  - DefaultPanelServer
  - PanelSourcePriority
  - PanelRequestTimeout
  - EnablePanelQuery
  - EnableAliasQuery
  - EnableArtifactScore
  - EnableDamageCalc
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
当前版本为 **功能语义迁移（v0.7.0）**，重点迁移命令形态、配置管理、更新日志、基础权限控制、面板数据源、图片模板、角色别名、圣遗物评分与伤害估算。
Miao API 已对齐 `profile/data` 参数，米游社源已实现 `index` + `character/list` 与 DS 签名流程，Enka 源已解析角色详情摘要；`PanelRenderMode=image` 可输出 miao-plugin 风格角色面板图片。圣遗物评分与伤害估算当前为首版通用算法，后续会继续逐角色对齐 miao-plugin 计算模板。

## 更新日志（内置）

完整变更记录见 `CHANGELOG.md`。

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
