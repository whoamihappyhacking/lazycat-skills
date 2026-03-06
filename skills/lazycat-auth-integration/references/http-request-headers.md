http headers
==============

所有从客户端发起的https/http的流量会先进入`lzc-ingress`这个组件进行分流。

lzc-ingress主要处理以下任务

- 对http请求进行鉴权，若未登录则跳转到登录页面
- 根据请求的域名分流到不同的lzcapp后端

在鉴权成功转发给具体的lzcapp前，`lzc-ingress`会设置以下额外的http headers

- `X-HC-User-ID`        登录的UID(用户名)
- `X-HC-Device-ID`      客户端位于本微服内的唯一ID， 应用程序可以使用这个作为设备标识符
- `X-HC-Device-PeerID`  客户端的peerid， 仅内部使用。
- `X-HC-Device-Version` 客户端的内核版本号
- `X-HC-Login-Time` 微服客户端最后一次的登录时间， 格式为unix时间戳(一个int32的整数)
- `X-HC-User-Role`  普通用户为:"NORMAL"， 管理员用户为: "ADMIN"
- `X-Forwarded-Proto` 固定为"https"，以便少量强制https的应用可以正常工作
- `X-Forwarded-By`  固定为"lzc-ingress"



`lzc-ingress`是通过`HC-Auth-Token`这个cookie来进行鉴权的(客户端内是通过其他内部方式完成鉴权)。

当`lzc-ingress`遇到此cookie值无效或为空时，且目标地址不是`public_path`，则会跳转到登录页面。

当目标地址为`public_path`时， `lzc-ingress`依旧会进行一次鉴权，但不会跳转到登录页面。
- 如果鉴权失败，则会清空上述`X-HC-XX`的header，避免一些安全风险
- 如果鉴权成功，则会带上上述`X-HC-XX`的header。

也就是lzcapp开发者在编写后端代码时，不用考虑是否为`public_path`， 直接信任`X-HC-User-ID`即可。
