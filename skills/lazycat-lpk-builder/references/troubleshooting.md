# Docker 移植避坑指南与最佳实践

将现有的 Docker 镜像或 `docker-compose.yml` 移植到懒猫微服（`lzc-manifest.yml`）时，开发者经常会在以下几个关键点遇到问题。请在协助用户时，务必参考并应用这些最佳实践。

## 1. 权限与用户问题 (User & Permissions)
**问题：** 许多第三方 Docker 镜像默认使用普通用户（如 `node`, `abc` 等）运行，但在懒猫微服中，持久化目录 `/lzcapp/var/` 和用户文稿目录 `/lzcapp/run/mnt/home/` 默认需要 `root` 权限才能读写，这会导致 `Permission denied` 错误。

**最佳实践：**
- **首选方案：** 尽可能让容器以 `root` 用户运行。如果镜像文档没有强制要求，这是最简单的解决路径。
- **次选方案（应用拒绝 root）：** 如果应用本身（如某些数据库或特定服务）强制禁止 `root` 运行，你需要通过 `setup_script` 以 root 权限先处理好目录权限，或者在 `services` 块中使用 `user: "1000"` (注意：用户ID必须是带引号的字符串) 并在启动前调整权限。

## 2. 配置文件初始化与读写 (Config Files)
**问题：** 应用需要一个初始的配置文件（如 `config.yml`），该文件打包在 lpk 中（位于 `/lzcapp/pkg/content/`），且应用在运行时还需要修改它。如果直接把 `/lzcapp/pkg/content/config.yml` 通过 `binds` 挂载，会因为 `/lzcapp/pkg/content` 是**只读 (Read-Only)** 的而导致应用修改失败崩溃。

**最佳实践：**
- **绝不要** 将 `/lzcapp/pkg/content/` 下的文件直接作为读写配置挂载。
- **正确做法：** 使用 `setup_script`。在容器启动执行原逻辑之前，先判断目标可写路径（如 `/lzcapp/var/config.yml`）是否存在。如果不存在，则将 `/lzcapp/pkg/content/` 下的初始配置拷贝过去。
  
  ```yaml
  services:
    app:
      image: xxx
      binds:
        - /lzcapp/var/conf:/app/conf # 挂载可写目录
      setup_script: |
        if [ ! -f /app/conf/config.yml ]; then
            cp /lzcapp/pkg/content/default-config.yml /app/conf/config.yml
        fi
  ```

## 3. 启动顺序与健康检查 (Startup & Healthcheck)
**问题：** 带有数据库的重量级应用首次启动时，初始化表结构可能耗时很久。如果不合理配置健康检查，容器可能在初始化完成前就被系统判定为 `unhealthy` 并 Kill 掉。

**最佳实践：**
- **不要单纯依赖硬等待 (`sleep`)：** 强行拉长 `start_period` 并不能完美解决问题，且体验极差。
- **正确做法：** 编写具有实际语义的健康检查探针。对于 Web 服务，使用 `curl` 检查实际的 API 接口；对于数据库（如 MySQL），应使用实际的 `select 1` 等 SQL 查询语句来判断服务是否真正就绪。
- 使用 `services.[].healthcheck`（而不是废弃的 `health_check`），并合理配置 `retries`, `interval` 和 `start_period`。

## 4. 特权与内核能力 (Privileged & Capabilities)
**问题：** 某些应用（如旁路由、VPN、需要 FUSE 挂载的应用）必须依赖 Docker 的特权模式 (`privileged: true`) 或特殊的 Capability (`cap_add`)。

**最佳实践：**
- 如果原应用确实依赖特权，在微服中可以直接果断地给予相关特权。
- 使用 `lzc-build.yml` 中的 `compose_override` 字段来注入这些底层 Docker 参数（如 `privileged`, `cap_add`, `devices`）。
- **商店审核：** 带有这类特权需求的应用，只要功能合理，**是允许上架**懒猫官方应用商店进行审核的，无需为此担忧。

## 5. 局域网访问、跨域与 Host 头校验 (Host & CORS)
**问题：** 容器服务经常对 HTTP 请求的 `Host` Header 进行严格校验。如果不对，可能会报错或引发跨域问题。

**最佳实践：**
- **默认情况：** 懒猫微服的 `lzc-ingress` 已经非常智能，绝大部分情况会自动处理好 Host 头和跨域问题，开发者通常不需要特殊配置。
- **特殊情况：** 如果应用确实报了相关的域名或 Host 校验错误，可以在 `application.upstreams` 中配置相关的转发规则，并添加 `use_backend_host: true`，让上游服务看到它期望的 Host 头。