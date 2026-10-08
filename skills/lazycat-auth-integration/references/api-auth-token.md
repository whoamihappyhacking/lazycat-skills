# API Auth Token

API Auth Token 用于脚本、命令行或 CI 访问微服 HTTP 系统 API，避免依赖浏览器 Cookie。要求 `lzcos >= 1.4.3`。

官方原文：<https://developer.lazycat.cloud/advanced-api-auth-token.html>

## 生成与管理

只能在微服命令行管理：

```bash
: "${LZC_API_UID:?请先设置最低权限用户环境变量 LZC_API_UID}"
hc api_auth_token gen --uid "$LZC_API_UID"
hc api_auth_token list
```

查看或确认删除某个 Token 时，先把真实值安全地放入环境变量；删除命令只在确认轮换后执行：

```bash
: "${LZC_API_TOKEN:?请先设置待管理的 LZC_API_TOKEN}"
hc api_auth_token show "$LZC_API_TOKEN"
# 确认不再使用后取消下一行注释：
# hc api_auth_token rm "$LZC_API_TOKEN"
```

- Token 权限等同于绑定用户；优先绑定满足任务所需的最低权限用户，不要默认使用管理员。
- 把 Token 当作密码保存，禁止提交到仓库、日志或镜像；用完及时删除/轮换。
- 未指定 `--uid` 时会自动使用管理员用户，因此自动化中应显式选择用户。

## 调用

```bash
: "${LZC_API_TOKEN:?请先设置 LZC_API_TOKEN}"
: "${LZC_BOX_DOMAIN:?请先设置不含协议的微服域名 LZC_BOX_DOMAIN}"
curl \
  -H "Lzc-Api-Auth-Token: ${LZC_API_TOKEN}" \
  "https://${LZC_BOX_DOMAIN}/sys/whoami"
```

Header 名称固定为 `Lzc-Api-Auth-Token`。正常证书可用时不要用 `curl -k` 跳过 TLS 校验。

## 平台鉴权与应用鉴权必须分开

该 Header 只用于**平台鉴权**，转发到应用前会被移除：

- 这不表示鉴权后的请求不能经平台入口到达应用；后端仍可收到平台注入的身份信息。
- 后端不会收到 `Lzc-Api-Auth-Token`，不能把它当作应用自己的 Bearer/API Token。
- 若应用接口另有业务鉴权，调用方必须另行提供应用认可的凭据。

## 上下文限制

API Token 请求不等同于真实客户端请求：

- 系统不会注入 `X-HC-Device-ID` 与 `X-HC-Device-PeerID`。
- `X-HC-Login-Time` 表示 Token 创建时间，不是某台客户端的登录时间。
- 依赖客户端信息进行回连、设备绑定或风控的能力不能直接用于此模式；代码必须允许设备字段缺失。

应用代表真实用户访问其他应用时，应使用 `app.<pkg-id>.lzcx` 与用户委托机制，而不是 API Auth Token；见 `app-interconnect.md`。