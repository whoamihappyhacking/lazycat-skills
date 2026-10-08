---
name: lazycat-aipod-developer
description: 懒猫 AI 算力舱应用开发与打包：AIApp resource、AGX Orin/Thor 型号 compose、Traefik AI host、浏览器插件、启动 gate、数据路径及旧包迁移。
---

# AI Pod 应用：资源与设备兼容

## 先校准两个来源

写/改配置或 build/deploy/release 前，读取并执行 `references/spec-sync.md`，确认微服、CLI、算力舱/消费端版本。**还必须读取 AI Pod 独立官方专题**：

- <https://developer.lazycat.cloud/aipod/package/spec.html>
- 必要时按章节检索 <https://developer.lazycat.cloud/aipod/llms-full.txt>，不要一次加载整站。

通用 LPK 源仓库不覆盖所有 AI Pod 能力。当前专题的资源导入位置/投影路径与通用 V2 规范存在差异，先按 `references/aipod-app-spec.md` 识别边界；不能猜测转换后声称可部署。

## 行动流程

1. 读取 `references/aipod-app-spec.md`，根据用户设备选择 agxorin/thor compose，不假定所有设备只是一种 Jetson。
2. 新配置使用 resource 中 config/aipod.yml（无外层 aipod）、型号目录、extensions 与平台 startup gate；旧 ai-pod-service/browser-extensions 仅作为兼容 fallback。
3. 核实各设备镜像架构/GPU软件栈，AI host 必须一致且以 -ai 结尾，加入 traefik-shared-network；长初始化服务配真实就绪探针。
4. 数据用 LZC_AGENT_DATA_DIR，缓存用 LZC_AGENT_CACHE_DIR，Traefik 标识用 LZC_SERVICE_ID；平台默认 NVIDIA runtime，无需机械添加 gpus/runtime。
5. 若专题与通用 schema 不一致，核实目标工具链与资源消费端后再生成完整包；只做构建/静态校验时，不宣称真实部署、模型推理或所有型号兼容。

安装、发布、设备变更需授权；需微服名称主动执行 `lzc-cli box default`。不把文档中的设备序列号或微服名复制进产物。
