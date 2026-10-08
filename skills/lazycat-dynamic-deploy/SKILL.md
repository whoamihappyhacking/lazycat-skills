---
name: lazycat-dynamic-deploy
description: 懒猫微服应用需要部署参数、Go 模板清单渲染或 browser/request/response 脚本注入时使用的动态部署指南。
---

# 懒猫微服动态部署与注入

任何配置生成前，先确认目标 `lzcos` 与 `lzc-cli`，并读取 `references/spec-sync.md` 按流程现场校准官方规范。本文示例按 LPK V2（`lzcos >= 1.5.0`、`lzc-cli >= 2.0.0`）组织；动态渲染能力始于 `lzcos 1.3.8+`。

## 选择正确层次

| 要解决的问题 | 机制 | 必读 |
| --- | --- | --- |
| 安装/重配时收集用户输入 | `lzc-deploy-params.yml` | `references/deploy-params.md` |
| 将部署输入或系统值写入运行清单 | Go `text/template` 渲染 | `references/manifest-render.md` |
| 按页面或请求动态改写行为 | `application.injects` | `references/injects.md` |

不要用 deploy render 做请求级路由，也不要用 inject 替代静态可表达的 manifest 配置。

## 部署参数与渲染

`lzc-deploy-params.yml`：

```yaml
params:
  - id: target_host
    type: string
    name: 目标主机
    description: 要连接的主机名或 IP
  - id: admin_password
    type: secret
    name: 管理员密码
    description: 留空时由系统生成随机初始密码
    default_value: "$random(len=20)"
```

`lzc-manifest.yml` 片段：

```yaml
services:
  web:
    environment:
      TARGET_HOST: {{ .U.target_host | quote }}
      ADMIN_PASSWORD: {{ .U.admin_password | quote }}
      INTERNAL_SECRET: {{ stable_secret "internal_secret" | quote }}
```

- 用户参数为 `.U`/`.UserParams`；含 `.` 的 ID 用 `index .U "listen.port"`。
- 系统参数为 `.S`/`.SysParams`。
- `stable_secret` 用于跨重启稳定的内部随机秘密；不要截成短弱口令。
- 含 `{{ ... }}` 的模板源不能直接当作最终 YAML 交给普通 YAML 解析器；应检查渲染后的 `/lzcapp/run/manifest.yml`。
- LPK V2 的静态元数据只写 `package.yml`，不要混回 manifest 顶层。

## 三阶段 inject

- `browser`：真实浏览器环境；面向 HTML 页面，可使用 hash 匹配。
- `request`：转发 upstream 前的 lzcinit 同步沙盒；可改 Header/Body/路由。
- `response`：upstream 响应后的 lzcinit 同步沙盒；可按状态码提交状态或改响应。

`request`/`response` 可处理 JSON 等非 HTML 流量；只有 browser 注入要求可承载脚本的 HTML 页面。匹配规则使用 `when`/`unless`/`do`，不存在 `include`/`exclude`/`mode`/`scripts`。

需要跨请求记住用户状态时：request 只把候选值写入 `ctx.flow`，response **确认业务成功**后才写 `ctx.persist`，browser 再通过 `$persist` 参数读取。不能在 request 阶段先持久化失败的登录/改密数据。

```yaml
application:
  injects:
    - id: login-autofill
      when:
        - /login
      do:
        - src: builtin://simple-inject-password
          params:
            user: admin
            password:
              $persist: app.password
            autoSubmit: false
```

脚本来源只使用官方列出的 inline、`builtin://...` 或 `file:///...`；不要宣称或依赖未在官方规范列出的远程 URL 脚本来源。

## 安全与交付检查

- 参数只收集实际需要的数据，密码使用 `secret`，示例不写死弱密码。
- `auth_required` 保持默认 `true`，除非确有未登录流量需求并完成风险分析；`ctx.persist` 要求非空 `ctx.safe_uid`。
- `when` 精确到所需路径；`/api/*` 不匹配 `/api`，需要时分别声明。
- 正式脚本优先随包提供；不加载远程可变代码。
- request/response 不使用 `Promise`/`async`；browser 的 `ctx.persist` API 是异步的。
- `ctx.dump` 不输出密码、Token 或请求体敏感信息。
- 对照 `references/injects.md` 的完整内置参数表和官方专题后再交付。