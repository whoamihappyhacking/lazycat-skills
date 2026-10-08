# 部署参数、清单渲染与 Injects

先读取同目录 `spec-sync.md` 并确认目标版本。详细 API 与示例由 `lazycat-dynamic-deploy` 技能维护；本页用于专家任务分流。

## 版本与文件边界

- 动态 render：`lzcos 1.3.8+`。
- 本页 LPK V2 口径：`lzcos >= 1.5.0`、`lzc-cli >= 2.0.0`。
- `package.yml`：`package`、`version`、名称、权限等静态信息。
- `lzc-manifest.yml`：`application`、`services` 等运行结构。
- `lzc-deploy-params.yml`：安装/重配时由用户提供的参数。

## 部署参数

参数类型为 `bool`、`lzc_uid`、`string`、`secret`；常用字段还有 `name`、`description`、`optional`、`default_value`、`hidden`。随机默认值从 `lzcos 1.5.0+` 支持 `$random(len=N)`。

```yaml
params:
  - id: admin_password
    type: secret
    name: 管理员密码
    description: 留空时随机生成
    default_value: "$random(len=20)"
```

不要写死弱密码，也不要把 `secret` 降级为普通 `string`。

## Go 模板 render

- `.U`/`.UserParams`：部署参数；含 `.` 的 ID 用 `index .U "listen.port"`。
- `.S`/`.SysParams`：系统参数。
- `stable_secret "seed"`：同应用同微服保持稳定的内部秘密，不要无理由截短。

模板源含 `{{ ... }}` 时不能直接当作最终 YAML 交给普通 YAML parser；应验证渲染后的 `/lzcapp/run/manifest.yml`。字段使用复数 `application.routes`，不要使用 `application.route`，也不要通过 route 暴露可能含秘密的运行态 manifest。

应用内部持久状态使用 `/lzcapp/var`；不要把旧 `/lzcapp/run/mnt/home` 文稿兼容路径当应用数据库目录。

## Injects 三阶段

- `browser`：浏览器环境，处理 HTML 页面并支持 hash 规则。
- `request`：upstream 前的同步沙盒，可改请求 Header/Body/目标。
- `response`：upstream 后的同步沙盒，可读 `ctx.status` 并改响应。

request/response 可处理 JSON 等非 HTML 流量；“非 HTML 不注入”只适用于 browser 阶段。

核心 helper：`ctx.headers`、`ctx.body`（写入是 `set`，没有 `setJSON`）、`ctx.flow`、`ctx.persist`、`ctx.proxy`。`ctx.persist` 按非空 `SAFE_UID` 隔离；browser API 异步，request/response API 同步。

### 跨阶段持久化原则

1. request 解析候选值并写 `ctx.flow`。
2. response 同时检查 HTTP 状态与目标 API 的业务成功语义，成功后才写 `ctx.persist`。
3. browser 用 `{ $persist: key, default: value }` 参数读取。

失败请求不能污染持久值。脚本来源只按官方使用 inline、`builtin://...`、`file:///...`；不要宣称支持无官方依据的远程 URL `src`。

## 最小权限

- `auth_required` 默认保持 `true`；放宽前先证明未登录场景确有必要。
- 路径匹配精确到需要范围；`/api/*` 不包含 `/api`。
- CORS 不要无条件设置 `Access-Control-Allow-Origin: *`，尤其不要与凭据访问组合。
- 密码、Token、请求 Body 不进入 `ctx.dump` 或日志。

## 官方来源

- <https://developer.lazycat.cloud/spec/deploy-params.html>
- <https://developer.lazycat.cloud/advanced-manifest-render.html>
- <https://developer.lazycat.cloud/spec/manifest.html#injects>
- <https://developer.lazycat.cloud/advanced-injects.html>
- <https://developer.lazycat.cloud/advanced-inject-passwordless-login.html>