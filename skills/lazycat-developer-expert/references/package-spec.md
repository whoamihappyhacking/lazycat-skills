# package.yml 规范 (LPK V2)

`package.yml` 用于定义 LPK 的静态包元数据，以及开发者声明的权限需求范围。自 LPK v2 起，静态元数据从 `lzc-manifest.yml` 移入此文件。

## 一、 核心字段

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `package` | `string` | **必填**；应用唯一包 ID (如 `cloud.lazycat.app.demo`) |
| `version` | `string` | **必填**；应用版本 (语义化版本) |
| `name` | `string` | 应用显示名称 |
| `description` | `string` | 应用描述 |
| `author` | `string` | 作者或维护者 |
| `license` | `string` | 许可证 (如 `MIT`) |
| `homepage` | `string` | 主页或反馈地址 |
| `admin_only` | `bool` | 是否仅管理员可见 |
| `min_os_version` | `string` | 要求的最低系统版本 |
| `unsupported_platforms` | `[]string` | 不支持的平台列表 (如 `linux/386`) |
| `locales` | `map` | 多语言元数据 (支持 `name`, `description`) |
| `permissions` | `object` | **权限声明** (包含 `required` 和 `optional`) |

## 二、 权限声明 (Permissions)

必须在 `package.yml` 中显式声明应用所需的权限。

```yaml
permissions:
  required:
    - net.internet      # 访问互联网
    - document.private  # 使用私有文稿目录 /lzcapp/documents/$uid
  optional:
    - device.dri.render # 访问 GPU
    - net.lan           # 访问局域网
```

### 常用权限 ID

- **网络**: `net.internet`, `net.lan`, `net.host`, `net.admin`
- **存储**: 
  - `document.private`: 私有文稿目录 (推荐使用 `/lzcapp/documents`)
  - `document.read` / `document.write`: 用户公共文稿目录访问
  - `media.read` / `media.write`: 系统媒体目录访问
- **设备**: `device.dri.render` (GPU), `device.usb`, `device.kvm`, `device.block`
- **系统**: `compose.override` (高危运行时覆盖), `power.shutdown.inhibit` (阻止关机)
- **LightOS**: `lightos.use`, `lightos.manage`

## 三、 多语言 (Locales)

```yaml
locales:
  zh-CN:
    name: 示例应用
    description: 这是一个示例
  en-US:
    name: Demo App
    description: This is a demo
```

## 四、 最小示例

```yaml
package: cloud.lazycat.app.demo
version: 1.0.0
name: Demo App
permissions:
  required:
    - net.internet
    - document.private
```
