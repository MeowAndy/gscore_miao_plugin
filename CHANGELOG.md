# Changelog

All notable changes to `gscore_miao-plugin` are documented in this file.

## [0.5.1] - 2026-04-25

### Added
- Enka 数据源解析 `avatarInfoList` 为统一角色详情字段。
- 面板文本摘要展示角色等级、命座、好感、天赋、武器、圣遗物数量、双暴与充能。

### Changed
- 将面板摘要文案从“数据接入骨架”调整为“文本详情摘要”。

## [0.5.0] - 2026-04-24

### Added
- 新增 Miao API `MiaoApiQQ`、`MiaoApiGame` 配置项，并对齐 `profile/data` 请求参数。
- 新增米游社 `MysDeviceFp`、`MysAppVersion`、`MysClientType`、`MysDsSalt` 配置项。
- 米游社源实现 `index` 获取角色列表，再调用 `character/list` 获取角色详情。

### Changed
- 对齐 Miao、MiniGG、Hutao 默认接口地址。
- 为 Enka、MiniGG、Hutao 使用更接近 miao-plugin 的 User-Agent。

## [0.4.0] - 2026-04-24

### Added
- 新增 `喵喵面板 <UID>` 数据查询入口。
- 新增 Miao、Enka、米游社、Mgg、胡桃数据源配置项。
- 新增 auto 数据源优先级、失败降级、请求超时与缓存时间配置。
- 新增面板文本摘要输出，为后续迁移 miao-plugin 图片渲染打基础。

## [0.3.1] - 2026-04-24

### Added
- 增加 `喵喵面板` 命令入口占位，便于后续接入真实面板数据源。
- 增加 GsCore 状态页注册。
- WebUI 用户配置表补充 `show_star` 与 `comma_group` 字段。

### Fixed
- 修正 `force_prefix=["喵喵", "miao"]` 下命令重复匹配前缀导致无法触发的问题。
- 调整设置命令示例，使其符合 GsCore 插件前缀规范。

## [0.3.0] - 2026-04-24

### Added
- 帮助改为结构化命令分组展示。
- 新增 `#喵喵设置星级 <开启|关闭>`。
- 新增 `#喵喵设置逗号 <2-8>`。
- 新增 `#喵喵设置导出`。
- 新增 `#喵喵设置重置`。

### Changed
- 设置读取支持默认值合并，提升旧配置兼容性。
- README 与元数据同步到 `v0.3.0`。

## [0.2.0] - 2026-04-24

### Added
- 增加 `喵喵更新日志` 指令。
- 增加游客开关与管理员权限控制。
- 设置项持久化增强，补充历史记录查询。
- 帮助命令补充快捷命令索引。

## [0.1.0] - 2026-04-24

### Added
- 完成 GsCore 版基础迁移结构。
- 实现 `喵喵帮助` / `喵喵版本` / `#喵喵设置`。
- 提供 WebUI 配置项与管理表映射。
