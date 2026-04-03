# 高级路由与 Upstreams (Advanced Routing)

在 `lzc-manifest.yml` 中，`application.routes` 提供简单路由，而 `application.upstreams` 提供了更细粒度的控制。

## 一、 UpstreamConfig 核心特性

| 字段名 | 类型 | 描述 |
| ---- | ---- | ---- |
| `location` | `string` | 入口路径。 |
| `backend` | `string` | 后端服务 (如 `http://app:8080`)。 |
| `disable_trim_location` | `bool` | **新特性**：为 true 时，转发到后端保留匹配的前缀路径。 |
| `domain_prefix` | `string` | **新特性**：根据域名前缀分流。 |
| `use_backend_host` | `bool` | 是否在访问后端时，将 Host 头改为 backend 的主机名。 |
| `remove_this_request_headers` | `[]string` | 转发前移除的 HTTP 头。 |

## 二、 场景示例

### 1. 保留路径前缀
```yaml
upstreams:
  - location: /api
    backend: http://server:3000
    disable_trim_location: true # 转发到后端仍包含 /api
```

### 2. 基于域名前缀的分流
当访问 `admin-myapp.boxdomain.com` 时：
```yaml
upstreams:
  - location: /
    domain_prefix: admin
    backend: http://admin-server:8080
```

### 3. 多协议支持
- `http(s)://`
- `file:///lzcapp/...` (静态资源)
- `exec://$port,$file` (动态启动并转发)

## 三、 四层转发 (Ingress)
对于非 HTTP 流量 (TCP/UDP)：
```yaml
application:
  ingress:
    - protocol: tcp
      port: 22
      service: ssh-server
```
