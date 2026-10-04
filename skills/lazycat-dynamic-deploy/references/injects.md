# 脚本注入（injects）

## 概述

`injects` 用于在**不修改 OCI image 或应用源码**的前提下，按规则注入脚本，覆盖浏览器行为、请求行为和响应行为。此功能需要 `lzcos 1.5.0+`。

> **字段定义以官方为准。** 本文如与官方不一致，以官方为权威：
> - <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/manifest.md>（`InjectConfig` / `InjectScriptConfig` 字段表）
> - <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-injects.md>（匹配机制、`ctx` API、排错）
>
> 打包/构建前请按 `spec-sync.md` 校准流程拉取最新原文。

## 快速示例

```yml
application:
  injects:
    - id: login-autofill
      when:
        - /#login
        - /#signin
      do:
        - src: builtin://simple-inject-password
          params:
            user: "admin"
            password: "CHANGE_ME"   # 请改为部署参数注入，勿写死
```

## 字段一览（`InjectConfig`）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `string` | 注入配置的唯一 ID |
| `on` | `string` | 阶段：`browser`（默认）/ `request` / `response` |
| `when` | `[]string` | 命中条件（OR），至少 1 条 |
| `unless` | `[]string` | 排除条件（OR），可选 |
| `prefix_domain` | `string` | 仅匹配 `<prefix>-<subdomain>...` 的域名前缀 |
| `auth_required` | `bool` | 是否要求请求带合法 `SAFE_UID`，默认 `true` |
| `do` | `string \| []InjectScriptConfig` | 脚本定义，见下节 |

**注意：不存在 `include` / `exclude` / `mode` / `scripts` 字段。** 早期草稿曾使用过这些名字，现行规范已改为 `when` / `unless` / `do`。

## `do` 的两种写法

- **short syntax**：`do` 直接写脚本字符串（只对应一条脚本）。
- **long syntax**：`do` 写 `[]InjectScriptConfig`，可配置多条脚本与 `params`。

`InjectScriptConfig`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `src` | `string` | 脚本来源，支持 `builtin://...`、`file:///...`、inline script |
| `params` | `map[string]any` | 传递给脚本的参数 |

```yml
# short syntax：单条脚本
- id: inject-basic-auth-header
  auth_required: false
  on: request
  when:
    - /api/*
  do: |
    ctx.headers.set("Authorization", "Basic " + ctx.base64.encode("user:pass"));

# long syntax：多条脚本 + params
- id: remove-cors
  on: response
  when:
    - /api/*
  unless:
    - /api/admin/*
  do:
    - src: |
        ctx.headers.del("Access-Control-Allow-Origin");
        ctx.headers.del("Access-Control-Allow-Credentials");
```

## 匹配规则

### 单条规则格式

```text
<path-pattern>[?<query>][#<hash-pattern>]
```

### 规则语义

- **仅支持后缀 `*` 作为前缀匹配**；无 `*` 时为精确匹配。
- 通配规则采用严格的**字符串前缀匹配**：`"/api/*"` 的匹配前缀是 `"/api/"`，因此匹配 `"/api/"` 与 `"/api/users"`，但**不匹配** `"/api"`。
- `query` token 支持 `key` 或 `key=value`，单条规则内为 **AND**（全部满足）。
- query 为 contains 语义：请求允许包含额外参数。
- `#hash` **仅 `browser` 阶段支持**；`request`/`response` 阶段不支持 hash 规则（写了不会生效）。

示例：

| 规则 | 匹配 |
| --- | --- |
| `"/api"` | 仅精确匹配 `/api` |
| `"/api/*"` | 匹配 `/api/` 前缀，**不**匹配 `/api` |
| `"/api/*?v=2"` | `/api/` 前缀且 query 包含 `v=2` |
| `"/#login"` | hash 为 `login`（仅 browser） |

### `when` 与 `unless` 的关系

- `when` 为 **OR**：任意一条命中即进入候选。
- `unless` 为 **OR**：任意一条命中即排除。
- 最终 `matched = whenMatched && !unlessMatched`。

若需同时匹配目录根路径与其下路径，应在同一个 `when` 中分别声明精确规则和通配规则：

```yml
when:
  - /api
  - /api/*
```

若需排除精确路径 `/api`、但匹配其他以 `/api` 开头的路径：

```yml
when:
  - /api*
unless:
  - /api
```

这会匹配 `/api/`、`/api/users` 和 `/api-v2`，但不匹配 `/api`。

### 域名与鉴权过滤

- `prefix_domain`：非空时，仅匹配域名前缀为 `<prefix>-` 的请求。
- `auth_required`：默认 `true`。请求**没有合法 `SAFE_UID` 时跳过当前 inject**。当 `auth_required=false` 且请求无合法登录态时，`ctx.safe_uid` 可能为空字符串。

## 阶段与执行环境

每个 inject 只属于一个阶段：

- `on=browser`：脚本在应用页面的**真实浏览器环境**执行。
- `on=request`：脚本在 **lzcinit 沙盒**中执行，时机是请求转发到 upstream **前**。
- `on=response`：脚本在 **lzcinit 沙盒**中执行，时机是收到 upstream 响应**后**。

执行顺序与中断：

- 先按 `application.injects` 声明顺序，再按同一 inject 的 `do[]` 声明顺序。
- 命中策略为 `all-match-run`：同阶段所有命中 inject 都执行。
- `request`/`response` 阶段中，`ctx.response.send(...)` 或 `ctx.proxy.to(...)` 生效后**立即短路**，停止当前阶段后续脚本。
- 任一脚本报错，当前阶段立即终止并返回错误。
- `request`/`response` 阶段为**同步执行模型**，不支持 `Promise` / `async`；`browser` 阶段允许异步。

## Hash 的 hard/soft 匹配

- `path` / `query` 是服务端可见条件，属 **hard 匹配**。
- `hash` 是服务端不可见条件，自动降级为**客户端 soft 匹配**（仅 browser）。

这意味着可能出现"**已注入 wrapper 但因 hash 不匹配未执行脚本**"，这是预期行为。

## Browser 阶段的触发时机与运行时对象

wrapper 的触发时机：

1. 页面加载后执行一次评估（`trigger=load`）。
2. 监听 `hashchange`，每次 hash 变化后再次评估（`trigger=hashchange`）。
3. 只要命中规则就执行脚本，**不做内置去重**。

脚本内可读取（官方 `ctx.runtime`）：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ctx.runtime.executedBefore` | `bool` | 当前页面生命周期内是否执行过 |
| `ctx.runtime.executionCount` | `int` | 执行次数（从 `1` 开始） |
| `ctx.runtime.trigger` | `string` | 触发来源（`load` / `hashchange`） |

示例（脚本侧去重）：

```js
(() => {
  const runtime = ctx.runtime || {};
  if (runtime.executedBefore) {
    return;
  }
  console.log("inject params:", ctx.params);
})();
```

## 脚本来源（`src`）

| 形式 | 说明 |
| --- | --- |
| `builtin://<name>` | 使用 lzcinit 内置脚本 |
| `file:///path` | 读取应用文件系统内脚本（常见路径 `/lzcapp/pkg/content/`） |
| `http(s)://...` | 远程脚本，**建议仅调试使用** |

## `ctx` API 速查

| helper | browser | request | response |
| --- | --- | --- | --- |
| `ctx.params` / `ctx.base64` / `ctx.persist` | 是 | 是 | 是 |
| `ctx.headers` / `ctx.body` / `ctx.flow` / `ctx.fs` | 否 | 是 | 是 |
| `ctx.client` / `ctx.dev` / `ctx.net` / `ctx.dump` | 否 | 是 | 是 |
| `ctx.response` / `ctx.proxy` | 否 | 是 | 是 |
| `ctx.status`（响应状态码） | 否 | 否 | 是 |

常用签名（完整列表以官方 `advanced-injects.md` 为准）：

```js
// headers（request/response）
ctx.headers.get(name); ctx.headers.set(name, value); ctx.headers.del(name);

// body（request/response）—— 注意：设置用 set，没有 setJSON
ctx.body.getText(opts?); ctx.body.getJSON(opts?); ctx.body.set(body, opts?);

// 短路响应 / 改写反代目标
ctx.response.send(status, body?, opts?);
ctx.proxy.to(url, { use_target_host, timeout_ms, path, query, via, on_fail });
```

## 内置脚本

当前最常用的是 `builtin://simple-inject-password`：自动填充账号/密码，并可选自动提交。**建议仅在明确登录路径下注入**，且密码/账号应通过部署参数注入，不要在 manifest 中写死。

其他内置脚本见 `builtin://hello`（调试打印）。

### `builtin://simple-inject-password` 参数

> ⚠️ 下表来自 lzcinit 内置脚本实现，官方文档未逐项列出。如与实现不符，**以实际行为为准**。

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `user` | `string` | 账号值，默认空 |
| `password` | `string` | 密码值，默认空 |
| `autoSubmit` | `bool` | 是否自动提交，默认 `true` |
| `submitMode` | `string` | `auto`/`requestSubmit`/`click`/`enter`，默认 `auto` |
| `submitDelayMs` | `int` | 自动提交前延迟（毫秒），默认 `50` |
| `retryCount` | `int` | 自动提交重试次数，默认 `10` |
| `retryIntervalMs` | `int` | 重试间隔（毫秒），默认 `300` |
| `observerTimeoutMs` | `int` | DOM 观察超时（毫秒），默认 `8000` |
| `debug` | `bool` | 开启调试日志，默认 `false` |
| `userSelector` | `string` | 显式指定账号输入框选择器 |
| `passwordSelector` | `string` | 显式指定密码输入框选择器 |
| `formSelector` | `string` | 限定在指定容器内搜索输入框 |
| `submitSelector` | `string` | 显式指定提交按钮选择器 |
| `allowHidden` | `bool` | 允许填充不可见输入框，默认 `false` |
| `allowReadOnly` | `bool` | 允许填充只读输入框，默认 `false` |
| `onlyFillEmpty` | `bool` | 仅当输入框为空时才填充，默认 `false` |
| `includeShadowDom` | `bool` | 是否搜索开放的 Shadow DOM，默认 `false` |
| `shadowDomMaxDepth` | `int` | Shadow DOM 最大递归深度，默认 `2` |
| `preferSameForm` | `bool` | 优先选择与密码框同一表单内的账号框，默认 `true` |
| `eventSequence` | `string \| []string` | 触发事件序列，默认 `input,change,keydown,keyup,blur` |

## 实践建议

- 需要多个页面时，优先增加多条 `when`，而不是放宽规则。
- 登录跳转场景可用 query 条件约束，例如 `"/?version=1.2&channel=stable"`。
- hash 路由场景建议在脚本中结合 `ctx.runtime.executedBefore` 控制是否重跑。
- **强烈建议将用户名、密码改为部署参数注入**，避免在代码或 manifest 中写死弱密码。
- 非 HTML 响应天然不会被注入；`unless` 主要用于进一步限制 HTML 页面范围（例如 `/admin/debug`）。
- 远程脚本仅建议调试使用，正式发布建议改为 `builtin://` 或 `file://`。

## 常见错误（排错）

| 现象 | 原因 |
| --- | --- |
| inject 完全不生效 | `when` 写了 `#hash` 但 `on=request/response`（hash 仅 browser 支持） |
| 登录后仍被跳过 | 无 `SAFE_UID` 且 `auth_required=true`（默认） |
| 通配没匹配上根路径 | `"/api/*"` **不**匹配 `"/api"`；需额外声明精确规则 `"/api"` |
| `ctx.body.getJSON()` 抛错 | 请求体并非合法 JSON，需先判断或捕获异常 |
| 用了 `include`/`scripts`/`mode` 但无效 | 这些字段不存在，应使用 `when`/`do`/`*` 后缀通配 |
