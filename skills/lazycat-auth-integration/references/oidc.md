# 对接微服 OIDC

懒猫微服从 `lzcos 1.3.5+` 提供统一 OIDC。LPK V2 配置示例另要求 `lzcos >= 1.5.0` 与 `lzc-cli >= 2.0.0`。

官方原文：

- <https://developer.lazycat.cloud/advanced-oidc.html>
- <https://developer.lazycat.cloud/advanced-envs.html#deploy_envs>

## 接入步骤

1. 阅读目标应用的 OIDC 文档，确认它支持的登录流、环境变量名与**准确回调路径**。
2. 在 `lzc-manifest.yml` 设置 `application.oidc_redirect_path`。只有存在该字段，系统才生成 OIDC client 环境变量。
3. 将平台变量映射到应用要求的变量。优先提供 issuer，让支持 discovery 的应用自行发现 endpoint；不支持时再逐项提供 endpoint。
4. 验证登录、登出、权限组和回调失败场景。

## LPK V2 示例

以下沿用官方文档中的 Outline 镜像、回调和 OIDC 环境变量，只展示 **OIDC 相关片段**。Outline 还依赖数据库、Redis、持久存储及其他应用配置，必须按 Outline 部署文档补齐；本片段不是可独立启动的完整应用。

```yaml
# package.yml：静态元数据片段
package: cloud.lazycat.app.outline
version: 0.0.1
name: Outline
```

```yaml
# lzc-manifest.yml：OIDC 相关运行结构片段
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

左侧变量名来自 Outline 官方接入要求；适配其他应用时必须以该应用文档为准。支持 issuer discovery 的应用可按其要求改为传入 `${LAZYCAT_AUTH_OIDC_ISSUER_URI}`。

## 平台变量

| 变量 | 用途 |
| --- | --- |
| `LAZYCAT_AUTH_OIDC_CLIENT_ID` | client ID |
| `LAZYCAT_AUTH_OIDC_CLIENT_SECRET` | 动态 client secret |
| `LAZYCAT_AUTH_OIDC_ISSUER_URI` | issuer |
| `LAZYCAT_AUTH_OIDC_AUTH_URI` | authorization endpoint |
| `LAZYCAT_AUTH_OIDC_TOKEN_URI` | token endpoint |
| `LAZYCAT_AUTH_OIDC_USERINFO_URI` | userinfo endpoint |

这些是部署时变量，仅在存在 `oidc_redirect_path` 时注入。不要把 client secret 固化到镜像或持久化数据库；应用必须能从环境变量读取变化后的值。

## Discovery 与身份

Issuer 当前形如：

```text
https://your-box-name.heiyu.space/sys/oauth
```

对应 discovery 文档可从微服 OIDC 地址获取。不要根据示例域名写死 endpoint；优先使用注入的 issuer/endpoint。

OIDC 可提供 UID 与用户组语义（管理员组为 `ADMIN`）。目标应用仍应按其 OIDC 实现正确校验 `iss`、`aud`、签名、`exp`、state/nonce；不能只解析未验证的 claim。

## 排错

- 没有 OIDC 变量：先检查 `application.oidc_redirect_path` 是否存在。
- redirect mismatch：以目标应用实际请求的回调路径修正配置，不要长期保留猜测值。
- 登录循环：核对应用外部 URL、反代 HTTPS 识别、issuer 与 cookie 配置。
- 权限错误：记录非敏感 claim 结构，核对应用的 group/role 映射；禁止记录 Token 或 client secret。