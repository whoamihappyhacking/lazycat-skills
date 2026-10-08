# package.yml：LPK V2 元数据与权限

本文件是常用项摘要，写配置前先执行 `references/spec-sync.md`。完整依据：[官方 package 规范](https://developer.lazycat.cloud/spec/package.html)。LPK V2 要求 **lzcos >=1.5.0、lzc-cli >=2.0.0**。

## 1. 文件边界

`package`、`version`、`name`、`description`、`author`、`license`、`homepage`、`admin_only`、`hidden_from_launcher`、`min_os_version`、`unsupported_platforms`、`locales`、`permissions`、`import_resources` 写入 **package.yml**，不要写到 V2 manifest 顶层。

- `package`、`version` 是最小必填字段；包 ID 和 `application.subdomain` 不是一回事。
- `version` 用字符串；建议语义化版本。`unsupported_platforms` 的取值依据目标平台规范，不凭示例猜测。
- `hidden_from_launcher`（>=1.5.3）只隐藏启动器入口，不改变地址、权限或部署行为。
- `min_os_version` 应不低于实际使用能力的最低版本。
- `locales` 的语言标签建议 BCP 47，如 `zh-CN`、`en-US`；未命中时回退顶层值。使用须知及入口标题的本地化见[manifest 本地化](https://developer.lazycat.cloud/spec/manifest.html#i18n)。

## 2. 最小权限

`permissions` 是**开发者声明**，不是最终授权结果。官方 schema 中可省略，但技能生成配置时必须审计所有功能所需权限：未声明权限不能使用，未知 ID 非法，同一 ID 不得同时在 required/optional 中出现。无权限需求时可以显式声明空列表，不能为了“保险”把全部权限设为 required。

| 类别 | 常用合法 ID |
| --- | --- |
| 网络 | `net.internet`、`net.lan`、`net.host`、`net.admin` |
| 文稿/媒体 | `document.private`、`document.read`、`document.write`、`media.read`、`media.write` |
| 设备 | `device.dri.render`、`device.dri.master`、`device.usb`、`device.kvm`、`device.block`、`vt.display` |
| 挂载 | `fuse.mount`（>=1.6.1） |
| 跨应用数据 | `appvar.other.read`、`appvar.other.write` |
| 高危运行时覆盖 | `compose.override` |
| 电源 | `power.shutdown.inhibit` |
| LightOS | `lightos.use`、`lightos.manage` |
| 通知 | `user.notify`（>=1.6.0） |

- `document.private`：`/lzcapp/documents/$uid`，按用户隔离，卸载默认不删除；只放用户可理解、可管理的文件。数据库、索引、内部配置放 `/lzcapp/var`，不滥用文稿权限。
- `fuse.mount`：系统注入 `/lzcinit/fusermount3` 并把 `/lzcinit` 加入 PATH；优先于直接 privileged。
- `vt.display`：还需 `application.vt: true`，且所有 service 不得使用 sysbox-runc。
- `user.notify`：容器内注入 `/lzcinit/notify-send`；不是客户端权限或配额声明。
- HTTP 代表用户访问自身/其他应用的 `lzcapp.self_delegate` / `lzcapp.user_delegate`，定义在[应用间访问专题](https://developer.lazycat.cloud/advanced-app-interconnect.html)。通用权限表与专题存在覆盖范围差异：按目标系统实际支持核实，不把跨应用数据文件权限当成 HTTP 委托权限。

## 3. 静态站元数据例子

```yaml
# package.yml
package: cloud.lazycat.app.demo
version: "1.0.0"
name: 示例静态站
min_os_version: "1.5.0"
locales:
  zh-CN:
    name: 示例静态站
    description: 由 LPK 内容提供的静态页面
  en-US:
    name: Demo Static Site
    description: A static page served from LPK content
permissions:
  required: []
  optional: []
```

这里没有申请互联网或文稿权限，因为示例只托管包内内容。移植实际应用时按功能补充权限，不机械照抄空列表。

## 4. 导入资源（>=1.5.2）

```yaml
# package.yml 的可选片段
import_resources:
  - kind: skills
  - kind: mcp-providers
```

每个 kind 只能出现一次，系统只投影已声明类型：

- payload：`/lzcapp/run/resources/<kind>/<package-id>/<resource-id>/...`
- 汇总摘要：`/lzcapp/run/resources/.digest/<kind>/summary`
- 单资源摘要：`/lzcapp/run/resources/.digest/<kind>/<package-id>/<resource-id>/digest`

投影只读；不能假定存在额外 catalog。声明资源导入不等于获取其他应用的 HTTP/业务权限。导出与校验细节请读取 `references/resource-export.md`。
