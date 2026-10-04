# 🐱 Lazycat Skills (懒猫微服 AI 技能包)

这是一套专为 **懒猫微服 (LazyCat MicroServer)** 平台开发者打造的 AI 智能体技能包 (Agent Skills)。

> [!IMPORTANT]
> **分支与版本说明：**
> - **`main` / `v2` 分支 (当前)**: 支持最新的 **LPK V2 (v1.5.0+)** 规范（元数据与运行结构分离，支持 `package.yml` 和 `permissions` 声明）。
> - **`v1` 分支**: 包含旧版的 LPK V1 规范。

通过安装本技能包，你可以让你的 AI 助手（如 Cursor、Windsurf、Cline等）瞬间变成懒猫平台的生态开发专家，帮你自动编写 `package.yml`、`lzc-manifest.yml`、打包 LPK、处理高级路由以及进行微服认证开发。

## 🔄 规范实时校准（重要）

懒猫官方开发者文档会**不定期更新**，而本技能包内的规范文档是**某一时刻的快照**，会落后。

因此本技能包内置了**打包前强制校准机制**：任何打包/构建动作（`lzc-cli project build` / `deploy` / `release`）之前，AI 会先读取官方最新规范原文，与本地快照比对，**冲突时一律以官方为准**，并向你声明本次校准来源与差异。

校准来源（见各技能 `references/spec-sync.md`）：

| 优先级 | 来源 | 地址 |
| --- | --- | --- |
| 1 | 官方文档**源仓库**（markdown 源，机器可读） | <https://gitee.com/lazycatcloud/lzc-developer-doc> |
| 2 | 官方开发者**文档站**（渲染版） | <https://developer.lazycat.cloud/> |

所以即使本仓库更新不及时，你得到的配置也会紧跟官方最新规范。

## 📦 技能列表 (Available Skills)

目前包含以下核心技能：
- `lazycat-developer-expert`: 懒猫微服全能开发者专家（入口级总控技能）。
- `lazycat-lpk-builder`: 专精将 Docker/源码转化为 `.lpk` 懒猫微服应用的打包专家。
- `lazycat-dynamic-deploy`: 处理懒猫动态部署的能手。
- `lazycat-advanced-routing`: 设置懒猫高级路由规则（如二级域名、内网通信）。
- `lazycat-auth-integration`: 处理懒猫微服 API 获取、OIDC 登录认证。
- `lazycat-aipod-developer`: 懒猫 AI 算力舱（AI Pod）应用开发与打包规范。
- `lazycat-android-webview-bridge`: Android WebView 宿主桥接 API（如 `lzc_toast.setSnackBarEnabled()`）。

## 🚀 安装指南

我们推荐使用 `npx skills` 工具直接安装到你的 AI 助手工作区中内：

```bash
# 在你的项目根目录下执行：
npx skills add whoamihappyhacking/lazycat-skills
```

安装完成后，你的 AI 将会自动发现最新的技能！试着对你的 AI 说：“**帮我把当前的 Docker 项目打包成懒猫的 lpk 应用**”，它就会自动触发对应技能并调用懒猫打包标准。

## 📂 项目结构规范

为了符合 Agent 渐进式加载（Progressive Disclosure）原则，本仓库采用标准结构：
```text
lazycat-skills/
├── scripts/
│   └── build-skills.mjs         # 由 skills/<name>/ 生成 skills/<name>.skill 打包件
├── skills/                      # 技能存放主目录
│   ├── lazycat-lpk-builder/
│   │   ├── SKILL.md             # AI 技能指令核心与触发词
│   │   ├── references/          # 供 AI 读取的规范文档
│   │   │   └── spec-sync.md     # 打包前强制校准流程与官方文档链接
│   │   └── ...
│   └── <技能名>.skill           # 打包件（由脚本生成，勿手动编辑）
└── README.md
```

### 维护打包件

`skills/<技能名>.skill` 是 ZIP 打包件，由脚本从 `skills/<技能名>/` 生成。**修改技能内容后必须重新生成**，否则打包件会与源文件不一致：

```bash
node scripts/build-skills.mjs          # 生成全部
node scripts/build-skills.mjs --check  # 仅校验，不一致则非零退出（可用于 CI）
```

## 🤝 贡献指南
期待社区的 Pull Request，补充更多的开发者文档和自动化脚本！
