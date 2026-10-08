# lzc-manifest.yml：LPK V2 运行配置

依据：[官方 manifest 规范](https://developer.lazycat.cloud/spec/manifest.html)。本文件只列常用能力；先按 `references/spec-sync.md` 校准原文和目标版本。元数据、权限、资源导入写入 `package.yml`，manifest 只描述运行结构。

## 1. 顶层与应用字段

顶层常用项：`usage`、`application`、`services`、`ext_config`。不要把元数据或 Docker Compose 顶层字段混入。

| application 字段 | 类型/注意事项 |
| --- | --- |
| `image` | string；默认系统镜像通常足够，支持镜像引用或 `embed:<alias>` |
| `subdomain` | string；申请的默认子域名，实际地址以运行时环境为准 |
| `multi_instance` | bool；实例模式变化涉及持久化数据迁移 |
| `depends_on` | []string；同应用其他服务，强制按健康状态依赖 |
| `environment` | map 或 KEY=VALUE 列表 |
| `workdir` | string |
| `user` / `run_as` | 见下一节，不能同时使用 |
| `routes` / `upstreams` | 简化路由 / 高级路由，可共存 |
| `public_path` | []string；放开平台登录检查，不是自动具备业务鉴权 |
| `oidc_redirect_path` | string；真实 OIDC 回调路径 |
| `injects` | []InjectConfig；browser/request/response |
| `entries` | []EntryConfig；多入口，见第 4 节 |
| `ingress` | []IngressConfig；TCP/UDP，不提供平台用户鉴权 |
| `file_handler` | 文件 MIME 与 actions；按官方规范配置 |
| `gpu_accel` / `usb_accel` / `kvm_accel` | bool；同时声明相应设备权限 |
| `vt` | bool；必须有 vt.display 权限，所有 service 禁用 sysbox-runc |
| `health_check` | app 的扩展检查；不随意替换系统自动依赖检查 |

## 2. 用户与持久目录 owner（run_as >=1.6.0）

`user` 只调整进程身份；`run_as` 还映射 `/lzcapp` 持久目录 owner。不要默认提权到 root 来掩盖配置错误。

- `run_as` 只接受数字 UID/GID：`1000` 或 `"1000:1000"`，不接受用户名。
- `application.run_as` 不与 application.user 同用。
- 同一个 service 的 `run_as` 不与 `user` 或 `setup_script` 同用。
- application.run_as 只作用于内置 app，各 service 必须独立声明。
- `/lzcapp/document`、`/lzcapp/documents/<uid>`、`/lzcapp/var`、`/lzcapp/cache` 映射 owner；`/lzcapp/run` 仍可写。
- 是否可改运行身份还取决于镜像入口；例如必须由 root 初始化再自行降权的镜像，不机械套 run_as。

```yaml
# lzc-manifest.yml 片段；这里用允许非 root 运行的 Alpine 进程演示身份语义
application:
  subdomain: demo
services:
  worker:
    image: alpine:3.21
    run_as: "1000:1000"
    command: "sh -c 'while true; do sleep 3600; done'"
    binds:
      - /lzcapp/var/worker:/data
```

## 3. 服务配置与初始化

`services.<name>` 常用字段：image、environment、entrypoint、command、binds、tmpfs、depends_on、healthcheck、user/run_as、cpu_shares、cpus、mem_limit、shm_size、network_mode、netadmin、setup_script、runtime。

- 普通容器健康检查是 **services.<name>.healthcheck**；不要把 application.health_check 也误判为废弃。
- `setup_script` 每次启动都会以 root 执行，系统随后运行镜像原始入口。须幂等，不与同 service 的 entrypoint/command/run_as 混用。
- binds 的来源只能是 `/lzcapp` 下路径；内部数据放 var/cache，包内容只读，用户文稿与权限匹配。
- network_mode 目前只支持 host 或留空；host/netadmin 需相应权限，并审计监听地址和鉴权。
- sysbox-runc 不支持 host namespace 共享等能力；按镜像与运行时实际限制选择。

权限或初始化问题请读取 `references/troubleshooting.md`。

## 4. 多入口与域名前缀

```yaml
# lzc-manifest.yml 片段
application:
  subdomain: demo
  entries:
    - id: home
      title: 首页
      path: /
    - id: admin
      title: 管理入口
      path: /settings
      prefix_domain: admin
```

`admin` 入口访问 `admin-<实际subdomain>.<rootdomain>`；前缀域名自动归属同一应用，无需另声明域名列表。**EntryConfig.prefix_domain**、**UpstreamConfig.domain_prefix**、**InjectConfig.prefix_domain** 是不同字段，不能互换。入口标题可在 package.yml.locales 中配置 `entries.<id>.title`。

## 5. 路由与 TCP/UDP

- routes 默认去掉 location 前缀；需要保留时用 upstreams.disable_trim_location（>=1.3.9）。
- upstream.backend 仅 http/https/file；程序自动启动用 backend_launch_command。routes 的 exec 简写是另一套语法，不能当成 upstream 协议。
- use_backend_host 控制 HTTP Host；改它不等于自行解决 TLS、CORS 或应用的可信代理配置。
- domain_prefix 按 `<prefix>-<subdomain>` 分流，HTTP 服务通信优先使用 `<service>.<appid>.lzcapp`。
- ingress 字段：protocol、port、service、description、publish_port、send_port_info、yes_i_want_80_443。它不提供 HTTP 登录、证书或用户鉴权；除特殊且明确授权场景，不接管 80/443。
- send_port_info 仅 TCP，增加 little-endian uint16 的两个字节，现有协议不一定能接受。

完整高级字段、路径匹配与端口范围以[路由](https://developer.lazycat.cloud/advanced-route.html)和[四层转发](https://developer.lazycat.cloud/advanced-l4forward.html)为准。

## 6. injects

- id、on、when（OR，至少一条）、unless（OR）、prefix_domain、auth_required（默认 true）、do。
- when/unless 单条规则精确匹配或末尾 `*` 前缀匹配；`/api/*` 不匹配 `/api`，需另列精确项。hash 仅 browser 生效。
- do 支持字符串 short syntax 或 `[{src, params}]` long syntax，两者都合法。
- src 的官方形式：builtin、file、inline。不要把未获官方保证的远程代码加载当作常规发布方案。
- browser 的参数/运行态用 ctx.params / ctx.runtime；request/response 在 lzcinit 同步执行，不支持 Promise/async，但可处理非 HTML 的 JSON/form/文本流量。
- ctx.body 写入用 set；ctx.response.send 与 ctx.proxy.to 生效后短路当前阶段。
- 平台 SAFE_UID 是 inject 上下文/门控身份，不是业务后端应读取的 Header。

开发机代理模板请读取 `references/build-spec.md`；细节以[官方 injects](https://developer.lazycat.cloud/advanced-injects.html)和[免密专题](https://developer.lazycat.cloud/advanced-inject-passwordless-login.html)为准。

## 7. 旧扩展与迁移

- ext_config.enable_document_access 只为旧 `/lzcapp/run/mnt/home` 兼容；v1.7.0 起需管理员明确授权。新文件功能优先 document.private 与 `/lzcapp/documents/$uid`。
- 旧 application.handlers 已废弃，改为 request/response inject。
- ext_config 等实验字段不保证长期兼容，不能为解决普通需求而默认启用。
