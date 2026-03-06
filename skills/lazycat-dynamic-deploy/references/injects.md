脚本注入（injects）
==================

概述
====

`injects` 用于在指定 URL 命中的 HTML 页面中注入脚本，适合第三方应用最小侵入适配。此功能需要 lzcos 1.5.0+。
字段定义请先看 [manifest.md#injects](./spec/manifest.md#injects)；本文聚焦行为细节和实践建议。

快速示例
========

```yml
application:
  injects:
    - id: login-autofill
      include:
        - "/"
        - "/?version=1.2&channel=stable"
        - "/#login"
      scripts:
        - src: builtin://simple-inject-password
          params:
            user: "admin"
            password: "admin123"
```

规则模型
========

- `include`：白名单规则，任一命中即进入候选
- `exclude`：黑名单规则，任一命中即排除
- `mode`：`exact` 或 `prefix`，默认 `exact`，作用于 `path/hash`
- `prefix_domain`：非空时，仅匹配域名前缀为 `<prefix>-` 的请求
- `injects` 条目按声明顺序注入；每个条目内 `scripts` 也按顺序注入

规则语法
========

单条规则格式：

`<path>[?<query>][#<hash>]`

示例：

- `"/"`
- `"/?version=1.2"`
- `"/#login"`
- `"/app?version=1.2&channel=stable#signin"`

解析说明：

- `path` 必填，且必须以 `/` 开头
- `query` token 支持两种形式：
  - `key`：要求 key 存在
  - `key=value`：要求 key 至少有一个 value 等于该值
- 单条规则内 query token 为 AND（全部满足）
- query 为 contains 语义：请求允许包含额外参数

匹配语义
========

整体逻辑：

- `include` 是 OR：任意一条命中即可进入候选
- `exclude` 是 OR：任意一条命中即拒绝
- 最终结果：`matched = includeMatched && !excludeMatched`

单条规则逻辑（AND）：

- `path` 命中
- 且 `query` 命中（若声明）
- 且 `hash` 命中（若声明）

`mode` 语义（作用于 `path/hash`）：

- `exact`：完全匹配
- `prefix`：前缀匹配

Hash 行为（hard/soft）
======================

- `path/query` 是服务端可见条件，属于 hard 匹配
- `hash` 是服务端不可见条件，自动降级为客户端 soft 匹配

这意味着：

- 服务端先根据 `path/query` 判断是否注入 wrapper
- wrapper 在浏览器端再按完整规则（含 `hash`）决定是否执行脚本
- 可能出现“注入了 wrapper 但因 hash 不匹配未执行脚本”，这是预期行为

执行时机与运行时参数
====================

wrapper 的触发时机：

1. 页面加载后执行一次评估（`trigger=load`）
2. 监听 `hashchange`，每次 hash 变化后再次评估（`trigger=hashchange`）
3. 只要命中规则就执行脚本，不做内置去重

脚本可读取以下对象：

- `__LZC_INJECT_PARAMS__`：来自 `scripts[].params`
- `__LZC_INJECT_RUNTIME__`：
  - `executedBefore`：当前页面生命周期内，该脚本此前是否执行过
  - `executionCount`：当前是第几次执行（从 `1` 开始）
  - `trigger`：`load` 或 `hashchange`

示例（脚本侧）：

```js
(() => {
  const runtime = __LZC_INJECT_RUNTIME__ || {};
  if (runtime.executedBefore) {
    return;
  }
  const params = __LZC_INJECT_PARAMS__ || {};
  console.log("inject params:", params);
})();
```

脚本来源
========

`scripts[].src` 支持：

- `builtin://name`：使用 lzcinit 内置脚本
- `file:///path`：读取应用文件系统内脚本（常见路径 `/lzcapp/pkg/content/`）
- `http(s)://...`：远程脚本（建议仅调试使用）

远程脚本加载会使用条件请求缓存（`ETag`/`Last-Modified`）。

内置脚本
========

`builtin://hello`
-----------------

打印调试信息。

参数：

- `message`：输出内容，默认 `hello world`

`builtin://simple-inject-password`
----------------------------------

自动填充账号/密码，并可选自动提交。建议仅在明确登录路径下注入。

参数说明（`params`）：

| 参数 | 类型 | 说明 |
| ---- | ---- | ---- |
| `user` | `string` | 账号值，默认空 |
| `password` | `string` | 密码值，默认空 |
| `requireUser` | `bool` | 是否必须找到账号输入框；默认逻辑：若 `allowPasswordOnly=true` 则 `false`，否则当 `user` 非空时为 `true` |
| `allowPasswordOnly` | `bool` | 允许仅填充密码，默认 `false` |
| `autoSubmit` | `bool` | 是否自动提交，默认 `true` |
| `submitMode` | `string` | 提交模式：`auto`/`requestSubmit`/`click`/`enter`，默认 `auto` |
| `submitDelayMs` | `int` | 自动提交前延迟（毫秒），默认 `50`，最小 `0` |
| `retryCount` | `int` | 自动提交重试次数，默认 `10` |
| `retryIntervalMs` | `int` | 自动提交重试间隔（毫秒），默认 `300` |
| `observerTimeoutMs` | `int` | DOM/状态观察超时（毫秒），默认 `8000` |
| `debug` | `bool` | 开启调试日志，默认 `false` |
| `userSelector` | `string` | 显式指定账号输入框选择器 |
| `passwordSelector` | `string` | 显式指定密码输入框选择器 |
| `formSelector` | `string` | 限定在指定容器内搜索输入框 |
| `submitSelector` | `string` | 显式指定提交按钮选择器 |
| `allowHidden` | `bool` | 允许填充不可见输入框，默认 `false` |
| `allowReadOnly` | `bool` | 允许填充只读输入框，默认 `false` |
| `onlyFillEmpty` | `bool` | 仅当输入框为空时才填充，默认 `false` |
| `allowNewPassword` | `bool` | 允许填充 `autocomplete=new-password` 的密码框，默认 `false` |
| `includeShadowDom` | `bool` | 是否搜索开放的 Shadow DOM，默认 `false` |
| `shadowDomMaxDepth` | `int` | Shadow DOM 最大递归深度，默认 `2` |
| `preferSameForm` | `bool` | 优先选择与密码框同一表单内的账号框，默认 `true` |
| `eventSequence` | `string` 或 `[]string` | 触发事件序列，默认 `input,change,keydown,keyup,blur` |
| `keyValue` | `string` | 触发键盘事件时的按键值，默认 `a` |
| `userKeywords` | `string` 或 `[]string` | 追加账号字段关键词（逗号分隔或数组） |
| `userExcludeKeywords` | `string` 或 `[]string` | 追加账号字段排除关键词 |
| `passwordKeywords` | `string` 或 `[]string` | 追加密码字段关键词 |
| `passwordExcludeKeywords` | `string` 或 `[]string` | 追加密码字段排除关键词 |
| `submitKeywords` | `string` 或 `[]string` | 追加提交按钮关键词 |

实践建议
========

- 需要多个页面时，优先增加多条 `include`，而不是放宽规则
- 登录跳转场景可直接用 query 条件约束，例如 `"/?version=1.2&channel=stable"`
- hash 路由场景建议在脚本中结合 `__LZC_INJECT_RUNTIME__.executedBefore` 控制是否重跑
- 强烈建议将用户名、密码改为部署参数注入，避免在代码或 manifest 中写死弱密码
- 非 HTML 响应天然不会被注入；`exclude` 主要用于进一步限制 HTML 页面范围（例如 `/admin/debug` 这类页面路径）
- 远程脚本仅建议调试使用，正式发布建议改为 `builtin://` 或 `file://`
