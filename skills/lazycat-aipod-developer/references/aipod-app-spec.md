# AI 应用：resource、型号 compose 与 startup gate

核对日期：2026-10-08。当前依据：[AI Pod 应用专题](https://developer.lazycat.cloud/aipod/package/spec.html)；通用依据：[LPK V2 package](https://developer.lazycat.cloud/spec/package.html)、[资源导出规范](https://developer.lazycat.cloud/spec/resource-export.html)。写配置前执行 `references/spec-sync.md` 并单独读取 AI Pod 专页。

## 1. 不再把 legacy 包布局当新规范

AI 应用现在以微服应用加 **AIApp resource** 为核心：服务随设备型号部署，插件自动加载，快捷方式与依赖由资源 config/aipod.yml 描述。

专题推荐的资源 payload：

```text
aipod/
├── package.yml
├── lzc-manifest.yml
├── icon.png
├── config/
│   └── aipod.yml
├── agxorin/
│   └── docker-compose.yml
├── thor/
│   └── docker-compose.yml
└── extensions/
    ├── desktop.zip
    └── android.crx
```

注意：这是 AIApp resource 的**内容布局**，不是自动等同通用 LPK 顶层或任意 resource-id 的完整打包声明。

### 专题与通用 V2 的未统一边界（必须说明）

- 当前 AI Pod 专题把 import_resources 示例放在 lzc-manifest.yml，而通用 V2 PackageConfig 明确该字段在 package.yml。
- 专题给出的运行路径是 `/lzcapp/run/resources/aipod/<package-id>/`；通用资源规范则是 `/lzcapp/run/resources/<kind>/<package-id>/<resource-id>/...`。
- 因此不能照抄专题就把 import_resources 加到 V2 manifest，也不能杜撰“default 资源 ID 会自动扁平化”的规则。
- **必须先核实目标版本、官方支持的 AIApp 分发/导入工具和实际消费端目录。** 通用构建部分遵循 V2 schema；专用导入映射未确认时，交付时明确未验证，不能保证一个猜出的完整包可被消费。

旧 ai-pod-service、browser-extension 构建字段不因本页出现新版资源布局就自动断言 CLI 全部不支持；它们不作为新项目默认入口，兼容迁移需按目标工具链核验。

## 2. 型号目录与镜像

1. Thor 优先 thor/docker-compose.yml。
2. 其他默认 Jetson/AGX Orin 设备用 agxorin/docker-compose.yml。
3. 型号目录缺失时才 fallback 到 legacy ai-pod-service/docker-compose.yml。
4. 多个目录或 legacy 同时存在时，对外 AI host **必须一致**。

不同硬件的 CPU 架构、JetPack/CUDA、驱动和镜像兼容性必须分别核实；不能把 AGX Orin 镜像直接宣称兼容 Thor。平台 Docker 默认 NVIDIA runtime，通常不需显式 gpus 配置；有特殊 runtime 需求时先核实，而非无条件禁止所有自定义配置。

### 最小 Traefik 服务示例

下列是官方已有 whoami 演示服务，仅说明路由结构，不宣称它是模型服务或已覆盖所有型号：

```yaml
# agxorin/docker-compose.yml；对应 thor 文件也需保持相同 whoami-ai host
services:
  whoami:
    image: registry.lazycat.cloud/traefik/whoami:ab541801c8cc
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.${LZC_SERVICE_ID}-whoami.rule=Host(`whoami-ai`)"
networks:
  default:
    external: true
    name: traefik-shared-network
```

- 可解析的 Host(...) label 和 `-ai` 后缀是平台识别条件。
- 服务必须加入 traefik-shared-network。
- 长初始化模型服务**必须**有真实 healthcheck；探针要检查 ready，而非只检查进程存在，且所用 curl/wget/解释器必须在镜像中。
- AI host 一致不代表各设备实现、内存占用或模型结果一致，须真机验证。

## 3. 数据、缓存与标识

| 环境变量 | 作用 |
| --- | --- |
| `LZC_AGENT_DATA_DIR` | `/ssd/lzc-ai-agent/data/<service_id>`，用户/服务持久化数据 |
| `LZC_AGENT_CACHE_DIR` | `/ssd/lzc-ai-agent/cache/<service_id>`，可重建缓存 |
| `LZC_SERVICE_ID` | appId 去掉点后的服务标识，用于 Traefik 名称 |

Compose volumes 使用环境变量，而不是写死真实设备路径；例如 `${LZC_AGENT_DATA_DIR}/data:/data`。不要因资源布局迁移改变实例/目录而丢旧模型或用户数据，先备份并设计迁移。

## 4. config/aipod.yml

配置文件**不带外层 aipod:**：

```yaml
# config/aipod.yml
shortcut:
  disable: false
  title: Whoami
  url: /_lzc/aipod_backend/startup/gate/cloud.lazycat.aipod.whoami?redirect=https%3A%2F%2Fwhoami-ai
locales:
  en:
    shortcut:
      title: Whoami
depends_on_hosts:
  - whoami-ai
```

- shortcut.disable 默认为 false；还可定义 title/url/favicon。
- depends_on_hosts 是本应用自己的 AI host；depends_on_others 是依赖的其他 AI host，不能与 Compose depends_on 混用。
- storage_alias 声明服务存储别名，需按实际模型/数据布局配置，不凭别名获得任意宿主目录访问。
- metadata 缺失时按资源内 package.yml → lzc-manifest.yml → icon.png 兜底；AI 浏览器展示以 resource 配置为准。

## 5. 插件与启动入口

- 浏览器插件放 extensions/，支持 zip/crx，可多个；适配 PC/Android 需分别验证权限、宿主能力和打包格式。
- legacy browser-extensions/extension.zip 只在缺新版插件时 fallback。
- 不再默认每个应用内置 caddy-aipod 做启动判断，优先平台 gate：
  `/_lzc/aipod_backend/startup/gate/:appid?redirect=<URL编码目标>`。
- appid 填真实应用包 ID，redirect URL 编码；ready/loading/失败提示复用平台与容器 healthcheck，gate 不代替业务鉴权。
- 静态前端拦截模板见官方专题：保留深链接和 query，排除 API/资源/icon/平台内部路径，避免重定向循环。不要机械复制专题中的 public_path 放开所有业务 API；只在确有独立鉴权且授权时开放。
- ready cookie 是平台启动流程提示，不是可以信任的业务授权凭据。

## 6. 交付与兼容验收

1. 确认资源打包/导入映射及消费端支持，不以通用资源静态发现代替 AIApp 业务消费验证。
2. 构建后的 V2 包必须有 package.yml，manifest 不混旧静态元数据；在副本中检查归档与配置。
3. 各目标型号真机安装/启动，验证 host、healthcheck、gate、插件和模型能力。
4. 验证重启/升级/资源重载时数据与依赖不丢失；旧包兼容路径需要专门测试。
5. 发布遵循当前[商店八项审核](https://developer.lazycat.cloud/store-submission-guide.html)；不得声称特殊 AI 包一定通过审核。

多算力舱访问格式仅使用占位符：`f-{算力舱序列号}-{服务名}-ai.{微服名}.heiyu.space`。需要实际微服名时执行 lzc-cli box default，不在技能中保存真实设备信息。
