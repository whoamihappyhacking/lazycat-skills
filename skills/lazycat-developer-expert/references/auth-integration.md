# 认证与用户身份 (Auth Integration)

懒猫微服通过多种方式提供身份验证，主要包括 OIDC 单点登录。

## 一、 OIDC 自动注入

开发者在 `lzc-manifest.yml` 中设置 `oidc_redirect_path` 后，系统会自动生成并注入以下环境变量到所有服务：

- **`LAZYCAT_AUTH_OIDC_CLIENT_ID`**
- **`LAZYCAT_AUTH_OIDC_CLIENT_SECRET`**
- **`LAZYCAT_AUTH_OIDC_ISSUER_URI`**
- **`LAZYCAT_AUTH_OIDC_AUTH_URI`**
- **`LAZYCAT_AUTH_OIDC_TOKEN_URI`**
- **`LAZYCAT_AUTH_OIDC_USERINFO_URI`**

### 示例 (对接 Outline):
```yaml
application:
  oidc_redirect_path: /auth/oidc.callback
services:
  outline:
    environment:
      - OIDC_CLIENT_ID=${LAZYCAT_AUTH_OIDC_CLIENT_ID}
      - OIDC_CLIENT_SECRET=${LAZYCAT_AUTH_OIDC_CLIENT_SECRET}
      - OIDC_ISSUER_URI=${LAZYCAT_AUTH_OIDC_ISSUER_URI}
```

## 二、 HTTP Header 用户身份识别

所有经过认证的请求在转发到后端前，微服网关 `lzc-ingress` 会自动注入以下 Header：

- **`X-HC-User-ID`**: 登录的用户名 (UID)。
- **`X-HC-User-Role`**: 用户角色 (`NORMAL` 或 `ADMIN`)。
- **`X-HC-Device-ID`**: 客户端在当前微服内的唯一设备 ID。
- **`X-HC-Login-Time`**: 登录时间的 Unix 时间戳。

开发者可直接根据 `X-HC-User-ID` 认为该用户已登录，无需再次验证密码。

> 完整 Header 清单（含 `X-HC-SOURCE`、`X-HC-User-Ticket`）见 `lazycat-auth-integration` 技能的 `references/http-request-headers.md`。
> 注意：`SAFE_UID` **不是**注入给应用的 Header，它只在 `injects.auth_required` 门控与 `ctx.safe_uid` 中使用。

## 三、 API Auth Token

当需要编写脚本（如 Python、bash）调用微服系统 API 时，不能依赖浏览器 Cookie，可使用 API Auth Token：

1. **生成**：只能通过 SSH 进入微服命令行生成。

   ```bash
   hc api_auth_token gen --uid admin
   ```

2. **携带**：在 HTTP 请求头中带上 **`Lzc-Api-Auth-Token: <token>`**（Header 名称固定）。

> 注意：该 Header 只用于**微服系统鉴权**，转发到应用时会被移除，因此**不能**用它调用应用自身接口。
> 详见 `lazycat-auth-integration` 技能的 `references/api-auth-token.md`。

## 四、 独立鉴权 (Public Path)

若应用某些路径无需微服登录即可访问 (如 Webhook 接口)，在 `application.public_path` 中声明：

```yaml
application:
  public_path:
    - /webhook
    - /api/public
```

支持 `!` 前缀表示排除，且排除语法优先级最高（不支持嵌套判断）：

```yaml
application:
  public_path:
    - /
    - "!/admin"
```

> 注意：放行的路径系统**依然会尝试获取登录状态**。若已登录，`X-HC-*` Header 依旧存在；若未登录，则清空相关 Header 但**不拦截请求**。
> 通配语法（是否支持 `*`）以官方 `advanced-public-api` 为准，详见 `lazycat-auth-integration` 技能的 `references/public-api.md`。
