# HTTP 请求身份 Header

客户端 HTTP(S) 流量先进入 `lzc-ingress` 完成鉴权与应用分流。官方原文：<https://developer.lazycat.cloud/http-request-headers.html>。

## 常见 Header

平台在鉴权成功并转发给应用前生成身份 Header：

| Header | 语义 |
| --- | --- |
| `X-HC-User-ID` | 登录用户 UID |
| `X-HC-User-Role` | `NORMAL` 或 `ADMIN` |
| `X-HC-Device-ID` | 该客户端在当前微服内的设备 ID |
| `X-HC-Device-PeerID` | 客户端 PeerID（内部信息） |
| `X-HC-Device-Version` | 客户端内核版本 |
| `X-HC-Login-Time` | 客户端最后登录时间的 Unix 时间戳；API Token 模式例外 |
| `X-HC-SOURCE` | 请求来源：`client`、`app:self`、`app:<pkg-id>` 或 `system` |
| `X-HC-USER-TICKET` | 应用代表真实用户继续访问时使用的临时票据能力 |
| `X-Forwarded-Proto` | 当前固定为 `https` |
| `X-Forwarded-By` | 当前固定为 `lzc-ingress` |

HTTP Header 名大小写不敏感；文档可能写作 `X-HC-User-Ticket`。

## 不是所有认证请求都有设备上下文

- **普通已登录客户端请求**：通常带用户及设备 Header。
- **API Auth Token 请求**：不注入 `X-HC-Device-ID`、`X-HC-Device-PeerID`；`X-HC-Login-Time` 是 Token 创建时间。
- **应用委托请求**：目标应用不会收到 `X-HC-Device-ID`、`X-HC-Device-PeerID`、`X-HC-Device-Version`、`X-HC-Login-Time` 这类客户端设备上下文。

因此必须把设备字段当作可选值。需要设备绑定、客户端回连或设备风控时，先拒绝/降级缺少上下文的模式，不能把 UID 当设备 ID。

## `public_path` 上的行为

平台仍会尝试鉴权，但不会因鉴权失败跳转登录：

- 鉴权成功：保留平台生成的身份 Header。
- 鉴权失败：清空相关 `X-HC-*` Header 后继续请求。

后端可以在可信 Ingress 路径上用非空 `X-HC-User-ID` 判断平台用户；不能因为请求命中 `public_path` 就假设它已登录。

## 信任边界

`X-HC-*` 的权威性来自平台 Ingress，而不是 Header 名本身：

1. 只在确认请求经过平台控制入口时信任这些值。
2. 不要信任客户端或不受控反向代理自行提供的同名 Header。
3. 不要把可绕过 Ingress 的服务端口暴露给不可信网络。
4. 使用 `X-HC-SOURCE` 区分真实客户端和应用委托来源；不要用设备 Header 推断委托来源。

`X-HC-USER-TICKET` 的来源、权限和临时性见 `app-interconnect.md`。