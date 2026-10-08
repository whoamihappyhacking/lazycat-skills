---
name: lazycat-advanced-routing
description: 处理懒猫微服 LPK V2 的 HTTP/HTTPS 路由、域名前缀、Host/TLS、复杂反向代理及 TCP/UDP 四层转发问题。
---

# 懒猫微服高级路由

按下面顺序工作，不要直接套用旧版清单或旧镜像示例。

## 1. 先校准官方规范

任何打包、构建或路由配置任务，先读取 `references/spec-sync.md`，按其中流程核对当前官方原文，并确认目标 `lzcos` 与 `lzc-cli` 版本。仓库参考文档是快照；若与当前官方冲突，以官方为准。

LPK V2 必须拆分配置：

- `package.yml`：`package`、`version`、`name`、`description`、权限等静态包信息。
- `lzc-manifest.yml`：`application`、`services` 等运行结构。
- 不要在 V2 manifest 顶层继续写旧元数据，也不要添加不存在的 `application.secondary_domains`。

## 2. 选择正确的流量机制

| 需求 | 使用 | 关键规则 |
| --- | --- | --- |
| 简单 HTTP/HTTPS、静态文件或启动本地程序 | `application.routes` | `URL_PATH=UPSTREAM`；默认移除匹配的路径前缀 |
| 保留路径、按域名前缀分流、控制 Host/Header/TLS 校验 | `application.upstreams` | `backend` 只支持 `http`、`https`、`file` |
| TCP/UDP、数据库或其他非 HTTP 协议 | `application.ingress` | L4 直通，不经过平台 HTTP 鉴权 |
| 内置能力无法表达的复杂重写 | 应用内反向代理 | 优先用已核验的当前镜像，不复制过时 `app-proxy` 标签 |

协议边界必须明确：

- `routes` 支持 `http(s)://`、`file:///`、`exec://端口,程序路径`。
- `upstreams[].backend` 支持 `http`、`https`、`file`，不支持 `exec://`；需要启动程序时使用 `backend_launch_command`。
- `ingress` 只声明 `tcp` 或 `udp`，不要用它代替普通 HTTP 路由。

## 3. 域名与服务发现硬规则

- 每个应用自动拥有 `<prefix>-<实际子域名>.<微服根域>` 形式的前缀域名；按域名分流使用 `upstreams[].domain_prefix`。
- 实际分配域名可能因冲突或多实例而变化，只能从 `LAZYCAT_APP_DOMAIN` 获取，不要按 `application.subdomain` 硬拼最终域名。
- 同一应用内通常使用 `http://<service>:<port>`。需要让应用内代理收到完整入口 Host 时，按官方多域名方案使用 `<service>.<package-id>.lzcapp`。
- `.lzcapp` 服务 DNS 不等于跨应用调用机制。代表用户访问另一个应用的 HTTP 入口应使用 `app.<target-package-id>.lzcx`，并按官方应用间访问文档处理委托权限与用户票据。
- 前缀域名流量会忽略 `application.ingress`；L4 仅使用应用默认域名对应的入口。

## 4. 风险边界

- `use_backend_host` 控制 HTTP `Host`，不是官方声明的 TLS SNI 开关；HTTPS backend 应写与证书匹配的主机名。
- `disable_backend_ssl_verify` 会关闭后端证书校验，只能在明确风险后使用。
- L4 转发没有平台账户鉴权；应用必须自行实现协议鉴权。
- 接管 80/443 会绕过鉴权、自动唤醒、平台证书以及 `routes`/`upstreams`，且必须显式设置 `yes_i_want_80_443: true`。绝大多数应用不应这样做。

## 5. 按需渐进读取

只加载当前问题需要的文档：

- 简单路由、协议与服务 DNS：`references/route.md`
- `upstreams`、Host/TLS、复杂代理：`references/advanced-routes.md`
- 域名前缀、多域名分流：`references/secondary-domains.md`
- TCP/UDP 与 80/443 风险：`references/l4forward.md`

输出配置前至少检查：文件是否按 V2 拆分、字段是否属于正确层级、协议是否匹配、是否误用跨应用 DNS、是否扩大未鉴权入口，以及所用字段是否满足目标系统版本。
