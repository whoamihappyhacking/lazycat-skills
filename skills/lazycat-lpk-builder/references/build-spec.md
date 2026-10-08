# lzc-build.yml：LPK V2 构建与开发态

先执行 `references/spec-sync.md`，依据[官方 build 规范](https://developer.lazycat.cloud/spec/build.html)核对目标系统和 CLI。V2 至少 lzcos 1.5.0 + lzc-cli 2.0.0。

## 1. 文件与命令选择

- lzc-build.yml：默认/release 配置。
- lzc-build.dev.yml：只放开发态差异，不能复制整份正式配置。
- project deploy、info/start/exec/cp/log/sync：优先 dev，不存在时默认配置。
- project build：默认正式配置，可用 `-f` 指定；project release：正式配置。
- 检查命令输出的 Build config，别误把正式实例当成 dev。

## 2. 常用字段

| 字段 | 语义 |
| --- | --- |
| `buildscript` | shell 命令或脚本路径；**不得调用 project build 自己** |
| `manifest` | lzc-manifest.yml 路径 |
| `contentdir` | 内容目录；省略或显式空值，不产生 content.tar* |
| `pkgout` | LPK 输出路径 |
| `icon` | PNG 文件路径；未指定有警告，尺寸/大小按当前商店要求核实 |
| `package_override` | 覆盖最终 package.yml 的顶层字段，不递归 merge，空值清空 |
| `envs` | 构建期 KEY=VALUE 字符串数组，不进入部署环境 |
| `images` | alias → ImageBuildConfig，供 manifest 使用 embed:alias |
| `compose_override` | 高危兼容方案，需 compose.override 权限及明确授权 |
| `resource_exports` | kind/source 列表，资源导出 >=1.5.2 |

dev 若定义 package_override，会**整体替换**正式文件中的 package_override。覆盖 package 字段参与最终包名/文件名校验。权限列表等顶层对象同样整体替换，不能假定只修改其中一个叶子。

envs 的 KEY 须为合法环境变量名称，禁止重复；变量注入 buildscript 和 manifest build 预处理，部署 render 仍只负责 .U/.S 等参数。

```yaml
# lzc-build.yml：静态站，无构建脚本时直接打包已有 content
manifest: ./lzc-manifest.yml
contentdir: ./content
pkgout: ./
```

```yaml
# lzc-build.dev.yml
package_override:
  package: cloud.lazycat.app.demo.dev
contentdir:
envs:
  - DEV_MODE=1
```

## 3. #@build 与开发机代理

指令必须在 YAML 注释中：if profile=dev/release、if env.KEY=VALUE、else、end、include ./relative.yml。include 相对主 manifest，只插入纯文本，片段不能再含 #@build 指令。先构建预处理，再部署 Go template render；二者不是同一个阶段。

下面示例代理到**开发机**的 3000 端口，而不是容器 localhost：

```yaml
# lzc-manifest.yml；两分支分别解析，不得作为重复 application 键的完整 YAML 直接加载
#@build if env.DEV_MODE=1
application:
  subdomain: demo
  injects:
    - id: frontend-dev-proxy
      on: request
      when: ["/*"]
      do:
        - src: |
            if (!ctx.dev.id) {
              ctx.response.send(503, "Developer device is not configured");
              return;
            }
            ctx.proxy.to("http://127.0.0.1:3000", {
              via: ctx.net.via.client(ctx.dev.id),
              use_target_host: true,
              on_fail: "error",
            });
#@build else
application:
  subdomain: demo
  routes:
    - /=file:///lzcapp/pkg/content
#@build end
```

`ctx.dev.id` 由项目开发工作流配置；缺开发机标识或开发机未在线时，应给明确错误/诊断，不能宣称代理已工作。省略 via 的 localhost 指**当前容器网络**，仅服务确实在那里运行时才正确。网络权限及设备上下文也需核验。连通性探测/回退模板见[官方开发态 Cookbook](https://developer.lazycat.cloud/advanced-inject-request-dev-cookbook.html)。

## 4. 内嵌镜像

```yaml
# lzc-build.yml 片段；假定项目根有 Dockerfile
images:
  web:
    dockerfile: ./Dockerfile
    context: ./
    upstream-match: registry.lazycat.cloud
```

```yaml
# lzc-manifest.yml 片段
services:
  web:
    image: embed:web
```

- dockerfile 与 dockerfile-content 必须二选一；不可同时定义。
- context 默认值随两种模式不同；需明确项目文件组织。
- 构建器沿父镜像链匹配 upstream-match，有上游可混合分发，否则全量内嵌。
- 最终 images/ 是 OCI layout，images.lock 记录 alias/digest/upstream；manifest 中最终 embed digest 应与 lock 对齐。
- 不把镜像内嵌等同商店自动审核通过；上架前按最新平台镜像政策核验。

## 5. 导出资源与 override

resource_exports 示例与 payload 校验请读取 `references/resource-export.md`。高权限迁移请读取 `references/troubleshooting.md`；不要默认 privileged 或挂载系统内部目录。Compose override 兼容性不受保证，上架需与官方沟通，不作一定可上架的承诺。
