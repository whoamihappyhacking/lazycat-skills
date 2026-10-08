# `application.upstreams` 与复杂反向代理（LPK V2）

> 校准基线：懒猫官方开发者文档仓库 `780d7206ce2298ee0a225e0221a993c4723d8e07`。生成配置前仍须先执行 `spec-sync.md`，以当前官方原文为准。

官方来源：

- <https://developer.lazycat.cloud/advanced-route.html>
- <https://developer.lazycat.cloud/spec/manifest.html#upstreamconfig-配置>
- <https://developer.lazycat.cloud/advanced-secondary-domains.html>

## 1. 优先使用平台内置 upstream

`application.upstreams` 自 `lzcos v1.3.8+` 提供比 `routes` 更细的 HTTP 控制，并可与 `routes` 共存。

| 字段 | 用途 |
| --- | --- |
| `location` | 匹配入口路径 |
| `backend` | 上游 URL；只支持 `http`、`https`、`file` |
| `domain_prefix` | 只匹配指定域名前缀 |
| `disable_trim_location` | 保留匹配的 `location` 前缀，要求 `lzcos v1.3.9+` |
| `use_backend_host` | 将 HTTP Host 改为 backend URL 的 host |
| `backend_launch_command` | 自动启动本地后端程序；不要写 `exec://` backend |
| `trim_url_suffix` | 删除转发 URL 末尾指定字符 |
| `disable_backend_ssl_verify` | 关闭后端 TLS 证书校验，高风险 |
| `disable_auto_health_checking` | 不为该条目自动生成健康检查 |
| `disable_url_raw_path` | 删除 HTTP header 中的 raw URL |
| `remove_this_request_headers` | 转发前删除指定请求头 |
| `fix_websocket_header` | 修正 `Sec-Websocket-*` 的大小写 |
| `dump_http_headers_when_5xx` | 上游 5xx 时输出请求 header，注意敏感信息 |
| `dump_http_headers_when_paths` | 指定路径输出请求 header，注意敏感信息 |

不要凭字段名猜行为；用到少见字段时必须回查当前 manifest 规范和目标系统版本。

## 2. LPK V2 拆分示例

### `package.yml`

```yml
package: cloud.lazycat.app.advanced-route-demo
version: 0.0.1
name: Advanced Route Demo
description: Upstream 路由示例
permissions:
  required:
    - net.internet
```

示例访问公网 HTTPS backend，因此声明 `net.internet`。如果应用只访问自身 service，不要无故申请该权限。

### `lzc-manifest.yml`

```yml
application:
  subdomain: advanced-route-demo
  upstreams:
    - location: /mirror
      backend: https://appstore.lazycat.cloud/
      use_backend_host: true
      disable_auto_health_checking: true

    - location: /api
      backend: http://whoami:80
      disable_trim_location: true

    - location: /
      domain_prefix: debug
      backend: http://whoami:80

services:
  whoami:
    image: registry.lazycat.cloud/traefik/whoami
```

公网 backend 和 whoami 镜像引用均取自当前官方路由教程；实际使用前仍须确认服务语义与 registry 可用性。

## 3. 路径保留

`routes` 默认剥离入口前缀；upstream 也应显式表达是否保留：

假设同一 manifest 已定义监听 8080 的 `services.backend`：

```yml
application:
  upstreams:
    - location: /api
      backend: http://backend:8080
      disable_trim_location: true
```

请求 `/api/v1` 转发后仍包含 `/api/v1`。不要通过增加重复 backend path 猜测拼接结果；部署后让测试后端回显实际 path。

## 4. HTTP Host 与 TLS SNI 必须分开判断

下面使用官方路由文档中的真实 HTTPS 上游：

```yml
application:
  upstreams:
    - location: /
      backend: https://appstore.lazycat.cloud/
      use_backend_host: true
```

- 默认行为：转发时通常保留浏览器请求的 Host，适合后端按入口域名分流。
- `use_backend_host: true`：HTTP Host 使用 `appstore.lazycat.cloud`，适合公网虚拟主机或会校验 Host 的后端。
- TLS SNI 属于 TLS 握手层，不是 HTTP Host。官方字段说明只承诺 `use_backend_host` 改 Host，并没有单独的 SNI 配置字段；不要宣称该开关一定改 SNI。
- HTTPS backend 应直接使用与证书匹配的 DNS 主机名。若把 backend 写成 IP，即使改 Host，也不能据此保证 SNI 与证书验证正确。

假设同一 manifest 已定义监听 4443、使用自签证书的 `services.legacy-backend`，且无法建立信任链时才考虑：

```yml
application:
  upstreams:
    - location: /legacy
      backend: https://legacy-backend:4443
      disable_backend_ssl_verify: true
```

该开关会失去对后端身份的证书验证，不解决 HTTP Host 错误，也不应成为默认配置。

## 5. Header 删除不是通用 CORS 修复

以下片段假设同一 manifest 已定义监听 8080 的 `services.legacy`：

```yml
application:
  upstreams:
    - location: /legacy-api
      backend: http://legacy:8080
      remove_this_request_headers:
        - Origin
        - Referer
```

只在已确认后端因这些请求头拒绝请求时使用。删除 `Origin`/`Referer` 会改变后端安全判断，不能代替正确的 CORS 响应头、CSRF 防护或业务鉴权。

## 6. 何时才增加应用内反向代理

只有内置 `routes`/`upstreams` 无法表达下列需求时才增加 Nginx/OpenResty 等代理 service：

- 复杂正则重写或响应内容处理；
- 一组域名/路径规则必须由同一代理统一控制；
- 需要代理自身的访问日志或模块能力。

当前校准的官方文档没有提供可继续硬编码的 `app-proxy` 旧镜像版本依据。不要复制旧标签，也不要杜撰“最新版本”。下面使用官方当前多域名示例中的 Nginx 镜像引用；它只是已知参考，使用前仍需现场核验。

### `package.yml`

```yml
package: cloud.lazycat.app.proxy-routing-demo
version: 0.0.1
name: Proxy Routing Demo
description: 应用内反向代理示例
```

### `lzc-manifest.yml`

```yml
application:
  subdomain: proxy-routing-demo
  routes:
    # 完整 service DNS 使 edge 收到完整入口 Host，供 server_name 分流。
    - /=http://edge.cloud.lazycat.app.proxy-routing-demo.lzcapp:80

services:
  edge:
    image: registry.lazycat.cloud/snyh1010/library/nginx:54809b2f36d0ff38
    setup_script: |
      cat <<'EOF' > /etc/nginx/conf.d/default.conf
      server {
        listen 80;
        server_name ~^admin-.*;
        location / {
          proxy_pass http://admin:80;
        }
      }

      server {
        listen 80 default_server;
        server_name _;
        location / {
          proxy_pass http://main:80;
        }
      }
      EOF

  main:
    image: registry.lazycat.cloud/traefik/whoami

  admin:
    image: registry.lazycat.cloud/traefik/whoami
```

注意：

1. 不需要也不存在 `application.secondary_domains`；`admin-<实际子域名>` 自动属于该应用。
2. `setup_script` 与同一 service 的 `entrypoint`、`command` 冲突，不要同时配置。
3. 示例没有注入 Basic Auth 凭据。若代理必须携带密钥，使用项目认可的密钥管理方式，禁止把真实密码或 Token 写进技能或 manifest。
4. 容器名是运行时生成的，不要硬编码。先执行 `lzc-cli docker ps`，再用 `lzc-cli docker logs -f <容器名>` 查看代理日志。

## 7. 排查顺序

1. 确认请求命中正确的 `domain_prefix` 与 `location`。
2. 让后端回显 path 和 Host，核对前缀是否保留。
3. 对 HTTPS backend 分别检查 DNS、TLS 证书名与 HTTP Host，不把三者混成一个问题。
4. 检查目标 service 健康状态与监听端口。
5. 只有在内置 upstream 无法表达需求时才引入额外代理层。
