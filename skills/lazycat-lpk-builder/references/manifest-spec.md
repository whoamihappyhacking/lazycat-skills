# lzc-manifest.yml 规范文档

## 一、 概述
`lzc-manifest.yml` 是用于定义应用部署相关配置的文件。 本文档将详细描述其结构和各字段的含义。

## 二、 顶层数据结构 `ManifestConfig`

### 2.1 基本信息 {#basic-config}

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `package` | `string` | 应用的唯一 id， 需保持全球唯一， 建议以个人域名开头 |
| `version` | `string` | 应用的版本号，X、Y 和 Z 为非负的整數，X 是主版本号、Y 是次版本号、而 Z 为修订号，格式：`X.Y.Z`，[阅读详细规范](https://semver.org/)|
| `name` | `string` | 应用名称 |
| `description` | `string` | 应用描述 |
| `usage` | `string` | 应用的使用须知， 如果不为空， 则微服内每个用户第一次访问本应用时会自动渲染 |
| `license` | `string` | 应用的 License 说明 |
| `homepage` | `string` | 应用的主页 |
| `author` | `string` | 作者名称， 若通过商店渠道则商店账号优先级更高 |
| `min_os_version` | `string` | 本应用要求的最低系统版本， 若不满足则应用安装时会失败， 且应用商店会拒绝安装此应用 |

### 2.2 其他配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `ext_config` | `ExtConfig` | 实验性属性， 暂不对外公开 |
| `unsupported_platforms` | `[]string` | 应用不支持的平台， 有效字段为: "ios", "android", "windows", "macos", "linux", "tvos" |
| `application` | `ApplicationConfig` | lzcapp 核心服务配置 |
| `services` | `map[string]ServiceConfig` | 传统 docker container 相关服务配置 |
| `locales` | `map[string]I10nConfigItem` | 应用本地化配置（可选配置项），**需要更新 lzc-os 版本 >= v1.3.0** |


## 三、 `IngressConfig` 配置
### 3.1 网络配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `protocol` | `string` | 协议类型， 支持 `tcp` 或 `udp` |
| `port` | `int` | 目标端口号， 若为空， 则使用实际入站的端口 |
| `service` | `string` | 服务容器的名称， 若为空， 则为 `app` 这个特殊 service |
| `description` | `string` | 服务描述， 以便系统组件渲染应用服务给管理员查阅 |
| `publish_port` | `string` | 允许的入站端口号， 可以为具体的端口号或 `1000~50000` 这种端口范围 |
| `send_port_info` | `bool` | 以 little ending 发送 uint16 类型的实际入站端口给目标端口后再进行数据转发 |
| `yes_i_want_80_443`| `bool` | 为true则允许将80,443流量转发到应用，此时流量完全绕过系统，因此鉴权、唤醒等都不会生效|


## 四、 `ApplicationConfig` 配置
### 4.1 基础配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `image` | `string` | 应用镜像， 若无特殊要求， 请留空使用系统默认镜像(alpine3.21) |
| `background_task` | `bool` | 若为 `true` 则会自动启动并且不会被自动休眠， 默认为 `true` |
| `subdomain` | `string` | 本应用的入站子域名，应用打开默认使用此子域名 |
| `multi_instance` | `bool` | 是否以多实例形式部署 |
| `usb_accel` | `bool` | 挂载相关设备到所有服务容器内的 `/dev/bus/usb` |
| `gpu_accel` | `bool` | 挂载相关设备到所有服务容器内的 `/dev/dri` |
| `kvm_accel` | `bool` | 挂载相关设备到所有服务容器内的 `/dev/kvm` 和 `/dev/vhost-net` |
| `depends_on` | `[]string` | 依赖的其他容器服务， 仅支持本应用内的其他服务， 且强制检测类型为 `healthly`， 可选 |

### 4.2 功能配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `file_handler` | `FileHandlerConfig` | 声明本应用支持的扩展名， 以便其他应用在打开特定文件时可以调用本应用 |
| `entries` | `[]EntryConfig` | 应用入口声明，用于配置多个入口的名称和地址信息，详见 4.3 |
| `routes` | `[]string` | 简化版 http 相关路由规则 |
| `upstreams` | `[]UpstreamConfig` | 高级版本 http 相关路由规则，与routes共存 |
| `public_path` | `[]string` | 独立鉴权的 http 路径列表 |
| `injects` | `[]InjectConfig` | 脚本注入配置，用于在指定路径注入脚本（lzcinit） |
| `workdir` | `string` | `app` 容器启动时的工作目录 |
| `ingress` | `[]IngressConfig` | TCP/UDP 服务相关 |
| `environment` | `map[string]string \| []string` | `app` 容器的环境变量，支持 map 或 list 形式 |
| `health_check` | `AppHealthCheckExt` | `app` 容器的健康检测， 仅建议在开发调试阶段设置 `disable` 字段， 不建议进行替换， 否则系统默认注入的自动依赖检测逻辑会丢失 |
| `oidc_redirect_path` | `string` | 合法的 OIDC redirect path，完整域名会自动根据 subdomain 进行拼接 |

提示：`routes` 在转发时默认会去掉路径前缀。如需保留前缀，请使用 `upstreams` 并设置 `disable_trim_location: true`（lzcos v1.3.9+）。

### 4.3 多入口配置 {#entries}

`entries` 用于声明多个入口，系统可在启动器里展示多个入口。

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `id` | `string` | 入口的唯一 ID |
| `title` | `string` | 入口标题 |
| `path` | `string` | 入口路径，通常以 `/` 开头。支持传递query参数 |
| `prefix_domain` | `string` | 入口域名前缀，最终域名表现为 `<prefix>-<subdomain>.<rootdomain>` |

入口标题支持通过 `locales` 配置 `entries.<entry_id>.title` 进行多语言本地化。

### 4.4 脚本注入配置 {#injects}

`injects` 用于在特定路径对 HTML 页面注入脚本，适合对第三方应用做最小侵入的适配逻辑。

注入匹配规则：
- 使用 `include` 白名单与 `exclude` 黑名单
- `include` 必填，任意一条命中即可进入候选
- `exclude` 可选，任意一条命中即排除
- 最终结果：`matched = includeMatched && !excludeMatched`
- `prefix_domain` 不为空时，仅匹配域名前缀为 `<prefix>-` 的请求
- `mode` 支持 `exact`/`prefix`，默认 `exact`，作用于 `path/hash`
- 仅 HTML 响应会执行注入，非 HTML 响应不会注入脚本

`injects` 支持多个条目，按声明顺序注入。每个条目内的 `scripts` 也按顺序注入。

#### InjectConfig
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `id` | `string` | 注入配置的唯一 ID |
| `prefix_domain` | `string` | 入口域名前缀（可选），仅对指定前缀域名生效 |
| `mode` | `string` | 匹配模式，`exact` 或 `prefix`，默认 `exact` |
| `include` | `[]string` | 注入白名单规则，至少一条 |
| `exclude` | `[]string` | 注入黑名单规则，可选 |
| `scripts` | `[]InjectScriptConfig` | 脚本列表 |

#### InjectScriptConfig
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `src` | `string` | 脚本来源，支持 `builtin://name`、`file:///lzcapp/...`、`http(s)://...` |
| `params` | `map[string]any` | 传递给脚本的参数 |

规则语法：

`include/exclude` 单条规则格式为：`<path>[?<query>][#<hash>]`

语义说明：

- `path` 必填，`query/hash` 可选
- `query` token 支持 `key` 或 `key=value`
- 单条规则内 query token 为 AND（全部满足）
- query 匹配为 contains 语义（允许额外 query 参数）
- `hash` 属于客户端软匹配条件；服务端仅按 `path/query` 决定是否注入 wrapper

示例：
```yml
application:
  injects:
    - id: login-autofill
      mode: exact
      include:
        - /login
        - /signin?channel=stable
        - /#login
      exclude:
        - /api
        - /#debug
      scripts:
        - src: builtin://hello
          params:
            message: "hello world"
        - src: file:///lzcapp/pkg/content/custom_inject.js
          params:
            usernameField: "#user"
            passwordField: "#pass"
        - src: https://dev.example.com/inject.js
          params:
            mode: "debug"
```

提示：`params` 会通过闭包参数注入脚本，脚本内可直接使用 `__LZC_INJECT_PARAMS__` 读取，避免多脚本全局变量冲突。

更多说明（运行时行为、hashchange、内置脚本参数、实践建议）见：[脚本注入（injects）](../advanced-injects.md)。

## 五、 `HealthCheckConfig` 配置
### 5.1 AppHealthCheckExt
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `test_url` | `string` | 仅 application 字段下生效。 扩展的检测方式， 直接提供一个 http url 不依赖容器内部有 curl/wget 之类的命令行 |
| `disable` | `bool` | 禁用本容器的健康检测 |
| `start_period` | `string` | 启动等待阶段时间， 超出此时间范围后若还未进入 `healthly` 状态则会变为 `unhealthy` |
| `timeout` | `string` | 单次检测耗时超过`timeout`则认为检测失败 |


### 5.2 HealthCheckConfig

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `test` | `[]string` | 在对应容器内执行什么命令进行检测， 如：`["CMD", "curl", "-f", "http://localhost"]`
| `timeout` | `string` | 单次检测耗时超过`timeout`则认为本次检测失败 |
| `interval` | `string` | 每次检测间隔时间 |
| `retries` | `int` | 连续多少次检测失败后让整个容器进入unhealthy状态。默认值1 |
| `start_period` | `string` | 启动等待阶段时间， 超出此时间范围后若还未进入 `healthly` 状态则会变为 `unhealthy` |
| `start_interval` | `string` | 在start_period时间内，每隔多久执行一次检测 |
| `disable` | `bool` | 禁用本容器的健康检测 |


## 六、 `ExtConfig` 配置 {#ext_config}

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `enable_document_access` | `bool` | 如果为true则将document目录挂载到/lzcapp/document |
| `enable_media_access` | `bool` | 如果为true则将media目录挂载到/lzcapp/media |
| `enable_clientfs_access` | `bool` | 如果为true则将clientfs目录挂载到/lzcapp/clientfs |
| `disable_grpc_web_on_root` | `bool` | 如果为true则不再劫持应用的grpc-web流量。需要配合新版本lzc-sdk以便系统本身的grpc-web流量可以正常转发|
| `default_prefix_domain` | string | 会调整启动器中点击应用后打开的[最终域名](../advanced-secondary-domains)，可以写任何不含`.`的字符串 |
| `enable_bind_mime_globs` | `bool` | 如果为true则绑定系统的 mime globs 到容器内的 `/usr/share/mime/globs2` |



## 七、 `ServiceConfig` 配置

### 7.1 容器配置 {#container-config}

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `image` | `string` | 对应容器的 docker 镜像 |
| `environment` | `map[string]string \| []string` | 对应容器的环境变量，支持 map 或 list 形式 |
| `entrypoint` | `*string` | 对应容器的 entrypoint， 可选 |
| `command` | `*string` | 对应容器的 command， 可选 |
| `tmpfs` | `[]string` | 挂载 tmpfs volume， 可选 |
| `depends_on` | `[]string` | 依赖的其他容器服务(app这个名字除外)， 仅支持本应用内的其他服务， 且强制检测类型为 `healthly` 可选 |
| `healthcheck` | `*HealthCheckConfig` | 容器的健康检测策略, 老版本`health_check`已被废弃 |
| `user` | `*string` | 容器运行的 UID 或 username， 可选 |
| `cpu_shares` | `int64` | CPU 份额 |
| `cpus` | `float32` | CPU 核心数 |
| `mem_limit`| `string\|int` | 容器的内存上限 |
| `shm_size`| `string\|int` | /dev/shm/大小 |
| `network_mode` | `string` | 网络模式， 目前只支持`host`或留空。 若为 `host` 则会容器的网络为宿主网络空间。 此模式下应用进行网络监听时务必注意鉴权， 非必要不要监听 `0.0.0.0` |
| `netadmin` | `bool` | 若为 `true`， 则容器具备 `NET_ADMIN` 权限， 可以操作网络相关系统调用， 如无必要请不要使用。 若使用此功能， 请务必小心不要扰乱 iptables 相关规则 |
|`setup_script` | `*string` | 配置脚本， 脚本内容会以 root 权限执行后， 再按照 OCI 的规范执行原始的 entrypoint 内容。 本字段和 entrypoint,command 字段冲突， 无法同时设置， 可选 |
| `binds` | `[]string` | lzcapp 容器的 rootfs 重启后会丢失， 仅 `/lzcapp/var`, `/lzcapp/cache` 路径下的数据会永久保留。 因此其他需要保留的目录需要 bind 到这两个目录之下。 此列表仅支持 `/lzcapp` 开头的路径 |
| `runtime` | `string` | 	指定OCI runtime。支持`runc`和`sysbox-runc`。sysbox-runc隔离程度更高，能跑完整的dockerd,systemd等。但不支持network_mode=host之类namespace共享相关的功能更|


## 八、`FileHandlerConfig` 配置
### 8.1 文件处理配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `mime` | `[]string` | 支持的 MIME 类型列表 |
| `actions` | `map[string]string` | 动作映射 |

## 九、`HandlersConfig` 配置

### 9.1 处理程序配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `acl_handler` | `string` | ACL 处理程序 |
| `error_page_templates` | `map[string]string` | 错误页面模板， 可选 |


## 十、`UpstreamConfig` 配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `location` | `string` | 入口匹配的路径 |
| `disable_trim_location` | `bool` | 转发到`backend`时，不要自动去掉`location`前缀 (lzcos v1.3.9+)|
| `domain_prefix` | `string` | 入口匹配的域名前缀 |
| `backend` | `string` | 上游的地址，需要是一个合法的url，支持http,https,file三个协议 |
| `use_backend_host` | `bool` | 如果为true,则访问上游时http host header使用backend中的host，而非浏览器请求时的host |
| `backend_launch_command` | `string` | 自动启动此字段里的程序 |
| `trim_url_suffix` | `string` | 自动删除请求后端时url可能携带的指定字符 |
| `disable_backend_ssl_verify` | `bool` | 请求backend时不进行ssl安全验证 |
| `disable_auto_health_checking` | `bool` | 禁止系统自动针对此条目生成的健康检测 |
| `disable_url_raw_path` | `bool` | 如果为true则删除http header中的raw url |
| `remove_this_request_headers` | `[]string` | 删除这个列表内的http request header， 比如"Origin"、"Referer" |
| `fix_websocket_header` | `bool` | 自动将Sec-Websocket-xxx替换为Sec-WebSocket-xxx |
| `dump_http_headers_when_5xx` | `bool` | 如果http上游出现5xx, 则dump请求 |
| `dump_http_headers_when_paths` | `[]string` | 如果与到此路径下的http, 则dump请求 |



## 十一、本地化 `I10nConfigItem` 应用配置 {#i18n}

配置 `locales` 使应用支持多语言，支持设置的 language key 规范可参考 [BCP 47 标准](https://en.wikipedia.org/wiki/IETF_language_tag)

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `name` | `string` | 应用名称本地化字段 |
| `description` | `string` | 应用描述本地化字段 |
| `usage` | `string` | 应用的使用须知本地化字段 |
| `entries.<entry_id>.title` | `string` | 入口标题本地化字段，`entry_id` 需与 `application.entries` 中的 `id` 一致 |

说明：入口标题可通过 `locales` 配置 `entries.<entry_id>.title` 进行多语言本地化。

::: details 配置示例
```yml
lzc-sdk-version: 0.1
package: cloud.lazycat.app.netatalk
version: 0.0.1
name: Apple 时间机器备份
description: Netatalk 服务可用于 Apple 时间机器备份
author: Netatalk
locales:
  zh:
    name: "Apple 时间机器备份"
    description: "Netatalk 服务可用于 Apple 时间机器备份"
  zh_CN:
    name: "Apple 时间机器备份"
    description: "Netatalk 服务可用于 Apple 时间机器备份"
  en:
    name: "Time Machine Server"
    description: "Netatalk service can be used for Apple Time Machine backup"
  ja:
    name: "タイムマシンサーバー"
    description: "Netatalk サービスは Apple Time Machine のバックアップに使用できます"
application:
  subdomain: netatalk3
```
:::
