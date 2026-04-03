# lzc-manifest.yml 规范文档 (LPK V2)

## 一、 概述
`lzc-manifest.yml` 用于定义应用运行结构与部署相关配置。

**重要说明**：自 LPK V2 起，静态元数据（如 `package`, `version`, `name`, `locales`, `permissions` 等）必须放入 `package.yml` 中。`lzc-manifest.yml` 仅保留运行时相关的配置。

## 二、 顶层数据结构 `ManifestConfig`

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `usage` | `string` | 应用使用须知，用户首次访问时自动渲染。 |
| `application` | `ApplicationConfig` | 应用核心服务配置。 |
| `services` | `map` | 其他容器服务配置。 |
| `ext_config` | `ExtConfig` | 实验性/高级扩展属性。 |

## 三、 `ApplicationConfig` 配置

### 3.1 基础配置
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `image` | `string` | 应用镜像，留空默认使用 alpine3.21。支持 `embed:<alias>`。 |
| `subdomain` | `string` | 入站子域名。 |
| `multi_instance` | `bool` | 是否支持多实例部署。 |
| `depends_on` | `[]string` | 依赖的应用内其他服务。 |
| `oidc_redirect_path` | `string` | OIDC 回调路径。 |

### 3.2 路由与注入 (核心)
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `routes` | `[]string` | 简化版 HTTP 路由。转发时**默认去掉路径前缀**。 |
| `upstreams` | `[]UpstreamConfig` | 高级 HTTP 路由，支持 `disable_trim_location` 和 `domain_prefix`。 |
| `injects` | `[]InjectConfig` | 脚本注入配置，支持 `browser`/`request`/`response` 阶段。 |
| `public_path` | `[]string` | 独立鉴权的路径列表。 |

### 3.3 脚本注入 (Injects)
`injects` 允许在不修改源码的情况下注入逻辑。

- **阶段 (`on`)**: `browser` (默认), `request` (转发前), `response` (响应后)。
- **匹配**: `when` (命中条件), `unless` (排除条件), `prefix_domain` (域名前缀)。
- **执行环境**: `request/response` 在 lzcinit 沙盒中执行，支持 `ctx.headers`, `ctx.body`, `ctx.proxy` 等。

示例：
```yaml
injects:
  - id: dev-proxy
    on: request
    when: ["/*"]
    do:
      - src: |
          ctx.proxy.to("http://127.0.0.1:3000", { use_target_host: true });
```

## 四、 `UpstreamConfig` 配置 (高级路由)

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `location` | `string` | 匹配路径。 |
| `backend` | `string` | 上游地址 (`http://`, `file://`, `exec://`)。 |
| `disable_trim_location` | `bool` | **新特性**：为 true 时，转发到后端保留路径前缀。 |
| `domain_prefix` | `string` | **新特性**：基于域名前缀的分流。 |
| `use_backend_host` | `bool` | 是否使用 backend 里的 host 作为请求头。 |

## 五、 `ExtConfig` 扩展配置

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `enable_document_access` | `bool` | 启用**旧版**兼容路径 `/lzcapp/run/mnt/home` (需管理员授权)。 |
| `enable_media_access` | `bool` | 挂载媒体目录到 `/lzcapp/media`。 |

**注意**：LPK V2 推荐使用 `permissions` 声明 `document.private` 权限，此时私有路径为 `/lzcapp/documents/$uid`。

## 六、 示例

```yaml
# package.yml 负责元数据
# lzc-manifest.yml 负责运行时
application:
  subdomain: myapp
  routes:
    - /=file:///lzcapp/pkg/content/dist
  upstreams:
    - location: /api
      backend: http://server:8080
      disable_trim_location: true
```
