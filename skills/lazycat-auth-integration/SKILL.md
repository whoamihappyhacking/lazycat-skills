---
name: lazycat-auth-integration
description: 懒猫微服应用接入 OIDC、Ingress 身份 Header、API Auth Token、public_path 与应用间用户委托访问时使用的认证安全指南。
---

# 懒猫微服认证接入

先确认目标 `lzcos` 与 `lzc-cli` 版本；编写配置前必须读取 `references/spec-sync.md`，按其中流程现场核对官方原文。LPK V2 示例要求 `lzcos >= 1.5.0`、`lzc-cli >= 2.0.0`；更老目标不能直接套用。

## 先选机制

| 需求 | 机制 | 最低系统版本 | 必读 |
| --- | --- | --- | --- |
| 应用使用统一登录 | OIDC | `1.3.5+` | `references/oidc.md` |
| 后端识别平台用户 | Ingress 注入 Header | 以目标版本官方文档为准 | `references/http-request-headers.md` |
| 脚本访问系统 API | API Auth Token | `1.4.3+` | `references/api-auth-token.md` |
| 极少数路径绕过平台 HTTP 登录 | `public_path` | 以目标版本官方文档为准 | `references/public-api.md` |
| 应用代表当前用户访问自身/其他应用 | `.lzcx` + 委托票据 | `1.5.2+` | `references/app-interconnect.md` |

## OIDC 最小流程

1. 从上游应用文档确认**准确**回调路径。
2. 在 `lzc-manifest.yml` 设置 `application.oidc_redirect_path`；没有此字段就不会生成 OIDC 环境变量。
3. 仅把应用需要的 OIDC 变量传入对应服务，优先使用 issuer discovery。
4. 不把动态生成的 client secret 写入镜像、数据库或文档。

以下沿用官方 Outline 镜像与回调，只展示 **OIDC 相关片段**；Outline 所需数据库、Redis、存储及其他环境变量仍须按其部署文档配置，本片段不能独立启动。

```yaml
# package.yml（LPK V2 静态元数据片段）
package: cloud.lazycat.app.outline
version: 0.0.1
name: Outline
```

```yaml
# lzc-manifest.yml（OIDC 相关运行配置片段）
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

左侧变量名来自 Outline 官方接入要求；适配其他应用时必须按该应用文档调整。右侧 `LAZYCAT_AUTH_OIDC_*` 是平台变量。

## 身份 Header 的边界

- 仅在请求确定经过平台 Ingress 的信任边界时，才把平台生成的 `X-HC-*` 当作身份依据；不要信任客户端自行传入的同名值。
- 普通已登录客户端请求通常包含用户与设备上下文；**API Auth Token 不注入 `X-HC-Device-ID`/`X-HC-Device-PeerID`，委托请求也不带完整客户端设备上下文**。
- `public_path` 上鉴权失败时，平台会清空身份 Header。因此代码必须先检查 `X-HC-User-ID` 是否存在，不能把“路径可访问”当作“用户已登录”。

## API Auth Token 的正确语义

请求使用 `Lzc-Api-Auth-Token: ${LZC_API_TOKEN}` 做**平台鉴权**，该敏感 Header 在转发到应用前会被移除。移除 Token 不等于鉴权后的请求不能到达应用；它只表示后端收不到该 Token。若应用接口还有自己的业务鉴权，调用方必须另行满足，不能把平台 Token 当作业务 Token。

## `public_path` 最小权限原则

默认不要配置。确需 webhook、分享下载等入口时，只放行经过风险审查的精确窄路径，并在应用层校验签名、一次性令牌或等价凭据；不要无条件开放 `/`、管理接口、文件读取接口或调试接口。

## 交付检查

- `package.yml` 与 `lzc-manifest.yml` 已按 LPK V2 分离，字段与目标版本匹配。
- OIDC 回调路径与应用实际回调完全一致，issuer/endpoints 未凭空拼接。
- 无真实 Token、client secret、弱口令或真实设备域名。
- Header 信任边界明确，缺少设备 Header 时能够安全降级。
- `public_path` 已缩到最小范围，并有应用层鉴权与未登录测试。
- 应用互访只申请 `self_delegate`/`user_delegate` 中实际需要的一项。