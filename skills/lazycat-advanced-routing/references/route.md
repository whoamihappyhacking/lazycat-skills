路由规则
=========

`application.routes`字段为 `[]Rule`类型

Rule按照`URL_PATH=UPSTREAM`的形式声明, 其中`URL_PATH`为浏览器访问时的实际URL路径(不含hostname部分),
`UPSTREAM`为具体的上游服务, 目前支持以下3种协议

- `file:///$dir_path`
- `exec://$port,$exec_file_path`
- `http(s)://$hostname/$path`

注意：`application.routes` 在转发时默认会去掉 `URL_PATH` 前缀。例如下面规则，
当浏览器请求 `/api/v1` 时，后端实际收到的是 `/v1`。
```
routes:
  - /api/=http://backend:80
```
如果需要保留前缀，请改用 `application.upstreams` 并设置 `disable_trim_location: true`（lzcos v1.3.9+）。

http上游
=======

`http/https`支持内网或外网服务. 比如内置的应用商店这个lzcapp只有一行代码.

```
routes:
    - /=https://appstore.lazycat.cloud
```
当访问`https://appstore.$微服名称.heiyu.space`时会将所有请求都直接转发到上游的`https://appstore.lazycat.cloud`, 这种
情况下页面内的js代码依旧可以使用`lzc-sdk/js`的功能, 应用商店的安装\打开逻辑是在微服中运行的,但代码是部署在公有云上,方便统一维护.

绝大部分情况下,lzcapp的http路由是转发到应用内某个service的http端口上, 比如`bitwarden`这个密码管理lzcapp, 就是将整个lzcapp的
http服务转发到bitwarden这个service的80端口上.

```
package: cloud.lazycat.app.bitwarden
description: 一款自由且开源的密码管理服务
name: Bitwarden

application:
  routes:
  - /=http://bitwarden.cloud.lazycat.app.bitwarden.lazcapp:80
  - /or_use_this_short_domain=http://bitwarden:80
  subdomain: bitwarden
services:
  bitwarden:
    image: bitwarden/nginx:1.44.1

```

1. `http://bitwarden:80`中的bitwarden是services中的service名称,这个名称在运行时会自动解析为service实际的ip.
2. `http://bitwarden.cloud.lazycat.app.bitwarden.lzcapp:80`的写法为`$service_name.$appid.lzcapp`

注意
1. lzcos-1.3.x之后会引入应用隔离,应用之间禁止相互访问,因此如果没有特殊原因直接使用`service_name`的形式作为域名更简便，也方便修改appid。(`xxx.lzcapp`本身不会被废弃，任意应用都能解析到正确IP，但隔离后无法访问到目标IP)
2. 但以下特殊情况依旧需要使用`xxx.lzcapp`域名形式
   1. 在lzcos-1.3.x之前因为没有进行应用隔离，所有应用看到的`service_name`都是互通的。当不同应用有相同service_name时，可能被错误解析到其他容器IP。
      因此`service_name`是`app`、`db`这类大概率会冲突的情况下在应用网络隔离前依旧需要使用`xxx.lzcapp`形式。
   2. 如果上游服务会检测`http request host`之类的，则需要使用`xxx.lzcapp`形式，否则上游服务解析http request时，
      `http header host`会是`service_name`而非`aaaa.xxx.heiyu.space`。
      此限制是因为上游服务也可能是一个公网服务，此时host必须原封不动传递给上游否则大概率会出现跨域之类的问题。
      如果有相关需求，建议使用`upstreams.[].use_backend_host=true`明确指定此行为。

file上游
=========

file路由用来加载静态html文件, 比如pptist这个lzcapp是一个纯前端应用,因此仅使用了一条静态file路由规则,没有运行任何其他service

```
package: cloud.lazycat.app.pptist
name: PPTist
description: 一个基于 Vue3.x + TypeScript 的在线演示文稿（幻灯片）应用
application:
  subdomain: pptist
  routes:
    - /=file:///lzcapp/pkg/content/
  file_handler:
    mime:
      - x-lzc-extension/pptist         # app支持.pptist
    actions:  # 打开对应文件的url路径,由文件管理器等app调用
      open: /?file=%u   # %u是某个webdav上的具体文件路径，一定存在文件名后缀

```

一般静态资源是通过lpk文件打包时引入的,lpk对应的contentdir内容最终会在运行时原封不动的以readonly的形式存放在`/lzcapp/pkg/content/`目录


exec上游
=========

`exec://$port,$exec_file_path`路由稍微特殊一点,由两部分组成

1. 最终提供服务的端口号$port,这里强制隐含了host为127.0.0.1
2. 具体的可执行文件路径. 可以为任意路径下的脚本或elf文件.

lzcapp启动时,系统会执行exec路由中的`$exec_file_path`文件,并假设此文件提供的服务运行在`http://127.0.0.1:$port`上.
系统本身不会检测此服务是否真的由`$exec_file_path`启动. (因此也能基于这个特性做一些初始化相关的操作)

一个lzcapp可以创建任意条不同类型的路由规则. 比如官方的懒猫网盘lzcapp的路由规则为

```
application:
  image: registry.lazycat.cloud/lzc/lzc-files:v0.1.47
  subdomain: file
  routes:
    - /api/=exec://3001,/lzcapp/pkg/content/backend
    - /files/=http://127.0.0.1:3001/files/
    - /=file:///lzcapp/pkg/content/dist
```

其中前端页面由静态文件`/lzcapp/pkg/content/dist`提供,
所有以`/api/`开头的路径由可执行文件`/lzcapp/pkg/content/backend`启动后在`http://127.0.0.1:3001`上提供服务,
并且所有以`/files/`开头的路径也转发到`http://127.0.0.1:3001/files`上.



UpstreamConfig
===============
除此外还(v1.3.8+)可以使用[applications.upstreams](./spec/manifest.md)字段配置更细致的路由规则，

比如,
```
subdomain: debug

routes: #简单版本的routes也是可以一起工作的
  - /=http://app1.org.snyh.debug.whoami.lzcapp:80

upstreams:
  # 明确指定一些细微行为
  - location: /search
    backend: https://baidu.com/
    use_backend_host: true  #如果不设置则一般外网服务器会因为host字段不对拒绝服务
    disable_auto_health_checking: true #不要针对这条路由做健康检测
    remove_this_request_headers: #删除origin,referer等header避免跨域之类的问题
      - origin
      - Referer
    disable_url_raw_path: true # 将原始url也进行规范化的转化

  # 跳过后端自签SSL证书问题
  - location: /other
    backend: https://app2.snyh.debug.lzcapp:4443 #正常情况下这个域名是不会有合法正式的
    disable_backend_ssl_verify: true #因此需要在这里配置跳过SSL验证

  # 使用domain_prefix做基于域名前缀的分流
  - location: /
    domain_prefix: config  #当访问https://config-debug.xx.heiyu.space/时走这里的规则
    backend: http://config.snyh.debug.lzcapp:80

  # 使用backend_launch_command替代exec路由规则，语义更明确
  - location: /api
    backend: http://127.0.0.1:3001/
    backend_launch_command: /lzcapp/pkg/content/my-super-backend -listen :3001

```
