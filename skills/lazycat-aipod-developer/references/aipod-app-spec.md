# AI 应用打包与发布规范

## AI 应用结构

`AI应用` 是在微服应用基础上，添加 `AI服务` 或 `AI浏览器插件` 的应用。安装后会自动部署服务到算力舱。

### lpk 包目录结构

```
ai-pod-service/              # AI 服务目录
  docker-compose.yml          # 服务编排文件
  README.md                   # 可选的说明文件
  check_ollama.py             # 可选的检查脚本等
content.tar                   # 微服应用内容
extension.zip                 # 可选-浏览器插件
icon.png                      # 应用图标
manifest.yml                  # 应用清单
```

## 添加 AI 服务

在 `lzc-build.yml` 中添加 `ai-pod-service` 字段：

```yml
# ai-pod-service: 指定算力舱的服务目录，会将里面的内容打包到lpk中
ai-pod-service: ./ai-pod-service
```

该目录下必须包含 `docker-compose.yml`。目录内的资源可在 docker-compose 中通过路径引用。

### 算力舱提供的环境变量

1. **数据持久化路径** `LZC_AGENT_DATA_DIR`
   - 定义: `/ssd/lzc-ai-agent/data/<service_id>`
   - 示例: `/ssd/lzc-ai-agent/data/cloud.lazycat.aipod.ai`

   ```yml
   ollama:
     volumes:
       - ${LZC_AGENT_DATA_DIR}/data:/root/.ollama
   ```

2. **数据缓存路径** `LZC_AGENT_CACHE_DIR`
   - 定义: `/ssd/lzc-ai-agent/cache/<service_id>`

   ```yml
   ollama:
     volumes:
       - ${LZC_AGENT_CACHE_DIR}/cache:/root/.cache
   ```

3. **服务ID** `LZC_SERVICE_ID`
   - 对应 LPK 中的 appId，但会将 `.` 去掉
   - 示例: appId `cloud.lazycat.aipod.fish-speech` → `cloudlazycataipodfishspeech`

   ```yml
   ollama:
     labels:
       - "traefik.http.routers.${LZC_SERVICE_ID}-ollama.rule=Host(`ollama-ai`)"
   ```

> **重要**: 算力舱中的 Docker 默认使用 `nvidia-runtime`，容器中可直接使用 GPU，不需要显式指定 `gpus` 配置。

### 配置 AI 服务 Traefik 访问规则

算力舱使用 `traefik` 通过 `Host` 规则做服务转发。

1. **Host 规则** - 域名**必须**以 `-ai` 结尾

   ```yml
   services:
     ollama:
       labels:
         - "traefik.enable=true"
         - "traefik.http.routers.${LZC_SERVICE_ID}-ollama.rule=Host(`ollama-ai`)"
   ```

2. **Traefik 网络** - 必须加入 `traefik-shared-network`

   推荐设为默认网络：

   ```yml
   networks:
     default:
       external: true
       name: traefik-shared-network
   ```

   或服务级别指定：

   ```yml
   services:
     myservice:
       networks:
         - traefik-shared-network
   ```

### 完整的 docker-compose.yml 示例

```yml
services:
  whoami:
    image: registry.lazycat.cloud/traefik/whoami:ab541801c8cc
    labels:
      - "traefik.http.routers.whoami.rule=Host(`whoami-ai`)"

networks:
  default:
    external: true
    name: traefik-shared-network
```

## 添加 AI 浏览器插件

在 `lzc-build.yml` 中添加 `browser-extension` 字段：

```yml
# browser-extension: 浏览器插件，支持 zip 文件或目录
browser-extension: ./my-awesome-chrome-extension.zip
```

## 配置快捷方式

在 `lzc-manifest.yml` 中配置：

```yml
aipod:
  shortcut:
    disable: false  # 设为 true 则不在 AI 浏览器显示快捷方式
```

在 `aipod` 字段中仅支持 `.SysParams(.S)` 中的 `.BoxName` 和 `.BoxDomain` 模板参数。

## 添加启动进度提示（caddy-aipod）

AI 应用需要显示算力舱服务启动进度时，使用 `caddy-aipod` 中间件：

```yml
# lzc-manifest.yml
name: ComfyUI
package: cloud.lazycat.aipod.comfyui
version: 1.0.5
description: 最强大的开源基于节点的生成式人工智能应用程序

aipod:
  shortcut:
    disable: false

application:
  subdomain: comfyui
  routes:
    - /=http://caddy:80

services:
  caddy:
    image: registry.lazycat.cloud/catdogai/caddy-aipod:65e058ce
    setup_script: |
      cat <<'EOF' > /etc/caddy/Caddyfile
      {
              auto_https off
              http_port 80
              https_port 0
      }
      :80 {
              handle {
                      route {
                              lzcaipod
                              root * /lzcapp/pkg/content/ui/
                              try_files {path} /index.html
                              header Cache-Control "max-age=60, private, must-revalidate"
                              file_server
                      }
              }
      }
      EOF
      cat /etc/caddy/Caddyfile
```

关键：`Caddyfile` 中的 `lzcaipod` 指令会检测算力舱服务是否运行并给出进度提示。

## AI 应用依赖算力舱服务健康检测（微服 1.3.8+）

使用 `upstreams` 访问算力舱的 health check 接口：

```yml
application:
  subdomain: comfyui
  gpu_accel: true
  routes:
    - /=file:///lzcapp/pkg/content/dist
  health_check:
    test_url: http://127.0.0.1/version
    start_period: 5m

  upstreams:
    - location: /version
      backend: https://comfyui-ai.{{ .S.BoxDomain }}/api/manager/version
      trim_url_suffix: /
      use_backend_host: true
      dump_http_headers_when_5xx: true
```

## 发布 AI 应用

1. 算力舱分类：https://appstore.lazycat.cloud/#/shop/category/27
2. 发布方式与普通微服应用一致，通过 `lzc-cli` 或开发者平台提交
3. 提交时写上 `AI Pod` 或 `算力舱` 关键词，方便审核分类

## 指定某一个算力舱上的服务

多个算力舱时，通过域名格式访问：`f-{算力舱序列号}-{服务名称}-ai.{微服名称}.heiyu.space`

示例：`https://f-1420225016421-dozzle-ai.your-box-name.heiyu.space`
