# Docker 移植：权限、持久化与启动排障

先按 `references/spec-sync.md` 核验目标版本。依据：[manifest](https://developer.lazycat.cloud/spec/manifest.html)、[setup_script](https://developer.lazycat.cloud/advanced-setupscript.html)、[Compose override](https://developer.lazycat.cloud/advanced-compose-override.html)、[权限](https://developer.lazycat.cloud/spec/package.html)。

## 1. 不用 root 掩盖权限问题

1. 先读镜像的入口、初始化与 UID/GID 要求，再检查实际目录 owner 和挂载是否只读。
2. lzcos >=1.6.0 且镜像支持数字非 root 用户时，优先 run_as：映射 `/lzcapp` 持久目录 owner，配置见 `references/manifest-spec.md`。
3. user 只调整进程用户，**不等于**开启持久目录 owner 映射。不要在宿主机盲目 chown 大目录或假定宿主 UID 必须等于容器 UID。
4. 镜像必须 root 初始化再内部降权时，尊重入口契约；仅在确实需要时用幂等 setup_script，不与同 service 的 run_as/entrypoint/command 混用。
5. 老系统不支持 run_as 时，明确兼容方案、授权与安全代价，不能默认推荐全服务 root。

## 2. 正确的数据位置

| 数据 | 路径/注意 |
| --- | --- |
| 包内模板、静态内容 | `/lzcapp/pkg/content`；只读 |
| 数据库、配置、内部索引 | `/lzcapp/var/<服务>`；应用内部数据 |
| 可重建缓存 | `/lzcapp/cache/<服务>`；不要把唯一用户数据当缓存 |
| 用户文件 | `/lzcapp/documents/$uid`；document.private，按用户隔离 |
| 临时运行状态 | `/lzcapp/run`；不当持久化目录 |

不要把旧 `/lzcapp/run/mnt/home` 当默认推荐路径。使用兼容挂载时核实系统版本与授权（v1.7.0 起管理员明确授权）。改变多实例配置、包 ID 或数据位置前，先备份并设计迁移。

初始化可写配置时，挂载**目录**而非不存在的单文件，首次复制，后续不覆盖用户修改。例如：

```yaml
# lzc-manifest.yml 片段；项目 content/default-config.yml 必须真实存在
services:
  worker:
    image: alpine:3.21
    binds:
      - /lzcapp/var/worker:/data
    setup_script: |
      set -eu
      if [ ! -e /data/config.yml ]; then
        cp /lzcapp/pkg/content/default-config.yml /data/config.yml
      fi
```

这是初始化模式示例，不是完整服务；实际应用应使用有合适原始入口的镜像，系统会在脚本后恢复它的入口。setup_script 每次容器启动都会运行；不能在里面递归调用打包或重复创建账号。

## 3. 健康检查与依赖

- services.<name>.healthcheck 是容器探针；application.health_check 是 app 扩展检查，两者不能混淆。
- 用实际就绪条件（HTTP 健康端点、数据库 select 1），先确认镜像有探针依赖，不能无条件写 curl。
- start_period 为首启初始化留合理空间，结合 timeout、interval、retries；不要以无限 sleep 或禁用探针掩盖启动失败。
- depends_on 是同应用服务健康依赖，不是跨应用依赖；service 不能依赖特殊 app 名称。
- 查日志时使用 `lzc-cli docker` 前缀，定位具体容器再查；不无界扫描微服文件系统。

## 4. 内核能力与高权限

- 网络访问、设备、FUSE 等先申请精确权限。FUSE 优先 fuse.mount（>=1.6.1），网络管理用 net.admin，宿主网络用 net.host；不要直接用 privileged 代替所有能力。
- LPK 无法表达而确有必要的需求，才使用 lzc-build.yml.compose_override，并在 package.yml 声明 compose.override；先向用户说明高风险并取得授权。
- override 属过渡机制，兼容性不受保证。需与官方沟通后提交审核；功能合理不意味着必然通过。
- Compose override 的挂载字段是 volumes，不是 manifest.binds；不要默认挂载宿主系统内部路径。
- 检查最终 compose.override.yml 与实际合并结果，验证权限边界未被意外放大。

## 5. Host、CORS 与业务鉴权

- 先检查完整请求 Host、上游监听、可信代理与应用 URL 配置，不宣称平台会自动解决所有跨域。
- use_backend_host 会改变上游 Host，只在上游需要时开启；优先规范服务 DNS。
- CORS 修改需限定允许来源/方法/凭据，不用 `*` 配合 credentials=true。
- public_path 只是免平台登录，不自动提供业务权限检查；webhook/公共 API 必须自行验签、鉴权或限流。
- 业务后端只有在请求确实经过可信平台入口时，才信任平台注入的身份 Header；不能直接暴露可伪造 Header 的后端端口。
