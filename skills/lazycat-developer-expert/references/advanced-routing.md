# 高级路由、域名前缀与 L4（LPK V2）

> 校准基线：懒猫官方开发者文档仓库 `780d7206ce2298ee0a225e0221a993c4723d8e07`。这是离线快照；任何打包/构建任务先读取同目录 `spec-sync.md`，以当前官方原文和目标系统版本为准。

官方来源：

- <https://developer.lazycat.cloud/advanced-route.html>
- <https://developer.lazycat.cloud/advanced-secondary-domains.html>
- <https://developer.lazycat.cloud/advanced-l4forward.html>
- <https://developer.lazycat.cloud/spec/manifest.html>
- <https://developer.lazycat.cloud/spec/package.html>
- <https://developer.lazycat.cloud/advanced-app-interconnect.html>

## 1. 先按 LPK V2 分文件

静态元数据属于 `package.yml`，运行结构属于 `lzc-manifest.yml`。不要继续把 `package`、`version`、`name`、`description` 等字段写在 V2 manifest 顶层。

### `package.yml`

```yml
package: cloud.lazycat.app.routing-demo
version: 0.0.1
name: Routing Demo
description: 高级 HTTP 路由示例
```

### `lzc-manifest.yml`

```yml
application:
  subdomain: routing-demo
  upstreams:
    - location: /api
      backend: http://api:80
      disable_trim_location: true

    - location: /
      domain_prefix: admin
      backend: http://admin:80

    - location: /
      backend: http://main:80

services:
  main:
    image: registry.lazycat.cloud/traefik/whoami
  admin:
    image: registry.lazycat.cloud/traefik/whoami
  api:
    image: registry.lazycat.cloud/traefik/whoami
```

该镜像引用来自当前官方 HTTP 路由教程；使用前仍须核验 registry 可用性。

## 2. 选对机制与协议

| 配置 | 用途 | 支持协议/类型 |
| --- | --- | --- |
| `application.routes` | 简单 HTTP 路由、静态文件、本地程序 | `http`、`https`、`file`、`exec` |
| `application.upstreams` | 路径保留、域名前缀、Host/Header/TLS 细控 | `backend` 仅 `http`、`https`、`file` |
| `application.ingress` | 非 HTTP 的 TCP/UDP 直通 | `tcp`、`udp` |

`routes` 写作 `URL_PATH=UPSTREAM`，默认移除匹配路径前缀。例如：

```yml
application:
  routes:
    - /api/=http://backend:80/
```

请求 `/api/v1` 到后端变为 `/v1`。要保留 `/api`，使用 upstream 的 `disable_trim_location: true`（`lzcos v1.3.9+`）。

`exec://<port>,<program>` 只属于 `routes`。`upstreams[].backend` 不接受 `exec://`；需要启动程序时，使用 HTTP backend 配合 `backend_launch_command`。

## 3. 域名前缀取代不存在的附加域名字段

应用会自动接收：

```text
<实际子域名>.<微服根域>
<prefix>-<实际子域名>.<微服根域>
```

因此：

- 不存在 `application.secondary_domains`，不要添加或保留该字段。
- HTTP 按前缀分流使用 `upstreams[].domain_prefix`。
- 启动器多入口可使用 `application.entries[].prefix_domain`。
- 实际分配域名可能因冲突和多实例变化，只从 `LAZYCAT_APP_DOMAIN` 获取，不按请求的 `subdomain` 硬编码完整域名。
- 前缀域名流量会忽略 `application.ingress`，不能用于 L4 域名分流。

## 4. Host、SNI 与完整 service DNS

`upstreams[].use_backend_host: true` 只表示转发时 HTTP `Host` 改为 backend URL 的 host。TLS SNI 是另一层概念；官方没有提供单独的 SNI 字段，也没有把 `use_backend_host` 定义为 SNI 开关。

HTTPS 后端应在 `backend` 中使用与证书匹配的 DNS 主机名。`disable_backend_ssl_verify: true` 会关闭身份校验，只能作为明确知情的例外，且不能修复 HTTP Host 错误。

同一应用内部通常使用：

```text
http://<service>:<port>
```

若 route 后方是按完整入口 Host 分流的 Nginx 等代理，按官方多域名方案使用：

```text
http://<service>.<package-id>.lzcapp:<port>
```

短名与完整 `.lzcapp` 名称都是 service 定位方式，不是跨应用用户态调用接口。

## 5. 不要把服务 DNS 与跨应用访问混淆

应用隔离后，其他应用的 `.lzcapp` 名称即使可解析，也可能无法访问目标 IP。代表真实用户访问目标应用 HTTP 面应使用：

```text
http://app.<target-package-id>.lzcx/<path>
```

该入口是 app 级，不支持选择 service；要求 `lzcos >= v1.5.2`，并按场景在 `package.yml` 声明 `lzcapp.self_delegate` 或 `lzcapp.user_delegate`，使用系统下发的 `X-HC-USER-TICKET`。不要用 service DNS 绕过平台入口、实例选择和授权语义。

## 6. 复杂代理：内置 upstream 优先

优先用 `domain_prefix`、`disable_trim_location`、`use_backend_host`、`remove_this_request_headers` 等内置字段。删除 `Origin`/`Referer` 不等于正确修复 CORS，还可能弱化 CSRF/来源校验。

只有复杂正则重写、响应处理或代理日志确实需要时，才增加 Nginx/OpenResty service。当前校准官方文档没有继续提供 `app-proxy` 旧镜像版本的依据：

- 不要硬编码该旧标签；
- 不要杜撰“当前版本”；
- 可参考当前官方多域名文档中的 `registry.lazycat.cloud/snyh1010/library/nginx:54809b2f36d0ff38`，但使用前仍需现场核验；
- route 到按 Host 分流的代理时使用完整 `<service>.<package-id>.lzcapp` 形式。

## 7. L4 安全边界

```yml
application:
  ingress:
    - protocol: tcp
      description: 数据库服务
      service: database
      port: 3306
      publish_port: "3306"
```

L4 不经过平台 HTTP 鉴权：微服客户端其他进程可直接访问，端口转发还会扩大暴露面。应用必须自行实现协议认证、加密、授权和审计。

### 端口范围官方口径差异

当前官方四层能力文档使用并示例 `20000-30000`，manifest 字段表却写作 `1000~50000`。在官方统一前遵从能力文档已给出的连字符 `-` 示例，并在打包前重新校准；不要把所有 `-` 武断替换为 `~`。

`send_port_info: true` 仅用于 TCP，会在业务字节流前增加 2 字节 little-endian 原始入站端口。目标协议未适配时不能开启。

### 80/443

直接接管 80/443 会绕过账户鉴权、自动唤醒、平台证书以及 `routes`/`upstreams`。确有极特殊需求时，相关 ingress 必须显式设置：

```yml
yes_i_want_80_443: true
```

这意味着应用自行承担 TLS、证书和鉴权，绝大多数应用不应使用。

## 8. 输出前检查

1. `package.yml` 与 `lzc-manifest.yml` 是否正确拆分。
2. route/upstream 的协议是否匹配，是否误把 `exec://` 写进 backend。
3. 路径前缀、HTTP Host、TLS 证书名是否分别验证。
4. 是否误用了 `secondary_domains`、硬编码实际设备域名或跨应用 service DNS。
5. L4 是否有应用自身鉴权，是否错误接管 80/443。
6. 使用的字段、镜像和最低版本是否已通过 `spec-sync.md` 现场核对。
