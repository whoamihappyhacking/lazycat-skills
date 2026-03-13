# 🐱 Lazycat Skills (懒猫微服 AI 技能包)

这是一套专为 **懒猫微服 (LazyCat MicroServer)** 平台开发者打造的 AI 智能体技能包 (Agent Skills)。
通过安装本技能包，你可以让你的 AI 助手（如 Cursor、Windsurf、Cline等）瞬间变成懒猫平台的生态开发专家，帮你自动编写 `lzc-manifest.yml`、打包 LPK、处理路由以及进行微服认证开发。

## 📦 技能列表 (Available Skills)

| 技能名称 | 功能描述 |
|---|---|
| `lazycat-developer-expert` | 全场景总控入口，覆盖打包、路由、认证、上架等所有需求 |
| `lazycat-lpk-builder` | 将 Docker 镜像 / 源码打包为 `.lpk` 懒猫微服应用 |
| `lazycat-dynamic-deploy` | 动态部署参数（`lzc-deploy-params.yml`）与前端脚本注入 |
| `lazycat-advanced-routing` | 高级路由、多域名、TCP/UDP 四层转发、复杂反向代理 |
| `lazycat-auth-integration` | OIDC 单点登录、HTTP Header 身份识别、API Auth Token |

## 🚀 安装指南

### 方式一：npx skills（推荐）

```bash
# 在你的项目根目录下执行：
npx skills add whoamihappyhacking/lazycat-skills
```

安装完成后，你的 AI 将会自动发现最新的技能！试着对你的 AI 说："**帮我把当前的 Docker 项目打包成懒猫的 lpk 应用**"，它就会自动触发对应技能并调用懒猫打包标准。

### 方式二：插件市场（适合 Claude Code，自动更新）

```bash
# 1. 添加仓库为插件源
/plugin marketplace add whoamihappyhacking/lazycat-skills

# 2. 按需安装单个技能（推荐安装总控技能）
/plugin install lazycat-developer-expert@whoamihappyhacking/lazycat-skills
```

### 方式三：本地开发安装（适合贡献者）

克隆仓库后，通过符号链接安装，修改即时生效：

```bash
# 安装到 ~/.claude/skills/（可通过 SKILLS_INSTALL_DIR 覆盖目标目录）
make install-skills

# 查看安装状态
make list-skills

# 卸载
make uninstall-skills
```

## 💬 使用示例

安装完成后，直接用自然语言对你的 AI 助手描述需求：

- "帮我把当前的 Docker 项目打包成懒猫的 lpk 应用"
- "我需要配置一个带二级域名的路由，管理后台走 myadmin 子域名"
- "应用需要支持 OIDC 登录，帮我配置懒猫的单点登录"
- "安装应用时让用户填写数据库密码，怎么做？"

## 📂 项目结构规范

为了符合 Agent 渐进式加载（Progressive Disclosure）原则，本仓库采用标准结构：
```text
lazycat-skills/
├── Makefile                     # 本地安装 / 卸载 / 打包命令
├── skills/                      # 技能存放主目录
│   ├── lazycat-lpk-builder/
│   │   ├── SKILL.md             # AI 技能指令核心与触发词
│   │   └── references/          # 供 AI 读取的规范文档
│   └── ...
└── README.md
```

## 🤝 贡献指南

期待社区的 Pull Request，补充更多的开发者文档和自动化脚本！
