# lzc-build.yml 规范 (LPK V2)

`lzc-build.yml` 定义了应用打包为 LPK 的过程。自 LPK V2 起，支持 `lzc-build.dev.yml` 进行开发态覆盖。

## 一、 构建配置文件

1. **`lzc-build.yml`**: 默认构建配置，即 Release 配置。
2. **`lzc-build.dev.yml`**: 开发态覆盖配置，只定义差异项。

`lzc-cli project deploy` 优先读取 `.dev.yml`。`lzc-cli project release` 仅读取 `.yml`。

## 二、 核心字段

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `buildscript` | `string` | 构建脚本路径或 shell 命令。 |
| `manifest` | `string` | `lzc-manifest.yml` 路径。 |
| `contentdir` | `string` | 静态内容目录 (挂载至 `/lzcapp/pkg/content`)。 |
| `pkgout` | `string` | LPK 输出目录。 |
| `icon` | `string` | 图标路径 (PNG, 1:1, <200KB)。 |
| `pkg_id` | `string` | (可选) 构建阶段覆盖 `package.yml.package`。 |
| `envs` | `[]string` | 构建期变量 (`KEY=VALUE`)，用于 `#@build` 宏。 |
| `images` | `map` | 容器镜像构建配置 (`embed:<alias>`)。 |

## 三、 manifest build 预处理 (#@build)

在 `lzc-manifest.yml` 中支持条件编译指令（需写在 YAML 注释中）：

- `#@build if profile=dev` / `profile=release`
- `#@build if env.KEY=VALUE`
- `#@build else`
- `#@build end`
- `#@build include ./path.yml`

示例：
```yaml
#@build if env.DEV_MODE=1
application:
  injects:
    - id: dev-proxy
      on: request
      do: "ctx.proxy.to('http://127.0.0.1:3000')"
#@build else
application:
  routes: ["/=file:///lzcapp/pkg/content/dist"]
#@build end
```

## 四、 开发态覆盖示例 (`lzc-build.dev.yml`)

```yaml
pkg_id: cloud.lazycat.app.demo.dev
contentdir:   # 显式覆盖为空，不打包 content
envs:
  - DEV_MODE=1
```
