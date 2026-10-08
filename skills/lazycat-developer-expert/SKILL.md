---
name: lazycat-developer-expert
description: 懒猫微服应用开发的总控入口，用于 LPK V2 打包、权限与持久化、HTTP/L4 路由、部署参数与 inject、OIDC/用户委托、静态资源导入导出和商店上架。
---

# 懒猫微服开发：按需加载总控

## 必须先校准

凡写/改平台配置，或执行 build/deploy/release，先读取并执行 `references/spec-sync.md`。确认目标系统与 CLI 版本、获取官方原文、核对本地快照并报告差异；离线明确声明风险，不能把请求失败或错误页当“官方最新”。

LPK V2 至少 **lzcos 1.5.0 + lzc-cli 2.0.0**。package.yml 管静态元数据/权限/import_resources，manifest 管运行结构；build 管构建，dev 只留差异。新字段不等于旧设备支持。

## 需求路由

用文件读取工具按需读取同技能内文档，不依赖用户同时安装其他技能：

| 需求 | 必读文档 |
| --- | --- |
| Docker/源码移植、打包验收 | `references/lpk-builder.md` |
| 元数据、权限/版本门槛 | `references/package-spec.md` |
| 服务、entries、run_as、VT、运行字段 | `references/manifest-spec.md` |
| build/dev、embed 镜像、开发机代理 | `references/build-spec.md` |
| HTTP/前缀域名/Host/四层转发 | `references/advanced-routing.md` |
| 安装参数、Go template、三阶段 inject | `references/dynamic-deploy.md` |
| OIDC、可信身份 Header、API Token、public_path | `references/auth-integration.md` |
| 代表用户访问自身/其他应用 | `references/app-interconnect.md` |
| Skill/MCP 等静态资源发现/导入导出 | `references/resource-export.md` |
| 权限、初始化、探针、持久化问题 | `references/troubleshooting.md` |
| 商店提交与八项审核 | `references/store-publish.md` |

## 强制边界

- 不默认 root/privileged/公网放行；按最小权限、镜像入口与目标版本生成配置。
- 内部数据、缓存、用户文件分开存放；改变实例模式或路径先设计数据迁移。
- 自动前缀域名、upstream.domain_prefix、inject.prefix_domain、entry.prefix_domain 不得混为不存在的字段。
- API Token 消费不等于请求不能转发到应用；Header 身份必须来自可信平台入口；用户委托票据是版本受限的专门能力。
- #@build、Go template 和运行 JS 是不同阶段；原文、预处理结果、最终 YAML 分别校验。
- buildscript 不调用 project build；安装、发布、提权、凭据变更须用户授权。
- 应用状态使用 `lzc-cli docker`；需微服名时执行 `lzc-cli box default`。

只加载与需求相关的摘要/原文，输出校准记录、实际执行结果、未验证项，不把静态示例检查等同真实部署成功。
