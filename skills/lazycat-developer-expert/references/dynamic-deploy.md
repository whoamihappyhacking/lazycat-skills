# 部署参数与清单渲染 (Dynamic Deploy)

`lzc-deploy-params.yml` 用于定义用户安装应用时需要填写的参数。

## 一、 部署参数 (`lzc-deploy-params.yml`)

### 核心字段
| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `id` | `string` | 参数 ID，在 `lzc-manifest.yml` 中通过 `.U.<id>` 引用。 |
| `type` | `string` | 类型：`bool`, `string`, `secret`, `lzc_uid`。 |
| `default_value` | `string` | 默认值。支持 **`$random(len=5)`** 生成随机串。 |
| `optional` | `bool` | 是否可选。 |

### 示例
```yaml
params:
  - id: admin_password
    type: secret
    name: 管理员密码
    default_value: "$random(len=8)"
```

## 二、 清单渲染 (Manifest Render)

在 `lzc-manifest.yml` 中使用 Go 模板语法引用变量：

- **`.U.<id>`**: 引用用户定义的部署参数。
- **`.S.<id>`**: 引用系统预设变量。

示例：
```yaml
services:
  app:
    environment:
      - ADMIN_PWD={{.U.admin_password}}
      - BOX_DOMAIN={{.S.BOX_DOMAIN}}
```

## 三、 脚本注入 (Injects) 增强

LPK V2 支持更丰富的脚本注入阶段：

- **`on: browser`**: 浏览器侧注入 (默认)。
- **`on: request`**: 请求转发到后端前拦截，可修改请求头、Body 或重定向。
- **`on: response`**: 后端响应返回浏览器前拦截，可修改响应头、Body。

### 常用 Context (`ctx`) 能力
- `ctx.headers`: 读写 HTTP 头。
- `ctx.body`: 读写 Body (支持 `getJSON`, `setJSON`)。
- `ctx.proxy`: 动态改变反代目标。
- `ctx.persist`: 跨请求持久化用户数据。

示例 (CORS 适配):
```yaml
application:
  injects:
    - id: cors-fix
      on: response
      when: ["/api/*"]
      do: |
        ctx.headers.set("Access-Control-Allow-Origin", "*");
```
