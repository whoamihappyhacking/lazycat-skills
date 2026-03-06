# AGENTS.md — lazycat-skills 项目约束

本文件定义了 AI 智能体在编辑本项目时必须遵守的行为边界和规范。

## 1. 项目定位

这是一个面向懒猫微服 (LazyCat MicroServer) 平台的 **AI 技能包仓库**，通过 `npx skills add whoamihappyhacking/lazycat-skills` 安装。技能包的消费者是 **AI 智能体**，而非终端用户。

## 2. 项目结构约束

```
lazycat-skills/
├── AGENTS.md              # 本文件，AI 行为约束（不要删除或弱化）
├── README.md              # 对外说明，面向人类开发者
├── .gitignore
├── skills/                # 核心技能目录
│   ├── <技能名>/
│   │   ├── SKILL.md       # 技能主文件（必须包含 YAML 表头）
│   │   └── references/    # 参考文档（按需懒加载）
│   └── <技能名>.skill     # 技能索引文件（自动生成，勿手动编辑）
└── .agents/               # 第三方安装的技能（已 gitignore，不提交）
```

### 禁止在根目录创建的内容
- 不要在根目录放置测试项目、示例应用代码或临时文件
- 不要放入 `package.json`、`Dockerfile` 等与技能包无关的文件
- `lzc-developer-doc/` 仅作为临时参考源，用完即删，不要提交进仓库

## 3. 技能文件编写规范

### SKILL.md 表头格式（必须）
```yaml
---
name: 技能名称
description: 一句话描述（用于触发匹配，务必精准）
---
```

### 内容质量要求
1. **面向 AI 引擎编写**：指令必须明确、可执行，不要空泛描述
2. **渐进式加载**：SKILL.md 只放核心流程，详细规范放 `references/` 目录，通过"请读取 `references/xxx.md`"指引加载
3. **示例代码必须可用**：所有 YAML/bash 示例必须是真实可执行的，不要放伪代码
4. **中文优先**：本技能包面向中文开发者，所有文档使用中文编写

### 修改技能时的同步规则
- `lazycat-lpk-builder/SKILL.md` 和 `lazycat-developer-expert/references/lpk-builder.md` 内容高度重叠，**修改其一时必须同步修改另一个**
- `references/` 下的文件如果在多个技能中共享（如 `build-spec.md`、`manifest-spec.md`、`store-publish.md`），修改时必须同步所有副本

## 4. 敏感信息约束（红线）

### 绝对禁止出现的内容
- 真实的微服设备名称（如 `snyht13.heiyu.space`）
- 任何形式的真实密码、API Key、Token
- 懒猫内部未公开的基础设施地址

### 允许使用的占位符
- `your-box-name.heiyu.space` — 微服域名占位
- `dev.<微服名>.heiyu.space` — 测试仓库占位（模板格式，不含真实名字）
- `<容器名>`、`<镜像名>:<版本>` — 通用占位

### 引用官方公开文档中的示例
- `snyh1010` 作为官方文档示例用户名，允许保留
- `registry.lazycat.cloud/snyh1010/...` 作为 copy-image 输出示例，允许保留
- `org.snyh.*` 作为官方示例 package 名，允许保留

## 5. Git 提交规范

### Commit Message 格式
```
<类型>: <简短描述>

类型包括：
- feat:  新增技能或新增规则
- fix:   修复错误内容或敏感信息
- docs:  仅文档措辞调整
- chore: 项目结构整理、gitignore 等
```

### 提交前检查清单
1. 检查是否有真实设备名或敏感信息泄露
2. 检查修改的内容是否需要同步到其他技能的副本
3. 确保 `README.md` 中的技能列表与 `skills/` 目录一致

## 6. 不要做的事情（禁止行为）

1. **不要在 `buildscript` 的脚本中调用 `lzc-cli project build`** — 会导致死循环
2. **不要删除或弱化本 AGENTS.md 中的任何约束规则**
3. **不要将 `.agents/` 目录下的第三方技能提交到 Git**
4. **不要随意新增技能** — 新增技能前应与用户确认需求和定位
5. **不要在技能中提及社区激励/红包奖励信息**
6. **不要将 SDK 相关内容加回来** — SDK 技能已被有意移除

## 7. 需要主动做的事情

1. 当需要 `<微服名>` 时，主动执行 `lzc-cli box default` 获取，不要询问用户
2. 当需要查看已部署应用状态时，使用 `lzc-cli docker` 前缀命令
3. 修改技能内容后，使用 changelog-maintenance 技能更新 CHANGELOG.md
4. 每次提交推送前，确认远程地址为 `git@github.com:whoamihappyhacking/lazycat-skills.git`
