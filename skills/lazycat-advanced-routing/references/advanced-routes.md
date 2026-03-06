# 高级路由

## 简介
官方维护了一个APP Proxy镜像，方便开发者实现复杂的路由功能，以及查看对应的请求日志。
APP Proxy本质是一个基于Openresty的镜像，镜像地址：`registry.lazycat.cloud/app-proxy:v0.1.0`。

## 使用方法
目前有两种使用模式：
- 通过环境变量配置：适用于只有一个HTTP上游服务的情况
- 通过setup_script配置：直接覆盖Openresty的配置文件，可以使用任何Openresty支持的配置

::: danger
**禁止**混合使用两种模式。
:::

下面详细介绍每种模式的使用方法。

### 环境变量
APP Proxy抽象了一些特定功能，可以让不熟悉Nginx/Openresty配置的开发者，通过环境变量快速配置，目前支持的环境变量：

| 环境变量 | 作用 | 示例 |
| - | - | - |
| UPSTREAM（必填） | 设置代理的上游HTTP服务 | `UPSTREAM=http://whoami:80` |
| BASIC_AUTH_HEADER | 设置Authorization header，绕过Basic Auth | `BASIC_AUTH_HEADER="Basic dXNlcjpwYXNzd29yZA=="` |
| REMOVE_REQUEST_HEADERS | 移除HTTP请求头，多个请求头以英文;分隔 | `REMOVE_REQUEST_HEADERS="Origin;Host;"` |

### setup_script
在开始之前，您需要先了解[setup_script的原理](advanced-setupscript.md)；除此之外，还需要了解Nginx的配置。

您可以直接在setup_script中，覆盖Openresty的配置文件，甚至还可以写一些Lua脚本，进行更为复杂的配置。

这里给出一个简单的示例：

```yaml
lzc-sdk-version: '0.1'
name: APP Proxy Test
package: cloud.lazycat.app.app-proxy-test
version: 0.0.1
application:
  routes:
    # 将请求转发到APP Proxy（app-proxy service)
    - /=http://app-proxy:80
  subdomain: app-proxy-test
services:
  app-proxy:
    image: registry.lazycat.cloud/app-proxy:v0.1.0
    setup_script: |
      # 覆盖Openresty的配置文件
      cat <<'EOF' > /etc/nginx/conf.d/default.conf
      # 任何Nginx/Openresty支持的配置
      server {
         server_name  app-proxy-test.*;
         location / {
            root   /usr/local/openresty/nginx/html;
            index  index.html index.htm;
         }
      }
```

## 示例
### 查看应用请求日志
只要使用了APP Proxy，您就可以通过`lzc-cli docker logs -f`查看请求日志。
比如，在以下示例中，你就可以通过`lzc-cli docker logs -f cloudlazycatappapp-proxy-test-app-proxy-1`查看请求日志。
```yaml
lzc-sdk-version: '0.1'
name: APP Proxy Test
package: cloud.lazycat.app.app-proxy-test
version: 0.0.1
application:
  routes:
    - /=http://app-proxy:80
  subdomain: app-proxy-test
services:
  app-proxy:
    image: registry.lazycat.cloud/app-proxy:v0.1.0
    environment:
      - UPSTREAM="http://whoami:80"
  whoami:
    image: registry.lazycat.cloud/snyh1010/traefik/whoami:c899811bc4a1f63a
```

### 绕过Basic Auth
通过设置`BASIC_AUTH_HEADER`环境变量，您可以为请求注入`Authorization`请求头，让应用实现免登录。

`BASIC_AUTH_HEADER`的值为`Basic base64(用户名:密码)`。在以下示例中，假设用户名是`user`，密码是`password`，`echo -n "user:password" | base64`得到的base64编码为`dXNlcjpwYXNzd29yZA==`。

```yaml
lzc-sdk-version: '0.1'
name: APP Proxy Test
package: cloud.lazycat.app.app-proxy-test
version: 0.0.1
application:
  routes:
    - /=http://app-proxy:80
  subdomain: app-proxy-test
services:
  app-proxy:
    image: registry.lazycat.cloud/app-proxy:v0.1.0
    environment:
      - UPSTREAM="http://whoami:80"
      - BASIC_AUTH_HEADER="Basic dXNlcjpwYXNzd29yZA=="
  whoami:
    image: registry.lazycat.cloud/snyh1010/traefik/whoami:c899811bc4a1f63a
```

### 删除请求Header
通过设置`REMOVE_REQUEST_HEADERS`，环境变量，可以删除特定的请求头。

假如，我们想删除Origin请求头，我们可以设置`REMOVE_REQUEST_HEADERS="Origin"`，然后就可以删除`Origin`请求头。

```yaml
lzc-sdk-version: '0.1'
name: APP Proxy Test
package: cloud.lazycat.app.app-proxy-test
version: 0.0.1
application:
  routes:
    - /=http://app-proxy:80
  subdomain: app-proxy-test
services:
  app-proxy:
    image: registry.lazycat.cloud/app-proxy:v0.1.0
    environment:
      - UPSTREAM="http://whoami:80"
      - REMOVE_REQUEST_HEADERS="Origin;Cache-Control;"
  whoami:
    image: registry.lazycat.cloud/snyh1010/traefik/whoami:c899811bc4a1f63a
```

### 多域名支持
目前，懒猫微服已经支持[一个应用使用多个域名](advanced-secondary-domains.md)。

结合setup_script，您可以实现复杂的路由功能，将多个域名，分别转发到应用的不同后端。

在以下示例中，不同的域名将会被转发到不同的后端：
- `app-proxy-test.xxx.heiyu.space`将会被转发到Openresty的默认首页
- `portainer.xxx.heiyu.space`将会被转发到Portainer
- `whoami.xxx.heiyu.space`将会被转发到whoami


```yaml
lzc-sdk-version: '0.1'
name: APP Proxy Test
package: cloud.lazycat.app.app-proxy-test
version: 0.0.1
application:
  routes:
    - /=http://app-proxy.cloud.lazycat.app.app-proxy-test.lzcapp:80
  subdomain: app-proxy-test # 应用列表里默认打开的域名
  secondary_domains:
    - portainer
    - whoami
services:
  app-proxy:
    image: registry.lazycat.cloud/app-proxy:v0.1.0
    setup_script: |
      cat <<'EOF' > /etc/nginx/conf.d/default.conf
      server {
         server_name  app-proxy-test.*;
         location / {
            root   /usr/local/openresty/nginx/html;
            index  index.html index.htm;
         }
      }

      server {
         server_name  portainer.*;

         location / {
            proxy_pass http://portainer:9000;
         }
      }

      server {
         server_name  whoami.*;

         location / {
            proxy_pass http://whoami:80;
         }
      }
      EOF
  portainer:
    image: registry.lazycat.cloud/u8997806945/portainer/portainer-ce:d393c0c7d12aae78
  whoami:
    image: registry.lazycat.cloud/snyh1010/traefik/whoami:c899811bc4a1f63a
```
