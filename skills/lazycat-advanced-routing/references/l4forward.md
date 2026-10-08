# TCP/UDP 四层转发（`application.ingress`）

> 校准基线：懒猫官方开发者文档仓库 `780d7206ce2298ee0a225e0221a993c4723d8e07`。生成配置前仍须先执行 `spec-sync.md`，以当前官方原文为准。

官方来源：

- <https://developer.lazycat.cloud/advanced-l4forward.html>
- <https://developer.lazycat.cloud/spec/manifest.html#ingressconfig-配置>
- <https://developer.lazycat.cloud/advanced-secondary-domains.html>

## 1. 只用于非平台 HTTP 入口

数据库、SSH、自定义 TCP/UDP 协议等才使用 `application.ingress`。普通 Web 页面/API 应使用 `application.routes` 或 `application.upstreams`，才能获得平台 HTTP 入口的鉴权、唤醒与证书处理。

## 2. 字段语义

| 字段 | 说明 |
| --- | --- |
| `protocol` | `tcp` 或 `udp` |
| `description` | 给管理员看的用途说明 |
| `service` | 目标 service；省略时为 `app` |
| `port` | 目标 service 端口；省略时沿用实际入站端口 |
| `publish_port` | 入站端口或端口范围；省略时等于 `port` |
| `send_port_info` | 仅 TCP；先写入 2 字节 little-endian `uint16` 原始入站端口 |
| `yes_i_want_80_443` | 明确确认接管 80/443 的高风险开关 |

匹配过程是：按应用默认域名对应的虚拟外部 IP 找到应用，再按 `protocol` 和原始入站端口匹配 ingress，最后转到 `service:port`。

## 3. LPK V2 拆分示例

下面是用于隔离测试的最小 L4 示例。它把外部 TCP 18080 直通到 whoami 的 80 端口；这条流量**没有平台 HTTP 鉴权**，生产 Web 服务不要照此绕开 `routes`。

### `package.yml`

```yml
package: cloud.lazycat.app.l4-demo
version: 0.0.1
name: L4 Demo
description: TCP 四层转发测试
```

### `lzc-manifest.yml`

```yml
application:
  image: registry.lazycat.cloud/traefik/whoami
  subdomain: l4-demo
  ingress:
    - protocol: tcp
      description: 隔离环境中的 TCP 直通测试
      publish_port: "18080"
      port: 80
```

镜像引用来自当前官方 HTTP 路由教程；使用前仍须确认 registry 可用性。验证地址应使用系统实际分配的 `LAZYCAT_APP_DOMAIN:18080`。

## 4. 端口范围：保留官方已示例的连字符

当前官方两处原文存在格式差异：

- 四层转发能力文档的可执行示例及字段说明使用 `20000-30000`。
- manifest 字段表将范围写作 `1000~50000`。

在官方统一口径前，本技能遵从能力文档已经给出的示例，使用连字符 `-`，并建议把范围写成字符串：

```yml
application:
  ingress:
    - protocol: udp
      description: 入站端口原样映射到 app 的相同端口
      service: app
      publish_port: "20000-30000"

    - protocol: tcp
      description: 16000 到 18000 都转发到 worker 的 6666
      service: worker
      port: 6666
      publish_port: "16000-18000"
```

不要因 manifest 表格里出现 `~` 就批量“修正”官方能力文档的 `-` 示例；打包前通过 `spec-sync.md` 再核对当前官方与目标系统实际支持。

## 5. `send_port_info` 会改变 TCP 字节流

多个入站端口都转到一个固定目标端口时，目标默认只知道固定端口。若业务协议需要知道原始端口，可以开启：

```yml
application:
  ingress:
    - protocol: tcp
      service: worker
      port: 6666
      publish_port: "16000-18000"
      send_port_info: true
```

目标服务接受连接后必须先读取 2 字节，并按 little-endian `uint16` 解析，再读取业务数据。现有 SSH、数据库或其他协议通常不认识这 2 字节；未经协议端适配不要开启。该字段对 UDP 无效。

## 6. 没有平台账户鉴权

L4 从原理上不能执行平台 HTTP 登录流程：

- 微服客户端上的其他进程可以直接访问开放端口。
- 用户若再使用端口转发工具，暴露面会进一步扩大。
- `application.public_path`、HTTP Header 身份以及 `routes`/`upstreams` 规则都不保护这条链路。

应用必须在自身协议中实现认证、授权、加密、限速与审计；不要把“只有微服网络能到”当成业务鉴权。

## 7. 80/443 是显式高风险例外

接管 80/443 时，流量直接进入容器，平台无法执行：

- 账户鉴权；
- 自动唤醒应用；
- HTTPS 证书配置；
- `application.routes` 与 `application.upstreams`。

确有极特殊需求时，相关 ingress 条目必须写：

```yml
application:
  ingress:
    - protocol: tcp
      port: 443
      yes_i_want_80_443: true
```

这不是“开启 HTTPS”的快捷方式。应用需要自己处理 TLS、证书、鉴权和唤醒缺失；绝大多数应用不应接管 80/443。

## 8. 域名前缀不参与 L4 分流

所有 `<prefix>-<实际子域名>` 进入的流量都会忽略 TCP/UDP Ingress，只有应用默认域名对应的 L4 入口有效。不要设计“不同域名前缀映射不同数据库端口”；域名前缀分流是 HTTP upstream 能力。

## 9. 验证清单

1. 使用对应协议客户端验证 TCP/UDP，不要只用浏览器判断。
2. 从 `LAZYCAT_APP_DOMAIN` 取得实际默认域名。
3. 分别验证范围首尾端口与范围外端口。
4. 若开启 `send_port_info`，抓取连接前两个字节确认小端端口值。
5. 从未登录或不同客户端进程测试暴露面，确认应用自己的鉴权确实生效。
6. 对 80/443 再次审查是否能改回平台 HTTP 路由。
