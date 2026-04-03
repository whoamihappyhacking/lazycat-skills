# 认证与用户身份 (Auth Integration)

懒猫微服通过多种方式提供身份验证，主要包括 OIDC 单点登录。

## 一、 OIDC 自动注入

开发者在 `lzc-manifest.yml` 中设置 `oidc_redirect_path` 后，系统会自动生成并注入以下环境变量到所有服务：

- **`LAZYCAT_AUTH_OIDC_CLIENT_ID`**
- **`LAZYCAT_AUTH_OIDC_CLIENT_SECRET`**
- **`LAZYCAT_AUTH_OIDC_ISSUER`** (以及各端点 URI)

### 示例 (对接 Outline):
```yaml
application:
  oidc_redirect_path: /auth/oidc.callback
services:
  outline:
    environment:
      - OIDC_CLIENT_ID=${LAZYCAT_AUTH_OIDC_CLIENT_ID}
      - OIDC_CLIENT_SECRET=${LAZYCAT_AUTH_OIDC_CLIENT_SECRET}
```

## 二、 HTTP Header 用户身份识别

所有请求在转发到后端前，微服网关会自动注入以下 Header：

- **`SAFE_UID`**: 当前用户的唯一 ID。
- **`SAFE_USER_GROUPS`**: 当前用户的权限组 (如 `ADMIN`)。

开发者可直接根据 `SAFE_UID` 决定是否授权或展示对应数据。

## 三、 API Auth Token

对于外部应用调用，可通过 API Auth Token 绕过浏览器登录：

1. **`ctx.api_auth.get_token()`**: 获取临时 Token。
2. **`Authorization: Bearer <token>`**: 在请求头中携带 Token。

## 四、 独立鉴权 (Public Path)

若应用某些路径无需微服登录即可访问 (如 Webhook 接口)，在 `application.public_path` 中声明：

```yaml
application:
  public_path:
    - /webhook/*
    - /api/public/*
```
