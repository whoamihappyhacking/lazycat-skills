# 域名前缀与多域名分流

> 校准基线：懒猫官方开发者文档仓库 `780d7206ce2298ee0a225e0221a993c4723d8e07`。生成配置前仍须先执行 `spec-sync.md`，以当前官方原文为准。

官方来源：

- <https://developer.lazycat.cloud/advanced-secondary-domains.html>
- <https://developer.lazycat.cloud/advanced-route.html#upstreamconfig>
- <https://developer.lazycat.cloud/spec/manifest.html#entries>

## 1. 当前机制：自动前缀域名

`application.subdomain` 只是期望的默认子域名。系统可能因名称冲突或多实例部署为实际域名添加后缀；最终值从运行时环境变量 `LAZYCAT_APP_DOMAIN` 获取，不要永久保存，也不要假定它永远等于 manifest 中的值。

应用自动拥有任意前缀域名：

```text
<实际子域名>.<微服根域>
<prefix>-<实际子域名>.<微服根域>
```

例如实际子域名为 `demo` 时，`admin-demo.<微服根域>` 和 `api-demo.<微服根域>` 都会进入同一应用。

**不存在需要枚举附加域名的 `application.secondary_domains` 字段。** 遇到旧配置时删除该字段，改用下述前缀匹配能力。

## 2. 用 `upstreams[].domain_prefix` 分流

### `package.yml`

```yml
package: cloud.lazycat.app.prefix-routing-demo
version: 0.0.1
name: Prefix Routing Demo
description: 域名前缀分流示例
```

### `lzc-manifest.yml`

```yml
application:
  subdomain: prefix-routing-demo
  upstreams:
    - location: /
      domain_prefix: admin
      backend: http://admin:80

    - location: /
      backend: http://main:80

services:
  main:
    image: registry.lazycat.cloud/traefik/whoami
  admin:
    image: registry.lazycat.cloud/traefik/whoami
```

效果：

- 默认域名进入 `main`。
- `admin-<实际子域名>.<微服根域>` 进入 `admin`。
- 不需要预先声明 `admin` 为第二域名。

镜像引用来自当前官方 HTTP 路由教程；实际使用前仍须核验 registry 可用性。

## 3. 启动器入口也可指定前缀

`application.entries[].prefix_domain` 用于让某个启动器入口直接打开前缀域名：

```yml
application:
  subdomain: prefix-routing-demo
  entries:
    - id: main
      title: 主界面
      path: /
    - id: admin
      title: 管理界面
      path: /
      prefix_domain: admin
  upstreams:
    - location: /
      domain_prefix: admin
      backend: http://admin:80
    - location: /
      backend: http://main:80
```

`prefix_domain` 的最终形式为 `<prefix>-<实际子域名>.<微服根域>`。它负责选择入口域名；真正的后端分流仍由 `upstreams[].domain_prefix` 或应用内代理完成。

官方 manifest 还记录了 `ext_config.default_prefix_domain`，用于调整点击应用默认打开的域名前缀。`ext_config` 属实验性区域，只有当前官方规范和目标系统明确支持时才使用，不要为了普通多入口场景优先依赖它。

## 4. 何时使用应用内代理

`application.routes` 不能按域名前缀选择不同 backend。若不使用 `upstreams.domain_prefix`，可把所有 HTTP 请求转给同一 Nginx/OpenResty service，再由 `server_name` 判断 Host。

这类 route 应按官方方案使用完整 service DNS：

```yml
application:
  routes:
    - /=http://edge.cloud.lazycat.app.prefix-routing-demo.lzcapp:80
```

使用短名 `http://edge:80` 时，代理可能看不到用于域名分流的完整入口 Host。代理镜像与配置示例见 `advanced-routes.md`；不要恢复过时且未经当前官方确认的 `app-proxy` 固定标签。

## 5. 与 L4、service DNS、跨应用访问的边界

1. **前缀域名流量会忽略 TCP/UDP Ingress。** `admin-...` 等前缀不能用来为不同 L4 服务分流；L4 使用应用默认域名对应的入口。
2. `domain_prefix` 是当前应用 HTTP 入口规则，不是创建新应用，也不改变 service DNS。
3. `<service>.<package-id>.lzcapp` 用于应用内 service 定位及特定 Host 保留场景，不应当成跨应用 HTTP API。
4. 代表用户访问另一个应用，应使用 `app.<target-package-id>.lzcx` 并遵循官方委托访问权限与票据规则。

## 6. 验证清单

- 从 `LAZYCAT_APP_DOMAIN` 确认实际默认域名，而不是只看 manifest 请求值。
- 分别访问默认域名和每个 `<prefix>-...` 域名，检查命中的 backend。
- 如用代理分流，让代理记录实际 Host；不要硬编码完整设备域名。
- 不要用前缀域名测试 L4 ingress；该流量按官方定义会忽略 ingress。
