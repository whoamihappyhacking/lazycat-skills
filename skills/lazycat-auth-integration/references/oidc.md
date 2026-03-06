lzcapp对接微服的OIDC
====================

v1.3.5+提供了统一的oidc的支持，lzcapp适配oidc后即可自动获取uid和对应权限组(`ADMIN`代表管理员)

开发者只需要在manifest.yml中提供以下两个信息即可完成适配。

1. 在`application.oidc_redirect_path`中填写正确的oidc回调地址
     这个路径一般是`/oauth2/callback`或者`/auth/oidc.callback`，
     具体需要查阅应用本身的文档。如果应用文档未提供相关信息，可以先随便填写一个，
     登录时浏览器报错时可以查看到实际使用的路径。

2. 通过部署时环境变量获取系统自动生成的相关环境变量给实际应用即可。
    必填项为`client_id`、`client_secret`。
    部分应用额外只需要填写一个ISSUER信息，剩下的会自动事实探测。
    部分应用则需要填写多个具体ENDPOINT的信息， 具体支持的信息可以参考[部署时环境变量](./advanced-envs#deploy_envs)。


::: warning oidc_redirect_path
必须设置了`application.oidc_redirect_path`系统才会动态生成oidc client相关的环境变量

如果您不知道这个值应该填写什么，可以先随便填写，一般应用的报错页面会告知您正确值。
:::


比如outline这个应用的OIDC适配，根据[outline官方文档](https://docs.getoutline.com/s/hosting/doc/oidc-8CPBm6uC0I)得知需要设置以下环境变量
* `OIDC_CLIENT_ID` – OAuth client ID
* `OIDC_CLIENT_SECRET` – OAuth client secret
* `OIDC_AUTH_URI`
* `OIDC_TOKEN_URI`
* `OIDC_USERINFO_URI`

在manifest.yml中可以这样填写
```yml
name: Outline
package: cloud.lazycat.app.outline
version: 0.0.1
application:
  subdomain: outline
  #outline官方文档没有提供这个信息，但通过报错信息可以得到这个地址
  oidc_redirect_path: /auth/oidc.callback
  routes:
    - /=http://outline.cloud.lazycat.app.outline.lzcapp:3000
services:
  outline:
    image: registry.lazycat.cloud/tx1ee/outlinewiki/outline:fb0e2ef4f32f3601
    environment:
      - OIDC_CLIENT_ID=${LAZYCAT_AUTH_OIDC_CLIENT_ID}
      - OIDC_CLIENT_SECRET=${LAZYCAT_AUTH_OIDC_CLIENT_SECRET}
      - OIDC_AUTH_URI=${LAZYCAT_AUTH_OIDC_AUTH_URI}
      - OIDC_TOKEN_URI=${LAZYCAT_AUTH_OIDC_TOKEN_URI}
      - OIDC_USERINFO_URI=${LAZYCAT_AUTH_OIDC_USERINFO_URI}
```


oidc issuer info
===============

访问`https://$微服名称.heiyu.space/sys/oauth/.well-known/openid-configuration#/`可以获取完整的issuer信息。

然后使用 `https://$LAZYCAT_BOXDOMAIN/$endpoint_path`即可自行获取任何endpoint的地址信息。


```json
{
"issuer": "https://snyht13.heiyu.space/sys/oauth",
"authorization_endpoint": "https://snyht13.heiyu.space/sys/oauth/auth",
"token_endpoint": "https://snyht13.heiyu.space/sys/oauth/token",
"jwks_uri": "https://snyht13.heiyu.space/sys/oauth/keys",
"userinfo_endpoint": "https://snyht13.heiyu.space/sys/oauth/userinfo",
"device_authorization_endpoint": "https://snyht13.heiyu.space/sys/oauth/device/code",
"introspection_endpoint": "https://snyht13.heiyu.space/sys/oauth/token/introspect",
"grant_types_supported": [
"authorization_code",
"refresh_token",
"urn:ietf:params:oauth:grant-type:device_code",
"urn:ietf:params:oauth:grant-type:token-exchange"
],
"response_types_supported": [
"code"
],
"subject_types_supported": [
"public"
],
"id_token_signing_alg_values_supported": [
"RS256"
],
"code_challenge_methods_supported": [
"S256",
"plain"
],
"scopes_supported": [
"openid",
"email",
"groups",
"profile",
"offline_access"
],
"token_endpoint_auth_methods_supported": [
"client_secret_basic",
"client_secret_post"
],
"claims_supported": [
"iss",
"sub",
"aud",
"iat",
"exp",
"email",
"email_verified",
"locale",
"name",
"preferred_username",
"at_hash"
]
}
```
