# 规范校准（打包前必做）

> **本文件是"防过期"机制，不是规范本身。**
>
> 懒猫官方规范会**不定期更新**，而本技能包 `references/` 下的规范文档是**某一时刻的快照**，会落后。
> 因此：**任何一次打包/构建动作之前，必须先执行本文第 2–5 节的校准流程。** 这不是可选步骤。

---

## 1. 权威来源（按优先级）

本地 `references/` 永远排在最后。三方冲突时，以高优先级来源为准：

| 优先级 | 来源 | 地址 | 说明 |
| --- | --- | --- | --- |
| **1** | 官方文档**源仓库**（markdown 源） | <https://gitee.com/lazycatcloud/lzc-developer-doc> | 机器可直接读取、字段最精确、更新最快。**首选** |
| **2** | 官方开发者**文档站** | <https://developer.lazycat.cloud/> | 人可读渲染版。作为兜底与交叉验证 |
| 3 | 本技能包 `references/` | 本地 | **仅当 1、2 均不可用时**，且必须向用户声明"规范可能已过期" |

**raw 链接格式**（已验证返回 `text/plain` markdown，可直接 `curl` / 抓取）：

```text
https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/<路径>.md
```

---

## 2. 第一步：拉取最新规范原文

### 2.1 核心规范（打包必读，5 篇）

| 内容 | raw markdown（首选） | 文档站（兜底） |
| --- | --- | --- |
| `package.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/package.md> | <https://developer.lazycat.cloud/spec/package.html> |
| `lzc-manifest.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/manifest.md> | <https://developer.lazycat.cloud/spec/manifest.html> |
| `lzc-build.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/build.md> | <https://developer.lazycat.cloud/spec/build.html> |
| `lzc-deploy-params.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/deploy-params.md> | <https://developer.lazycat.cloud/spec/deploy-params.html> |
| LPK 包格式 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/lpk-format.md> | <https://developer.lazycat.cloud/spec/lpk-format.html> |

**一次性拉取命令**（推荐，避免逐篇抓取）：

```bash
mkdir -p /tmp/lzc-spec && BASE=https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs
for f in spec/package spec/manifest spec/build spec/deploy-params spec/lpk-format; do
  curl -sSL "$BASE/$f.md" -o "/tmp/lzc-spec/$(basename "$f").md" \
    && echo "OK  $(basename "$f").md  $(wc -c < "/tmp/lzc-spec/$(basename "$f").md") bytes"
done
```

### 2.2 按需读取（命中对应能力时才读）

| 涉及能力 | raw markdown |
| --- | --- |
| HTTP 路由 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-route.md> |
| 应用多域名 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-secondary-domains.md> |
| TCP/UDP 四层转发 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-l4forward.md> |
| 独立鉴权 / `public_path` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-public-api.md> |
| OIDC 单点登录 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-oidc.md> |
| HTTP Headers 身份识别 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/http-request-headers.md> |
| 脚本注入 `injects` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-injects.md> |
| manifest 模板渲染 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-manifest-render.md> |
| 初始化脚本 `setup_script` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-setupscript.md> |
| 部署时环境变量 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-envs.md> |
| API Auth Token | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-api-auth-token.md> |
| 应用间访问 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-app-interconnect.md> |
| Skill / MCP 资源（导入/导出） | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/resource-skill-mcp.md> |
| 资源导出规范 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/resource-export.md> |
| 上架审核规则 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/store-submission-guide.md> |
| GPU 加速 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-gpu.md> |
| 多实例 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-multi-instance.md> |

---

## 3. 第二步：与本技能包快照比对

拉取后，**用官方原文覆盖本地快照的字段认知**。重点核对以下"最容易过期"的位置：

| 核对项 | 为什么容易过期 |
| --- | --- |
| `package.yml` 顶层字段与 `permissions` 权限 id 清单 | 每个 lzcos 版本都在新增（如 `user.notify`、`fuse.mount`、`hidden_from_launcher`、`import_resources`） |
| `lzc-build.yml` 字段名 | **字段会被改名**：`pkg_id` 已由 `package_override` 取代 |
| `lzc-manifest.yml` 的 `application.*` 字段表 | 持续新增（`run_as`、`entries`、`vt`、`ingress` 等） |
| `application.injects` 的字段名 | 存在历史写法（`include`/`mode`/`scripts`）与现行写法（`when`/`unless`/`do`）之别，**必须以上游为准** |
| 各类版本门槛（`lzcos vX.Y.Z+`） | 官方会随能力上线调整 |
| 存储路径语义 | 旧路径会废弃（如 `/lzcapp/run/mnt/home` → `/lzcapp/documents/$uid`） |
| 上架审核红线条数 | 官方会新增（如"必须支持免密登录"） |

---

## 4. 第三步：冲突裁决

当本地 `references/` 与上游原文不一致时，**无条件按以下顺序处理**：

1. **以上游为准**生成配置。本地快照在此处视为过期，不得引用。
2. **不要静默忽略**。必须向用户显式说明：

   > ⚠️ 本技能包的 `references/<文件>:<行>` 记录的 `<本地写法>` 已过期，
   > 官方最新规范（<来源链接>）为 `<官方写法>`；本次已按官方写法生成。

3. 若冲突涉及**字段名或字段是否存在**（会直接导致构建失败），即使只影响示例也要指出。

---

## 5. 第四步：留下校准记录

在交付打包结果时，附一行校准信息，便于问题追溯：

```text
规范校准：已读取官方文档源（gitee.com/lazycatcloud/lzc-developer-doc @ <commit 或日期>）
  已核对：package.yml / lzc-manifest.yml / lzc-build.yml
  发现差异：<有/无>；<如有，列出>
```

---

## 6. 降级规则（网络不可用时）

1. 依次尝试：Gitee raw → 文档站 → 本地 `references/`。
2. 若三者只剩本地快照可用，**必须**在交付时声明：

   > ⚠️ 当前无法访问官方规范来源，本次基于本技能包的**本地快照**生成，可能存在过期风险。
   > 建议恢复网络后重新校准，或人工核对 <https://developer.lazycat.cloud/>。

3. **不允许**因为"拉取失败"而跳过校准声明。

---

## 7. 维护本文件

本文件刻意**只放来源链接与流程，不放任何字段内容**——因此它自身不随规范演进过期。当官方新增规范页面时，只需在 §2 的表格中补一行。
