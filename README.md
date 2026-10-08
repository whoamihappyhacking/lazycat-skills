# 🐱 Lazycat Skills (懒猫微服 AI 技能包)

这是一套专为 **懒猫微服 (LazyCat MicroServer)** 平台开发者打造的 AI 智能体技能包 (Agent Skills)。

> [!IMPORTANT]
> **分支与版本说明：**
> - **`main` / `v2` 分支 (当前)**: 面向 **LPK V2**（lzcos >=1.5.0、lzc-cli >=2.0.0），元数据与运行结构分离。新能力另有最低系统版本，不能仅凭 V2 就认为设备全部支持。
> - **`v1` 分支**: 包含旧版的 LPK V1 规范。

通过安装本技能包，你可以让你的 AI 助手（如 Cursor、Windsurf、Cline等）瞬间变成懒猫平台的生态开发专家，帮你自动编写 `package.yml`、`lzc-manifest.yml`、打包 LPK、处理高级路由以及进行微服认证开发。

## 🔄 规范实时校准（重要）

懒猫官方开发者文档会**不定期更新**，而本技能包内的规范文档是**某一时刻的快照**，会落后。

六个涉及平台配置的技能（除 Android WebView 桥接）分别携带**校准流程与独立工具**。写/改配置及 build/deploy/release 前，AI 应先确认目标系统/CLI 版本，读取 `references/spec-sync.md`，获取官方原文并比对快照，声明实际来源、原文摘要和差异。下载工具会拒绝 HTTP 错误、空内容及冒充 Markdown 的 HTML；无法联网时必须明确声明快照降级。

校准来源：

| 优先级 | 来源 | 地址 |
| --- | --- | --- |
| 1 | 官方文档**源仓库**（markdown 源，机器可读） | <https://gitee.com/lazycatcloud/lzc-developer-doc> |
| 2 | 官方开发者**文档站**（渲染版） | <https://developer.lazycat.cloud/> |

校准降低过期风险，不保证每个 Agent 都会遵从指令，也不等于真实设备测试。已知坏示例仍必须维护；官方页冲突需核实目标实现，不能用“官方为准”掩盖冲突。

本轮通用文档核对日期 **2026-10-08**，源仓库基线 `780d7206ce2298ee0a225e0221a993c4723d8e07`；AI Pod 额外读取[独立应用专题](https://developer.lazycat.cloud/aipod/package/spec.html)。版本、权限、资源与上架细节按需加载，而不是把整站一次塞入上下文。

## 📦 技能列表 (Available Skills)

目前包含以下核心技能：
- `lazycat-developer-expert`: 懒猫微服全能开发者专家（入口级总控技能）。
- `lazycat-lpk-builder`: 专精将 Docker/源码转化为 `.lpk` 懒猫微服应用的打包专家。
- `lazycat-dynamic-deploy`: 处理懒猫动态部署的能手。
- `lazycat-advanced-routing`: HTTP/域名前缀分流、Host、TCP/UDP 四层转发与安全边界。
- `lazycat-auth-integration`: OIDC、可信身份 Header、API Token、用户委托与应用间访问。
- `lazycat-aipod-developer`: AI Pod resource、设备型号 compose、浏览器插件与 startup gate；专题与通用资源规范差异须按目标实现核验。
- `lazycat-android-webview-bridge`: Android WebView 宿主桥接 API（如 `lzc_toast.setSnackBarEnabled()`）。

## 🚀 安装指南

推荐使用 `npx skills` 安装到 AI 助手工作区：

```bash
# 在你的项目根目录下执行：
npx skills add whoamihappyhacking/lazycat-skills
```

安装后，支持 Agent Skills 的 AI 助手可发现已安装技能；仓库后续更新仍需重新安装/更新本地副本。试着对你的 AI 说：“**帮我把当前的 Docker 项目打包成懒猫的 lpk 应用**”，它就会自动触发对应技能并调用懒猫打包标准。

## 📂 项目结构规范

为了符合 Agent 渐进式加载（Progressive Disclosure）原则，本仓库采用标准结构：
```text
lazycat-skills/
├── scripts/
│   ├── build-skills.mjs         # 由 skills/<name>/ 生成 skills/<name>.skill 打包件
│   ├── check-repo.py            # 标准库静态筛选，不冒充完整 YAML 校验
│   ├── requirements-check.txt   # 测试中的严格 YAML 与表头检查依赖
│   └── tests/                  # 隔离回归测试
├── skills/                      # 技能存放主目录
│   ├── lazycat-lpk-builder/
│   │   ├── SKILL.md             # AI 技能指令核心与触发词
│   │   ├── references/          # 按需加载规范摘要与校准流程
│   │   ├── scripts/             # 独立安装可用的规范抓取工具
│   │   └── ...
│   └── <技能名>.skill           # 打包件（由脚本生成，勿手动编辑）
└── README.md
```

### 维护打包件

`skills/<技能名>.skill` 是 ZIP 打包件，由脚本从 `skills/<技能名>/` 生成。**修改技能内容后必须重新生成**，否则打包件会与源文件不一致：

```bash
python3 -m pip install -r scripts/requirements-check.txt
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
node scripts/build-skills.mjs          # 生成全部
python3 scripts/check-repo.py          # 结构、共享副本、引用、安全和分发件
node scripts/build-skills.mjs --check  # 仅校验，不一致则非零退出
```

维护要求 Python >=3.10、Node >=20；CI 使用 Python 3.11。依赖安装后，回归测试在隔离本地目录/HTTP fixture 中运行，不访问真实设备。严格 YAML 检查拒绝重复键；Go template 与 `#@build` 源片段明确排除，必须另外用真实构建/部署渲染验证，不能把静态筛选称为全量运行验证。

完整的本地构建示例见 [`skills/lazycat-developer-expert/examples/static-site/`](skills/lazycat-developer-expert/examples/static-site/README.md)，迁移与本轮变更见 [`CHANGELOG.md`](CHANGELOG.md)。

## 🤝 贡献指南
期待社区的 Pull Request，补充更多的开发者文档和自动化脚本！
