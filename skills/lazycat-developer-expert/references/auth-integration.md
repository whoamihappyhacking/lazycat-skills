# 认证与用户身份

先读取同目录 `spec-sync.md`，按目标 `lzcos`/`lzc-cli` 版本核对官方原文。详细接入流程位于 `lazycat-auth-integration` 技能；本页只保留专家路由与安全边界。

## 机制选择

| 需求 | 使用 | 关键版本 |
| --- | --- | --- |
| 统一登录 | OIDC | `lzcos 1.3.5+` |
| 自动化访问系统 API | API Auth Token | `lzcos 1.4.3+` |
| 应用代表用户访问自身/其他应用 | `.lzcx` + 委托票据 | `lzcos 1.5.2+` |
| 少数路径跳过平台 HTTP 登录 | `application.public_path` | 现场核对目标版本 |

LPK V2 示例应把 `package`、`version` 等静态字段放在 `package.yml`，运行结构放在 `lzc-manifest.yml`；构建使用 `lzc-cli >= 2.0.0`。

## OIDC

必须设置准确的 `application.oidc_redirect_path`，平台才会生成 `LAZYCAT_AUTH_OIDC_CLIENT_ID`、`LAZYCAT_AUTH_OIDC_CLIENT_SECRET`、`LAZYCAT_AUTH_OIDC_ISSUER_URI` 及各 endpoint 变量。优先将 issuer 传给支持 discovery 的应用；client secret 只从环境读取，不写入镜像或数据库。

以下是官方 Outline 的 **OIDC 相关片段**，不是可独立启动的完整部署；数据库、Redis、存储等仍须按 Outline 要求补齐。

```yaml
# lzc-manifest.yml（OIDC 相关片段）
application:
  subdomain: outline
  oidc_redirect_path: /auth/oidc.callback
  routes:
    - /=http://outline.cloud.lazycat.app.outline.lzcapp:3000
services:
  outline:
    image: registry.lazycat.cloud/tx1ee/outlinewiki/outline:fb0e2ef4f32f3601
    environment:
      - OIDC_CLIENT_ID=${LAZYCAT_AUTH_OIDC_CLIENT_ID}
      - OIDC_CLIENT_SECRET=${LAZYCAT_AUTH_OIDC_CLIENT_SECRET}
      - OIDC_AUTH_URI=${LAZYCAT_AUTH_OIDC_AUTH_URI}
      - OIDC_TOKEN_URI=${LAZYCAT_AUTH_OIDC_TOKEN_URI}
      - OIDC_USERINFO_URI=${LAZYCAT_AUTH_OIDC_USERINFO_URI}
```

左侧变量名来自 Outline；其他应用必须按其 OIDC 文档调整。

## Ingress 身份 Header

在确认请求经过平台 Ingress 后，可用非空 `X-HC-User-ID` 判断平台用户，并用 `X-HC-User-Role` 做授权。不要把所有认证方式都当成真实客户端请求：

- API Auth Token 模式不注入 `X-HC-Device-ID`、`X-HC-Device-PeerID`，其 `X-HC-Login-Time` 是 Token 创建时间。
- 委托请求不带完整客户端设备上下文。
- `SAFE_UID` 不是应用入站 Header，只用于 inject 门控/`ctx.safe_uid`。
- `X-HC-SOURCE` 只能在平台控制的 Ingress/`.lzcx` 信任边界内信任，不能接受客户端伪造值。

## API Auth Token

Header 固定为 `Lzc-Api-Auth-Token`，只做平台鉴权，转发到应用前会被移除。**移除 Token 不等于请求不能到达应用**；它表示应用后端收不到该 Token。若应用另有业务鉴权，必须另行满足，平台 Token 不能代替业务 Token。Token 权限等同绑定用户，应绑定最低权限用户并禁止入库。

## `public_path`

默认不配置。确需 webhook 等入口时只放行精确窄路径，并在应用层验证签名/令牌：

```yaml
application:
  public_path:
    - /webhooks/provider
```

鉴权失败时平台会清空身份 Header 后放行，故后端必须显式处理缺少 `X-HC-User-ID` 的请求。不要开放 `/`、管理、调试或文件读取接口；`!` 排除语法优先级最高且不支持嵌套，不能用它替代最小放行清单。

## 应用间访问

访问目标使用 `app.<target-pkg-id>.lzcx`。只回访自身申请 `lzcapp.self_delegate`；访问其他应用才申请 `lzcapp.user_delegate`。票据来自真实用户访问时 Ingress 可能附带的 `X-HC-USER-TICKET`，当前是临时行为，预计 `1.7.x` 转为显式用户授权。完整说明见同目录 `app-interconnect.md`（由认证技能同名文档同步）。

## 官方来源

- <https://developer.lazycat.cloud/advanced-oidc.html>
- <https://developer.lazycat.cloud/http-request-headers.html>
- <https://developer.lazycat.cloud/advanced-api-auth-token.html>
- <https://developer.lazycat.cloud/advanced-public-api.html>
- <https://developer.lazycat.cloud/advanced-app-interconnect.html>