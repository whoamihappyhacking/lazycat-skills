# HTTP 路由规则（LPK V2）

> 校准基线：懒猫官方开发者文档仓库 `780d7206ce2298ee0a225e0221a993c4723d8e07`。生成配置前仍须先执行 `spec-sync.md`，以当前官方原文为准。

官方来源：

- <https://developer.lazycat.cloud/advanced-route.html>
- <https://developer.lazycat.cloud/getting-started/http-route-backend.html>
- <https://developer.lazycat.cloud/spec/manifest.html>
- <https://developer.lazycat.cloud/advanced-app-interconnect.html>

## 1. `routes` 的语法与协议

`application.routes` 是 `[]string`，每条按 `URL_PATH=UPSTREAM` 声明。`URL_PATH` 是不含 hostname 的入口路径。

`routes` 支持三类上游：

```text
file:///<目录>
exec://<端口>,<可执行文件路径>
http://<主机>[:端口][/路径]
https://<主机>[:端口][/路径]
```

不要把它与 `application.upstreams` 混为一谈：`upstreams[].backend` 只支持 `http`、`https`、`file`，不接受 `exec://`。

## 2. 默认会移除入口路径前缀

```yml
application:
  routes:
    - /api/=http://backend:80/
```

访问 `/api/v1` 时，后端收到 `/v1`。需要保留 `/api` 时，改用：

```yml
application:
  upstreams:
    - location: /api
      backend: http://backend:80
      disable_trim_location: true
```

`disable_trim_location` 要求 `lzcos v1.3.9+`。路径更具体的 route 应放在宽泛的 `"/="` 之前。

## 3. LPK V2 拆分示例

下面分别是两个文件，不要合并回旧式 manifest。

### `package.yml`

```yml
package: cloud.lazycat.app.route-demo
version: 0.0.1
name: Route Demo
description: HTTP 路由示例
```

### `lzc-manifest.yml`

```yml
application:
  subdomain: route-demo
  routes:
    - /inspect/=http://whoami:80/
    - /=file:///lzcapp/pkg/content/

services:
  whoami:
    image: registry.lazycat.cloud/traefik/whoami
```

该镜像引用来自当前官方“有后端时如何通过 HTTP 路由对接”示例；现场仍需确认目标 registry 可拉取。

## 4. `http(s)`：只转发，不启动服务

同一应用内优先使用 service 短名。下面使用官方当前教程中的 whoami 镜像和真实监听端口 80，仅演示 `http://` route 的转发机制：

```yml
application:
  routes:
    - /=http://whoami:80

services:
  whoami:
    image: registry.lazycat.cloud/traefik/whoami
```

- `whoami` 由同一 `lzc-manifest.yml` 的 `services.whoami` 提供。
- `http://...` 只负责转发，不会启动后端程序。
- 该例仅用于验证 HTTP 路由，不代表生产应用的业务后端设计。
- 外部 HTTPS 入口默认受平台登录态保护；只有明确需要匿名访问的最小路径才放入 `application.public_path`。

### service 短名与完整 `.lzcapp` 名称

同一应用内常规调用使用 `<service>` 即可。官方还给出完整形式：

```text
<service>.<package-id>.lzcapp
```

当 route 后方是需要读取完整入口 Host 的 Nginx 等代理时，应按官方多域名方案使用完整形式。以下片段假设同一 manifest 已定义 `services.edge`：

```yml
application:
  routes:
    - /=http://edge.cloud.lazycat.app.route-demo.lzcapp:80
```

这仍是**当前应用内部的 service 定位**，不是通用跨应用 API。

### 不要把服务 DNS 与跨应用访问混淆

应用隔离后，即使另一个应用的 `.lzcapp` 名称能够解析，也不代表目标 IP 可访问。若需要代表真实用户访问另一个应用的 HTTP 面：

```text
http://app.<target-package-id>.lzcx/<path>
```

`.lzcx` 是 app 级入口，不能选择目标 service；还必须按官方“应用间访问”文档声明 `lzcapp.self_delegate` 或 `lzcapp.user_delegate`，传递系统下发的用户票据，并满足对应系统版本。不要用 service DNS 绕过这套入口与授权语义。

## 5. `file`：直接提供只读打包内容

```yml
application:
  routes:
    - /=file:///lzcapp/pkg/content/web/
```

构建时打入 content 的文件会在运行时出现在 `/lzcapp/pkg/content/`。静态资源不需要额外 service。

## 6. `exec`：启动本地程序并转发

```yml
application:
  routes:
    - /=exec://3000,/lzcapp/pkg/content/backend
```

系统执行指定程序，并假设它在 `127.0.0.1:3000` 提供 HTTP 服务。系统不会验证该端口一定由这个程序启动。适合内置 `app` 容器里的简单后端；已有独立 service 时使用 `http://<service>:<port>`。

高级路由中若需要同类启动行为，使用 `backend_launch_command`，不要把 `exec://` 写入 `upstreams[].backend`。

## 7. Host 与 HTTPS 名称

`routes` 没有 `use_backend_host` 开关。需要显式切换后端 HTTP Host 时使用 `application.upstreams`：

```yml
application:
  upstreams:
    - location: /
      backend: https://appstore.lazycat.cloud/
      use_backend_host: true
```

`use_backend_host` 只承诺改变 HTTP `Host`。TLS SNI 与 HTTP Host 是不同层；官方规范没有单独的 SNI 字段。HTTPS backend 应使用与证书匹配的 DNS 主机名，不要把 `use_backend_host` 描述成 SNI 开关。

## 8. 最小验证

1. 用已登录浏览器分别请求根路径与更具体路径。
2. 确认后端实际收到的 path 与预期一致。
3. 检查 Host 敏感后端返回的状态；需要时转为 `upstreams`。
4. 用 `lzc-cli project info` 确认部署版本已生效，并用 `lzc-cli project log -s <service> -f` 查看目标 service 日志。
