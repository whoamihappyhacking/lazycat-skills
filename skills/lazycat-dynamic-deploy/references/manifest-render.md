# manifest.yml渲染

lzcos-v1.3.8+ 支持 manifest.yml 文件的动态渲染，以便开发者可以更好的控制部署参数。

manifest.yml 的渲染流程为

1. 开发者在项目根目录下创建一个 [lzc-deploy-params.yml](./spec/deploy-params) 文件，并使用 `lzc-cli project build` 打包到 lpk 中(需要 lzc-cli 版本 v1.3.7+)
2. 在运行前会跳转到一个参数补充的UI界面，要求用户补充开发者在 `lzc-deploy-params.yml` 中定义的所有参数
3. 系统获取到用户提供的参数，并将其作为模板参数 `U` 与 lpk 中的 lzc-manifest.yml 一起渲染为最终结果
4. 将最终的manifest存放在 `/lzcapp/run/manifest.yml` (相对于原始文件 `/lzcapp/pkg/manifest.yml` )并以此作为最终文件


--------------

1. 用户可以在应用列表中主动重新进入修改部署参数的页面，点击后进入步骤 2。每次修改部署参数后应用实例会被停止并重新走上述流程
2. 多实例应用下，每个用户的部署参数都是独立的，由每个用户自行填写。
3. 即使应用没有配置 `lzc-deploy-params.yml` 依旧会进行 manifest 渲染流程

## 渲染机制

使用 golang 的 `text/template` 对 lpk 中的 manifest.yml 进行渲染，您需要先熟悉一下[Go官方的模板语法](https://pkg.go.dev/text/template)外
以下为一些内置的模板函数和模板参数。


## 内置模板函数

1. [spring](https://masterminds.github.io/sprig/) 支持的函数。( env 相关除外)
2.  `stable_secrt "seed"` 模板函数，用来产生稳定的密码。此函数需要传递一个任意字符串。
    1. 同样的 seed，不同应用的结果保证不相同
    1. 同样的 seed，同样的应用不同的微服结果保证不相同
    2. 同样的 seed，相同的应用相同的微服(未重新恢复出厂设置)保证多次调用结果相同

## 模板参数

主要为两个大参数(括号内为其简写方式)

- `.UserParams(.U)` lzc-deploy-params.yml 中要求的参数

- `.SysParams(.S)` 系统相关参数
    - `.BoxName`  微服的名称
    - `.BoxDomain`  微服的域名
    - `.OSVersion`  微服系统版本号，注意如果是测试版则会强制修改为 `v99.99.99-xxx`
    - `.AppDomain`  应用的域名，注意此域名目前是根据开发者写死，将来会动态分配并支持管理员动态调整。
    - `.IsMultiInstance` 是否为多实例部署方式，目前是开发者写死，将来版本会调整为管理员可以动态调整最终值。
    - `.DeployUID`  实际部署时的用户ID,单实例部署方案下无此字段。
    - `.DeployID`   实例本身的唯一ID



::: tip
调试阶段，您可以在 lzc-manifest.yml 任意位置添加来渲染出所有的可用参数
```
xx-debug: {{ . }}
```

您可以在 `application.route` 里增加一条规则来查看最终的 manifest.yml
```
application:
    route:
        - /m=file:///lzcapp/run/manifest.yml
```
或直接使用 devshell 后 `cat /lzcapp/run/manifest.yml`
:::

## 示例

完整 demo 示例可以参考[这里](https://gitee.com/lazycatcloud/netmap)

### 更安全的内部密码

```yml
package: cloud.lazycat.app.redmine
name: Redmine
services:
  mysql:
    binds:
    - /lzcapp/var/mysql:/var/lib/mysql
    environment:
    - MYSQL_ROOT_PASSWORD={{ stable_secret "root_password" }}
    - MYSQL_USER=LAZYCAT
    - MYSQL_PASSWORD={{ stable_secret "admin_password" | substr 0 6 }}
    image: registry.lazycat.cloud/mysql
  redmine:
    environment:
    - DB_PASSWORD={{ stable_secret "root_password" }}
```

### 多实例/单实例不同配置

如果是单实例应用，则将数据放到每个用户的文稿目录下

如果是多实例应用，则将用户数据放到应用内部


```yml
#lzc-manifest.yml

services:
  some_service_name:
    binds:
    {{ if .S.IsMultiInstance }}
      - /lzcapp/run/mnt/home:/home/
    {{ else }}
      - /lzcapp/run/mnt/home/{{ .S.DeployUID }}/the_name:/home/
    {{ end }}
```


### 启动参数由用户配置
```yml
#lzc-deploy-params.yml
params:
  - id: target
    type: string
    name: "target"
    description: "the target IP you want forward"

  - id: listen.port
    type: string
    name: "listen port"
    description: "the forwarder listen port, can't be 80, 81"
    default_value: "33"
    optional: true
```

```yml
#lzc-manifest.yml
package: org.snyh.netmap
version: 0.0.1
name: netmap
application:
  subdomain: netmap

  upstreams:
    - location: /
      backend_launch_command: /lzcapp/pkg/content/netmap -target={{ .U.target }} -port={{ index .U "listen.port" }}
```
