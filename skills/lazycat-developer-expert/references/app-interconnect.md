# 应用间代表用户访问

该能力让一个 lzcapp 以“代表当前真实用户”的语义访问自身或其他 lzcapp 的 **HTTP** 入口。要求 `lzcos >= 1.5.2`。

官方原文：

- <https://developer.lazycat.cloud/advanced-app-interconnect.html>
- <https://developer.lazycat.cloud/http-request-headers.html>

## 入口与路由

统一访问：

```text
http://app.<target-pkg-id>.lzcx/<path>
```

例如：

```text
http://app.cloud.lazycat.app.todo.lzcx/api/tasks
```

- `.lzcx` 是 **app 级**入口，不选择具体 service。
- 它复用正常应用入口的 Ingress 路由语义；多实例目标会按真实用户 UID 路由到对应实例。
- 回访自身也使用 `app.<self-pkg-id>.lzcx`。
- service 内网 `.lzcapp` 地址不是“代表用户访问其他应用”的替代方案；它没有这里描述的票据消费与用户路由语义。

## 只申请必要权限

静态包元数据与权限写在 `package.yml`。只访问自己时：

```yaml
package: cloud.lazycat.app.example
version: 0.1.0
min_os_version: 1.5.2
permissions:
  required:
    - lzcapp.self_delegate
```

访问其他应用或 `app.home.system.lzcx` 时才申请：

```yaml
package: cloud.lazycat.app.example
version: 0.1.0
min_os_version: 1.5.2
permissions:
  required:
    - lzcapp.user_delegate
```

| 权限 | 范围 |
| --- | --- |
| `lzcapp.self_delegate` | 仅访问 `app.<self-pkg-id>.lzcx` |
| `lzcapp.user_delegate` | 代表用户访问其他应用或 `app.home.system.lzcx` |

不要因“以后可能需要”同时申请两项；按实际调用目标选择最小权限。

## `X-HC-USER-TICKET` 从哪里来

当前没有独立的主动申请票据 API。当前流程是：

1. 应用在 `package.yml` 声明相应委托权限。
2. 真实用户通过正常微服 HTTP 入口访问应用。
3. Ingress **可能**在应用收到的入站请求中附带 `X-HC-USER-TICKET`（Header 名大小写不敏感）。
4. 应用从该请求读取票据；后续调用 `.lzcx` 时携带它。

```bash
: "${LZC_USER_TICKET:?请先设置当前用户票据 LZC_USER_TICKET}"
: "${LZC_TARGET_PKG_ID:?请先设置目标包 ID LZC_TARGET_PKG_ID}"
curl \
  -H "X-HC-USER-TICKET: ${LZC_USER_TICKET}" \
  "http://app.${LZC_TARGET_PKG_ID}.lzcx/api/tasks"
```

票据是敏感凭据：不要写日志、返回前端、跨用户复用或以明文长期保存。若当前流程必须暂存，应绑定平台 UID 与服务端会话，并允许票据缺失/失效后重新走授权流程。

## 临时性与版本演进

当前默认下发行为是**临时方案，不提供长期兼容保证**：

- 不能假设每个首个真实用户请求都必然带票据。
- 不能假设票据格式、有效期或默认下发行为稳定。
- 官方预计在 `lzcos 1.7.x` 改为用户明确授权后才能获取。
- 新应用必须为“票据缺失/失效/需要重新授权”设计可恢复流程，不能把当前默认行为固化成唯一登录路径。

## 目标应用收到什么

系统会消费并移除上游传入的 `X-HC-USER-TICKET`，再向目标应用注入用户与来源语义。委托请求不携带完整客户端设备上下文：

- 可使用：`X-HC-User-ID`、`X-HC-User-Role`、`X-HC-SOURCE`。
- 不应期待：`X-HC-Device-ID`、`X-HC-Device-PeerID`、`X-HC-Device-Version`、`X-HC-Login-Time`。

`X-HC-SOURCE` 当前语义：

| 值 | 来源 |
| --- | --- |
| `client` | 真实客户端访问 |
| `app:self` | 应用代表当前用户访问自己 |
| `app:<pkg-id>` | 其他应用代表当前用户访问目标应用 |
| `system` | 系统来源 |

## `X-HC-SOURCE` 信任边界

`X-HC-SOURCE` 只有在请求确定经过平台控制的 Ingress/`.lzcx` 转发边界时才可信。应用不得信任客户端、直连服务端口或不受控代理自行提供的同名 Header；也不要把 Header 名本身当作防伪机制。

目标应用应：

1. 用 `X-HC-User-ID` 做用户级业务鉴权。
2. 需要区分真实客户端与应用委托时，再检查 `X-HC-SOURCE`。
3. 对 `app:<pkg-id>` 仅授予该来源完成当前操作所需的权限；高风险操作仍做细粒度授权与审计。
4. 避免把可绕过平台 Ingress 的后端端口暴露给不可信网络。

## 验证

- 分别验证无票据、无权限、错误权限、票据失效与正常委托。
- 验证多实例目标按 UID 路由，不共享用户数据。
- 验证目标后端看不到原始 Ticket，且设备 Header 缺失时安全降级。
- 验证伪造 `X-HC-SOURCE` 的直连请求不会获得平台身份权限。