# TCP/UDP 4层转发 {#tcp-udp-ingress}

::: warning 正常http流量，请使用`application.routes`功能

ingress的TCP/UDP转发能是为了提供给微服客户端之外使用，比如命令行或第三方应用。
如果只是为了转发容器的某个http端口，请使用lzcapp的[http路由功能](./advanced-route.md)。

:::


如果您想提供一些 TCP/UDP 服务，可以在 `lzc-manifest.yml` 文件中的 `application` 字段下加一个 `ingress` 子字段

```yml
application:
  ingress:
    - protocol: tcp
      port: 8080
    - protocol: tcp
      description: 数据库服务
      port: 3306
      service: mysql
    - protocol: tcp
      description: 2W-3W端口来源转发到对应端口
      service: app
      publish_port: 20000-30000
    - protocol: tcp
      description: 1.6W-1.8W端口来源都转发到6666端口
      service: app
      port: 6666
      publish_port: 16000-18000
```

- `protocol`: 对外服务的协议， 有 `tcp` 和 `udp` 两种选择
- `description`: 对此服务的描述，便于管理员了解基本情况
- `port`: 目标服务的端口号，若不写则为实际入站端口号。（v1.3.8之前的版本不支持`port`为80或443）
- `service`: 服务名称，用来定位具体的`service container`。默认值为`app`
- `publish_port`: 入站端口号，默认值为`port`对应的端口号。支持`3306`以及`1000-50000`两种写法。

设置好以后， 就可以通过浏览器来进行访问啦, 比如您的应用域名为 `app-subdomain` (lzc-manifest.yml 文件的 subdomain 字段)， 设备名为 `devicename`, 您就可以通过访问 `app-subdomain.devicename.heiyu.space:3306` 来访问对外提供的 TCP 服务啦。

::: warning 安全提示
当您使用TCP/UDP功能时，微服系统仅能提供底层虚拟网络的保护，从原理上无法提供鉴权流程。
微服客户端上的其他进程可以不受限制的访问对应TCP/UDP端口。
若用户使用端口转发工具进行转发则会进一步降低安全性，因此开发者在提供TCP/UDP功能时一定要妥善处理鉴权逻辑。
:::

::: warning 80/443

当您的应用直接接管443时(v1.3.8+支持)，流量是直接到达您容器内，因此系统无法做一些预处理，包括但不限于

- 账户鉴权
- 自动唤醒应用
- HTTPS证书配置
- application.routes,application.upstreams等配置

几乎所有情况下您都不应该去使用443端口配置。

目前设想唯一合理的场景是：使用微服分配的EIP，全流量转发到另外一台主机/NAS上，并配置一个非微服域名。

如果您真的确定要自行处理80/443流量则需要在对应ingress条目里明确声明`yes_i_want_80_443:true`

:::
