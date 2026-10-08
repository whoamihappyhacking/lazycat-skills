# 更新记录

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 的分类格式。尚未发布的修改记录在 Unreleased；本次不虚构新版本号或发布日期。

## [Unreleased]

### Added · 新增

- 纳入 [PR #4](https://github.com/whoamihappyhacking/lazycat-skills/pull/4) 的官方规范校准、规范字段纠错与确定性 `.skill` 生成机制，保留原贡献提交。
- 六个配置技能独立携带规范抓取工具与校准流程，记录来源和原文摘要；支持错误检测、站点兜底与明确的离线风险状态。
- 仓库自动检查、隔离工具回归测试与 GitHub Actions，覆盖分发件同步、共享副本、引用、示例、敏感内容和 V2 配置边界。
- 静态资源导入/导出与用户委托应用互访参考；完整的最小 LPK V2 静态站示例。
- 首次建立本仓库更新记录；维护时使用 changelog-maintenance 技能，第三方技能不随仓库提交。

### Changed · 变更

- 通用规范按 2026-10-08 拉取的官方源仓库 `780d7206ce2298ee0a225e0221a993c4723d8e07` 核对，明确 V2 的 lzcos >=1.5.0 / CLI >=2.0.0 及各新能力门槛。
- 更新 package/manifest/build/权限/持久化/上架摘要，补 run_as、entries、VT、FUSE、通知、资源配置、最小权限与八项审核。
- 高级路由改为自动域名前缀机制；开发机代理使用明确的客户端网络路径。
- AI Pod 读取独立当前专题：resource、agxorin/thor、extensions、config/aipod.yml、startup gate；旧 ai-pod-service 和插件路径降为兼容说明。
- 官方 AI Pod 专题与通用 V2 import_resources/投影路径不一致处明确记录，未证实的消费端映射不再当作可直接套用的配置。
- README 不再承诺“永远最新”，区分静态校验、构建和真机部署；安装、发布与高权限动作须明确授权。

### Fixed · 修复

- 修复 PR 校准命令对 HTTP 错误/HTML 错误页误报成功、同技能引用断链及校准覆盖不足。
- 修正 API Token 被消费后的应用访问解释、不同调用模式下设备 Header 的可用性、public_path 的业务安全边界。
- 恢复官方免密注入参数依据，补参数持久化与三阶段成功后提交；区分 browser 与 request/response 的非 HTML 行为。
- 修正旧元数据混入 V2 manifest、错误字段/模板写法、路由协议与路径语义，以及无当前官方依据的断言。
- ZIP 生成修复 UTF-8 文件名、执行权限与参数校验边界；源文件与分发件同时校验，不接受隐藏额外内容。

### Security · 安全

- 重建分发件，移除旧包中已删除的 SDK 文档与设备敏感信息残留；AGENTS 示例改用占位符，不重写 Git 历史。
- 不默认 root、privileged、全量权限或业务 API 免登录；旧兼容挂载与 override 明确授权、版本及审核风险。
- 未获官方保证的远程 inject 脚本不再作为普通发布路径推荐。

### 迁移提示

- 旧 manifest 元数据移入 package.yml；dev 的 package_override 为顶层整体替换，不递归合并。
- 仅 user 不映射持久目录 owner；支持 run_as 的镜像/系统应按数值身份配置，不能与同 service 的 user/setup_script 混用。
- AI Pod 新资源不能仅按通用静态 resource_exports 推断专用消费布局；迁移前核实目标实现、备份并测试型号兼容。
- 使用者需重新安装/更新技能目录或替换 `.skill`；旧已安装副本不会因仓库变化自动被保证更新。
