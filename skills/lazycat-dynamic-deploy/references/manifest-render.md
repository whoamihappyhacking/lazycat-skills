# `lzc-manifest.yml` 动态渲染

动态渲染始于 `lzcos 1.3.8+`。以下按 LPK V2 编写，因此构建还要求 `lzcos >= 1.5.0`、`lzc-cli >= 2.0.0`。

官方原文：

- <https://developer.lazycat.cloud/advanced-manifest-render.html>
- <https://developer.lazycat.cloud/spec/deploy-params.html>
- <https://developer.lazycat.cloud/spec/package.html>
- <https://developer.lazycat.cloud/spec/manifest.html>

## 渲染流程

1. 项目根目录的 `lzc-deploy-params.yml` 随 LPK 打包。
2. 安装或重新配置实例时，系统收集部署参数。
3. 系统以 Go `text/template` 渲染 `/lzcapp/pkg/manifest.yml`。
4. 结果写入 `/lzcapp/run/manifest.yml`，再作为最终运行配置。

多实例应用的部署参数按用户独立。即使没有部署参数文件，manifest 仍会经过 render 流程。

## 模板源不是最终 YAML

包含 `{{ ... }}`、`{{ if }}` 等 Go action 的源文件，**不能直接按最终 YAML 用普通 YAML 解析器解析或校验**。正确顺序是先完成模板渲染，再解析/校验渲染结果。排错时查看 `/lzcapp/run/manifest.yml`，不要因模板源的 YAML parser 报错就删除合法模板结构。

同时必须保证每一种条件分支渲染后都是合法 YAML；动态字符串放在 YAML 值中时优先加引号并测试特殊字符。

## 可用上下文

- `.UserParams` / `.U`：来自 `lzc-deploy-params.yml`。
- `.SysParams` / `.S`：系统参数。
  - `.BoxName`
  - `.BoxDomain`
  - `.OSVersion`
  - `.AppDomain`
  - `.IsMultiInstance`
  - `.DeployUID`（单实例下无实际意义）
  - `.DeployID`

部署 render 不再提供 `.E` / `.PkgEnvs`。dev/release 结构差异应在 build 阶段用 `lzc-build.yml`、`lzc-build.dev.yml` 与 `#@build` 处理。

参数 ID 含 `.` 时使用：

```gotemplate
{{ index .U "listen.port" }}
```

## 模板函数

- [Sprig](https://masterminds.github.io/sprig/)（不含 `env`/`expandenv`）。
- `stable_secret "seed"`：为同一应用、同一微服稳定生成秘密；不同应用或微服结果不同。

不要把稳定秘密截成 6～8 位弱口令。除非上游有明确长度上限，否则保留完整输出；若必须截断，先按其密码策略评估足够熵并记录原因。

## LPK V2 示例

静态元数据必须与运行配置分离：

```yaml
# package.yml
package: org.snyh.netmap
version: 0.1.0
name: netmap
min_os_version: 1.5.0
```

```yaml
# lzc-deploy-params.yml
params:
  - id: target
    type: string
    name: 目标地址
    description: 要转发到的目标 IP 或主机名
  - id: listen.port
    type: string
    name: 监听端口
    description: 不能使用 80 或 81
    default_value: "33"
    optional: true
```

```yaml
# lzc-manifest.yml 运行配置片段（与真实 web service 配置合并）
application:
  subdomain: netmap
  routes:
    - /=http://web:8080
services:
  web:
    environment:
      TARGET: {{ .U.target | quote }}
      LISTEN_PORT: {{ index .U "listen.port" | quote }}
```

`package`、`version`、`name` 不再写入 `lzc-manifest.yml`。用户输入先作为环境变量传入，并由应用按目标格式校验；不要把未验证的 `.U` 值直接拼进 `command`、`entrypoint` 或 `backend_launch_command`，否则会形成参数/命令注入风险。

## 持久存储与秘密

应用内部持久状态放在 `/lzcapp/var`，再 bind 到服务需要的目录：

```yaml
services:
  database:
    binds:
      - /lzcapp/var/database:/var/lib/database
    environment:
      DB_PASSWORD: {{ stable_secret "database_password" | quote }}
```

不要把应用内部状态写到旧的 `/lzcapp/run/mnt/home` 文稿兼容路径。用户可直接理解和管理的文稿应按最新 package 权限与 manifest 规范单独设计，不能借动态模板绕过授权。

## `routes` 与调试安全

字段是复数 `application.routes`；不要写旧的/错误的 `application.route`。但**不要**为了调试增加 HTTP route 暴露 `/lzcapp/run/manifest.yml`：渲染结果可能包含密码和内部地址。

只在受控 devshell 中查看，并避免把输出复制到日志或工单：

```bash
cat /lzcapp/run/manifest.yml
```

如临时加入 `xx-debug: {{ . }}` 检查上下文，完成后必须删除；其中可能含部署参数。

## 边界原则

1. build 阶段决定包里有什么。
2. deploy render 决定目标设备上的部署值。
3. request inject 决定当前请求如何处理。

模板只使用完成部署所需的最少参数；密码参数使用 `secret`，内部秘密优先 `stable_secret`，不写死默认弱密码。