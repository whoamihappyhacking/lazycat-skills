一个应用使用多个域名
===================

`lzc-manifest.yml:application.subdomain`是开发者期望使用的域名，但微服系统(v1.3.6+后)会进行一定调整

1. 如果多个应用使用相同的`subdomain`字段，则后安装的会被添加域名小尾巴
2. 多实例类型应用，同一个应用每个用户会分配独立的域名，因此非管理员看到的域名大概率会加上小尾巴
3. 域名前缀概念:  `xxxx-subdomain`的域名和`subdomain`的效果是一致，即每个应用自动拥有任意多个域名。
4. 最终实际分配到的`subdomain`只能通过环境变量`LAZYCAT_APP_DOMAIN`获取到。
5. 所有前缀域名进入的流量都会忽略`TCP/UDP Ingress`配置。 (不影响默认应用域名进入的流量)


v1.3.8已支持[基于域名的流量转发](./advanced-route#upstreamconfig)

由于`application.routes`不支持基于域名的转发，如果需要比较细致的调整路由规则，
可以添加一条特殊route规则，`- /=http://nginx.$appid.lzcapp`。
注意这里一定要用`$service.$appid.lzcapp`的形式，否则nginx无法收到完整的域名信息，[原因见](advanced-route.html#p2)

比如，下面这个配置的效果是
1. 应用列表里打开默认是`whoami.xx.heiyu.space`(假设实际分配到的`subdomain`是`whoami`)
2. `nginx-whoami.xx.heiyu.space`流量会返回默认的nginx静态hello world
3. `任意内容-whoami.xx.heiyu.space`与访问`whoami.xx.heiyu.space`效果相同


```yaml

package: org.snyh.debug.whoami
name: whoami-lazycatmicroserver

application:
  subdomain: whoami
  routes:
    - /=http://nginx.org.snyh.debug.whoami.lzcapp:80

services:
  nginx:
    image: registry.lazycat.cloud/snyh1010/library/nginx:54809b2f36d0ff38
    setup_script: |
      cat <<'EOF' > /etc/nginx/conf.d/default.conf
      server {  # whoami.xxx.heiyu.space以及其他任意域名前缀都转发到traefix/whoami
         server_name _;
         location / {
            proxy_pass http://app1:80;
            #目前setup_script机制还有点问题，这里不能直接写环境变量，如果有这个需求则
            #只能使用binds的形式把文件放到pkg/content中binds进去
         }
      }
      server {  # nginx开头的域名转发到nginx默认页，比如nginx3-whoami.xxx.heiyu.space, nginx-whoami.xxx.heiyu.space
         server_name  ~^nginx.*-.*;
         location / {
            root   /usr/share/nginx/html;
            index  index.html index.htm;
         }
      }

      EOF
  app1:
    image: registry.lazycat.cloud/snyh1010/traefik/whoami:c899811bc4a1f63a
```
