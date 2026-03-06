# API Auth Token

API Auth Token 用于在脚本或命令行里访问系统 API 时进行鉴权，避免依赖浏览器登录态。适合自动化、运维脚本、CI 等场景。

需要 lzcos v1.4.3+。

## 生成与管理

```bash
hc api_auth_token gen
hc api_auth_token gen --uid admin
hc api_auth_token list
hc api_auth_token show <token>
hc api_auth_token rm <token>
```

- `gen` 会创建一个 UUID 形式的 token
- `--uid` 可指定绑定的用户，未指定时会自动使用管理员用户

## 调用示例

```bash
curl -k -H "Lzc-Api-Auth-Token: <token>" "https://<box-domain>/sys/whoami"
```

## 行为说明

- Header 名称固定为 `Lzc-Api-Auth-Token`
- 该 Header 只用于系统鉴权，转发到应用时会被移除
- token 权限等同于绑定用户，请妥善保存并避免泄露
- 因为部分lpk会使用鉴权信息内的客户端信息进行反向访问。此功能在API TOKEN下无法被支持
- 此模式下系统不会自动注入`X-HC-Device-PeerID`和`X-HC-Device-ID`
- 此模式下的`X-HC-Login-Time`为`Token`的创建时间
