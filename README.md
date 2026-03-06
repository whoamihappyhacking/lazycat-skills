# 🐱 Lazycat Skills (懒猫微服 AI 技能包)

这是一套专为 **懒猫微服 (LazyCat MicroServer)** 平台开发者打造的 AI 智能体技能包 (Agent Skills)。
通过安装本技能包，你可以让你的 AI 助手（如 Cursor、Windsurf、Cline等）瞬间变成懒猫平台的生态开发专家，帮你自动编写 `lzc-manifest.yml`、打包 LPK、处理路由以及进行微服认证开发。

## 📦 技能列表 (Available Skills)

目前包含以下核心技能：
- `lazycat-developer-expert`: 懒猫微服全能开发者专家。
- `lazycat-lpk-builder`: 专精将 Docker/源码转化为 `.lpk` 懒猫微服应用的打包专家。
- `lazycat-dynamic-deploy`: 处理懒猫动态部署的能手。
- `lazycat-advanced-routing`: 设置懒猫高级路由规则（如二级域名、内网通信）。
- `lazycat-auth-integration`: 处理懒猫微服 API 获取、OIDC 登录认证。
- `lazycat-sdk-dev`: 辅助由于懒猫微服 SDK 对接的代码开发。

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
├── skills/                      # 技能存放主目录
│   ├── lazycat-lpk-builder/
│   │   ├── SKILL.md             # AI 技能指令核心与触发词
│   │   └── references/          # 供 AI 读取的规范文档
│   └── ...
└── README.md
```

## 🤝 贡献指南
期待社区的 Pull Request，补充更多的开发者文档和自动化脚本！
