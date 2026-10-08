---
name: lazycat-lpk-builder
description: 将源码、Docker 镜像或 docker-compose 移植为懒猫微服 LPK V2 应用；用于编写元数据与权限、运行清单、构建/开发态配置、资源导入导出及打包验证。
---

# 懒猫微服 LPK V2 打包与移植

## 0. 先校准，后写配置

写/改 package、manifest、build 或执行 build/deploy/release 前，**必须先读取并执行 `references/spec-sync.md`**：记录目标 lzcos 与 CLI 版本，获取官方原文，核对本地快照并声明冲突。HTTP 错误、空文档、HTML 错误页不算成功；离线只能明确声明使用快照，不能声称实时校准。

基线为 **lzcos >=1.5.0、lzc-cli >=2.0.0**；每项新能力还需独立核验门槛。当前技能不是“永远最新”的保证。

## 1. 分析应用

梳理端口/协议、CPU 架构、镜像入口与 UID、内部数据/用户文件、依赖、业务鉴权和所需权限。不要将 Compose 原样当 manifest，不默认申请 root/privileged/全部权限。

## 2. 分开编写四种配置

| 文件/需求 | 行动指令 |
| --- | --- |
| package.yml：静态身份、版本、权限 | 读取 `references/package-spec.md` |
| lzc-manifest.yml：服务、路由、inject、entries、运行身份 | 读取 `references/manifest-spec.md` |
| lzc-build.yml：正式构建 | 读取 `references/build-spec.md` |
| lzc-build.dev.yml：开发差异 | 同上，不能复制整份 release 配置 |
| 资源导出/导入 | 读取 `references/resource-export.md` |
| 权限、初始化、探针、持久化故障 | 读取 `references/troubleshooting.md` |
| 上架与审核 | 读取 `references/store-publish.md` |

V2 manifest 不放 package/version/name/locales/permissions/import_resources 等静态字段。完整包的内容可选，image-only 不必伪造 contentdir；图标按官方 PNG/商店要求，不能臆造大小限制。

## 3. 构建与验证

```bash
lzc-cli --version
lzc-cli project build -o release.lpk
```

检查实际使用的 Build config、最终 tar 包中的 package.yml/manifest.yml、必要资源与镜像 lock。`buildscript` **不得调用 project build**。带 #@build 或 Go template 的原始文件先按真实阶段预处理/渲染，再做严格 YAML 校验，不能忽略重复键或把模板错误当成合法文件。

安装/部署会改变设备状态，只有用户授权时执行：

```bash
lzc-cli app install ./release.lpk
# 本地开发场景；优先 dev 配置
lzc-cli project deploy
```

测试首装、升级、重启持久化、最小权限、免密登录和接口鉴权；仅本地静态校验不得声称“部署成功”。查已部署应用用 `lzc-cli docker` 前缀；需微服名时主动执行 `lzc-cli box default`。

## 4. 不可省略的边界

- 内部配置/数据库：var；缓存：cache；用户文件：有 document.private 的 `/lzcapp/documents/$uid`。不把所有持久化都塞 var，也不默认旧 home 兼容挂载。
- run_as（>=1.6.0）按镜像兼容性选择；不与同一 service 的 user/setup_script 混用。
- routes 默认去前缀；保留前缀用 upstreams；非 HTTP 用 ingress，不能用它绕过用户鉴权或随意接管 80/443。
- 开发机 localhost 需要 ctx.net.via.client(ctx.dev.id)，不是容器默认网络。
- 服务内网通信与代表用户的应用互访是不同机制，后者按[应用间访问](https://developer.lazycat.cloud/advanced-app-interconnect.html)校准权限与票据。
- public_path 不是业务鉴权；远端发布、提权、Token 创建与销毁等操作须明确范围和授权。

交付包含：校准来源/原文摘要、目标版本与门槛、配置/包位置、实际验证结果、未验证项、需授权的下一步。
