# 规范校准（产出配置前必做）

> 本文件以**校准流程和官方来源**为主，不是规范字段快照；来源、工具和流程本身仍需维护。
> 本技能内的其他 `references/` 只是在某一时刻保存的说明，不能替代当次校准。

## 1. 先核验目标版本

在读取“最新规范”前，先取得并记录本次目标环境的明确版本：

- 目标 lzcos 版本；
- 目标 `lzc-cli` 版本；
- 本次会使用的能力（构建、路由、注入、认证、Compose override、VT、entries 等）。

不得把 `latest`、`unknown` 或“当前最新版”当成版本核验结果。字段出现在最新文档中，不代表目标设备已经支持；下载原文后还要逐项核对文档标注的版本门槛。无法确认目标版本时，先向用户说明并停止产出最终配置。

## 2. 使用技能自带 helper

在**已安装技能的根目录**执行；脚本只使用 Python 标准库：

```bash
: "${LZCOS_VERSION:?请设置目标 lzcos 版本，例如 1.6.1}"
: "${LZC_CLI_VERSION:?请设置目标 lzc-cli 版本，例如 2.0.9}"
python3 scripts/sync-specs.py \
  --lzcos-version "$LZCOS_VERSION" \
  --cli-version "$LZC_CLI_VERSION"
```

默认拉取 5 篇核心规范。按需专题可重复指定，或拉取全部来源：

```bash
: "${LZCOS_VERSION:?请设置目标 lzcos 版本，例如 1.6.1}"
: "${LZC_CLI_VERSION:?请设置目标 lzc-cli 版本，例如 2.0.9}"
python3 scripts/sync-specs.py \
  --lzcos-version "$LZCOS_VERSION" \
  --cli-version "$LZC_CLI_VERSION" \
  --topic passwordless-login \
  --topic inject-dev-cookbook \
  --topic compose-override \
  --topic vt \
  --topic entries

python3 scripts/sync-specs.py \
  --lzcos-version "$LZCOS_VERSION" \
  --cli-version "$LZC_CLI_VERSION" \
  --all
```

若已从官方仓库核实 commit，可固定原文版本：

```bash
: "${LZCOS_VERSION:?请设置目标 lzcos 版本，例如 1.6.1}"
: "${LZC_CLI_VERSION:?请设置目标 lzc-cli 版本，例如 2.0.9}"
: "${OFFICIAL_DOC_COMMIT:?请设置已核实的 7 至 40 位官方 commit}"
python3 scripts/sync-specs.py \
  --lzcos-version "$LZCOS_VERSION" \
  --cli-version "$LZC_CLI_VERSION" \
  --official-commit "$OFFICIAL_DOC_COMMIT"
```

helper 的行为边界：

- 通用规范每页严格按 **Gitee raw → 官方文档站** 尝试；AI Pod 独立专页没有通用仓库 raw，只读取其官方站点，HTTP 错误不会当成成功；
- raw/官方文本必须是 UTF-8、有 Markdown 标题结构且首标题不是明显错误；站点 HTML 必须有 VitePress 正文与标题或合理的 main/article 正文结构；HTML 冒充 raw、空体、类型异常、错误页/验证页、超限正文都会失败；
- 每次网络操作有有限超时，单页失败不会阻止其余页面校验；
- 每次运行创建新的任务目录，正文先写临时文件再原子替换，不共享固定缓存目录；
- `calibration.json` 记录目标版本、实际最终 URL、来源类型、字节数和每篇原文 SHA-256；指定 commit 时也会记录 commit；
- 任一页面的 raw 与文档站都失败时，脚本汇总所有失败、写入明确的离线声明并以非零状态退出，**不会把本地快照或错误页冒充校准成功**。

默认任务目录位于系统临时目录。需要保留到指定父目录时使用 `--output-root <目录>`；其下仍会创建本次任务独占的随机目录。

## 3. 权威来源与降级顺序

冲突时按下列顺序裁决：

1. 官方文档源仓库原文：<https://gitee.com/lazycatcloud/lzc-developer-doc>；
2. 官方开发者文档站：<https://developer.lazycat.cloud/>；
3. 技能内本地 `references/` 快照。

raw 首选是因为便于机器校验、固定 commit 和计算 digest，不代表它必然比文档站更早发布。文档站是第二个**在线官方来源**。只有前两者均不可用时才可人工参考本地快照，此时必须向用户声明：

> ⚠️ 当前无法完成官方规范校准；本次仅参考技能内本地快照，可能已经过期。未将离线结果声明为校准成功，网络恢复后必须重跑。

## 4. 核心规范（默认拉取）

| topic | 内容 | raw markdown | 文档站 |
| --- | --- | --- | --- |
| `package` | `package.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/package.md> | <https://developer.lazycat.cloud/spec/package.html> |
| `manifest` | `lzc-manifest.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/manifest.md> | <https://developer.lazycat.cloud/spec/manifest.html> |
| `build` | `lzc-build.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/build.md> | <https://developer.lazycat.cloud/spec/build.html> |
| `deploy-params` | `lzc-deploy-params.yml` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/deploy-params.md> | <https://developer.lazycat.cloud/spec/deploy-params.html> |
| `lpk-format` | LPK 包格式 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/lpk-format.md> | <https://developer.lazycat.cloud/spec/lpk-format.html> |

## 5. AI Pod 独立专页（AI Pod 配置额外必读）

AI Pod 规范**不在通用 Gitee `lzc-developer-doc` 仓库中**。产出或修改 AI Pod 配置时，除第 4 节通用核心规范外，还必须读取并记录以下两个官方来源：

| topic | 内容 | 官方专页 |
| --- | --- | --- |
| `aipod-package-spec` | AI Pod package 专项规范 | <https://developer.lazycat.cloud/aipod/package/spec.html> |
| `aipod-llms-full` | AI Pod 完整文档文本 | <https://developer.lazycat.cloud/aipod/llms-full.txt> |

从 `lazycat-aipod-developer` 技能根目录运行 helper 时，这两页会被**强制附加**到默认、`--topic` 和 `--all` 校准中。二者没有可固定的通用仓库 commit，因此以 `calibration.json` 中的实际 URL 与逐页 SHA-256 原文 digest 留痕；任一页失败都不能宣称“AI Pod 已完成校准”。只读取通用五篇核心规范，**不构成 AI Pod 校准成功**。

## 6. 按需专题来源

命中相关能力时，用 `--topic <topic>` 同步对应页面：

| topic | 能力 | raw markdown | 文档站 |
| --- | --- | --- | --- |
| `route` | HTTP 路由 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-route.md> | <https://developer.lazycat.cloud/advanced-route.html> |
| `secondary-domains` | 应用多域名 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-secondary-domains.md> | <https://developer.lazycat.cloud/advanced-secondary-domains.html> |
| `l4forward` | TCP/UDP 四层转发 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-l4forward.md> | <https://developer.lazycat.cloud/advanced-l4forward.html> |
| `public-api` | 独立鉴权 / `public_path` | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-public-api.md> | <https://developer.lazycat.cloud/advanced-public-api.html> |
| `oidc` | OIDC 单点登录 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-oidc.md> | <https://developer.lazycat.cloud/advanced-oidc.html> |
| `headers` | HTTP 身份 Header | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/http-request-headers.md> | <https://developer.lazycat.cloud/http-request-headers.html> |
| `injects` | 注入机制与 API | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-injects.md> | <https://developer.lazycat.cloud/advanced-injects.html> |
| `passwordless-login` | **免密登录专题与参数附录** | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-inject-passwordless-login.md> | <https://developer.lazycat.cloud/advanced-inject-passwordless-login.html> |
| `inject-dev-cookbook` | **开发态注入 Cookbook** | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-inject-request-dev-cookbook.md> | <https://developer.lazycat.cloud/advanced-inject-request-dev-cookbook.html> |
| `manifest-render` | manifest 模板渲染 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-manifest-render.md> | <https://developer.lazycat.cloud/advanced-manifest-render.html> |
| `setup-script` | 初始化脚本 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-setupscript.md> | <https://developer.lazycat.cloud/advanced-setupscript.html> |
| `envs` | 部署时环境变量 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-envs.md> | <https://developer.lazycat.cloud/advanced-envs.html> |
| `api-auth-token` | API Auth Token | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-api-auth-token.md> | <https://developer.lazycat.cloud/advanced-api-auth-token.html> |
| `app-interconnect` | 应用间访问 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-app-interconnect.md> | <https://developer.lazycat.cloud/advanced-app-interconnect.html> |
| `compose-override` | **Compose override** | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-compose-override.md> | <https://developer.lazycat.cloud/advanced-compose-override.html> |
| `entries` | **应用 entries** | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-entries.md> | <https://developer.lazycat.cloud/advanced-entries.html> |
| `vt` | **VT 图形应用** | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-vt.md> | <https://developer.lazycat.cloud/advanced-vt.html> |
| `skill-mcp` | Skill / MCP 资源 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/resource-skill-mcp.md> | <https://developer.lazycat.cloud/resource-skill-mcp.html> |
| `resource-export` | 资源导出规范 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/spec/resource-export.md> | <https://developer.lazycat.cloud/spec/resource-export.html> |
| `store-submission` | 上架审核规则 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/store-submission-guide.md> | <https://developer.lazycat.cloud/store-submission-guide.html> |
| `gpu` | GPU 加速 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-gpu.md> | <https://developer.lazycat.cloud/advanced-gpu.html> |
| `multi-instance` | 多实例 | <https://gitee.com/lazycatcloud/lzc-developer-doc/raw/master/docs/advanced-multi-instance.md> | <https://developer.lazycat.cloud/advanced-multi-instance.html> |

## 7. 比对、裁决与交付记录

1. 按本次需求选择核心页与专题页，检查 `calibration.json` 的 `result`；只有 `success` 才表示所有所选页面均取得在线官方正文。
2. 先按目标 lzcos / CLI 版本核对能力门槛，再把官方原文与本地说明、拟生成配置逐项比对。重点检查字段归属、权限、路径、模板、运行时与审核要求，不凭记忆补字段。
3. 本地快照与官方原文冲突时，以官方原文为准；指出本地文件与冲突位置，不静默忽略。
4. 交付时至少记录：目标版本、所读页面、实际来源、官方 commit（如已核实）或每篇原文 SHA-256、发现的差异及离线状态。

建议交付格式：

```text
规范校准：目标 lzcos=<版本>，lzc-cli=<版本>
来源：官方文档源/文档站；official commit=<值或“未固定”>；原文 SHA-256 见 calibration.json
已核对：<页面列表>
结果：<成功/未完成，不得把离线写成成功>；差异：<无或逐项列出>
```
