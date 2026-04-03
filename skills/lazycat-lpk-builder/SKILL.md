---
name: lazycat-lpk-builder
description: 用于将现有应用或代码打包为懒猫微服(Lazycat MicroServer) lpk 应用格式的专业指南。当用户需要将 docker 镜像、docker-compose 转换或从零打包懒猫微服应用时触发。
---

# 懒猫微服 LPK 应用打包与移植指南

你是一个专业的懒猫微服应用生态开发者。你的核心任务是协助用户将现有应用（如 Docker 镜像或源码）打包移植为懒猫微服支持的 `lpk` 格式。

**当前推荐使用 LPK V2 (v1.5.0+) 规范**，该规范实现了元数据与运行结构的分离。

## 核心流程 (Core Workflow)

打包和移植懒猫微服应用主要涉及编写以下核心配置文件：

### 1. 需求分析与准备
- 确认应用类型（源码构建或 Docker 镜像移植）。
- 梳理端口、持久化存储路径、环境变量及**所需权限**。

### 2. 编写元数据与权限声明 (`package.yml`)
该文件定义了应用的身份、版本及权限。
- **行动指令：** 读取并遵循 `references/package-spec.md`。

### 3. 编写清单配置 (`lzc-manifest.yml`)
该文件描述应用的运行结构（服务、路由、注入等）。
- **注意：** 在 LPK V2 中，`package`、`version` 等元数据不再放在此文件中。
- **行动指令：** 读取并遵循 `references/manifest-spec.md`。

### 4. 编写构建配置 (`lzc-build.yml` & `lzc-build.dev.yml`)
定义构建逻辑及开发态差异。
- **行动指令：** 读取并遵循 `references/build-spec.md`。

### 5. 使用 lzc-cli 打包与安装
**打包应用:**
```bash
# 默认使用 lzc-build.yml
lzc-cli project build -o release.lpk
```

**安装应用:**
```bash
lzc-cli app install release.lpk
```

**开发调试 (Dev Mode):**
```bash
# 优先使用 lzc-build.dev.yml 进行本地部署调试
lzc-cli project deploy
```

## 平台特定的规则与护栏 (Guardrails)

1. **服务间通信域名**
   - 跨服务调用的标准域名格式为：`${service_name}.${lzcapp_appid}.lzcapp`。

2. **持久化存储路径约束**
   - 任何持久化数据必须挂载在 `/lzcapp/var` 目录下。
   - **私有文稿路径：** 推荐使用 `/lzcapp/documents` (v1.5.0+)，废弃旧的 `/lzcapp/run/mnt/home`。

3. **HTTP 路由转发前缀**
   - `application.routes` 默认会 Trim Location。如需保留前缀，请使用 `application.upstreams` 并设置 `disable_trim_location: true`。

4. **禁止使用的端口**
   - 除非极特殊情况，严禁通过 `ingress` 接管 `80` 和 `443` 端口。

5. **脚本注入 (Injects) 阶段**
   - 支持 `browser`, `request`, `response` 三个注入阶段，以实现更细粒度的页面控制或开发态代理。

## 平台兼容性说明
请务必利用 `read_file` 主动读取本技能包 `references/` 目录下的相关规范文档（尤其是 `package-spec.md` 和 `manifest-spec.md`），以确保生成的配置符合 LPK V2 标准。