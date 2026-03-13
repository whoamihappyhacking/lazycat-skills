.PHONY: all help install-skills uninstall-skills list-skills build-skills

SHELL = /usr/bin/env bash -o pipefail
.SHELLFLAGS = -ec

SKILLS_DIR := $(CURDIR)/skills

# 默认安装目录为 ~/.claude/skills，可通过环境变量覆盖
# 示例：SKILLS_INSTALL_DIR=~/.codex/skills make install-skills
SKILLS_INSTALL_DIR ?= $(HOME)/.claude/skills

HELP_FUN = \
	%help; while(<>){push@{$$help{$$2//'options'}},[$$1,$$3] \
	if/^([\w-_]+)\s*:.*\#\#(?:@(\w+))?\s(.*)$$/}; \
	print"\033[1m$$_:\033[0m\n", map"  \033[36m$$_->[0]\033[0m".(" "x(20-length($$_->[0])))."$$_->[1]\n",\
	@{$$help{$$_}},"\n" for keys %help; \

all: help

.PHONY: help
help: ##@通用 显示帮助信息
	@echo -e "用法: make \033[36m<目标>\033[0m\n"
	@echo -e "安装目录: \033[33m$(SKILLS_INSTALL_DIR)\033[0m"
	@echo -e "覆盖示例: \033[36mSKILLS_INSTALL_DIR=~/.codex/skills make install-skills\033[0m\n"
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)
	@echo -e "\033[1m推荐安装方式（自动更新）：\033[0m"
	@echo -e "  通过插件市场安装，支持自动同步最新版本："
	@echo -e "    \033[36m/plugin marketplace add whoamihappyhacking/lazycat-skills\033[0m"
	@echo -e "    \033[36m/plugin install lazycat-lpk-builder@whoamihappyhacking/lazycat-skills\033[0m"

.PHONY: install-skills
install-skills: ##@技能管理 将所有技能安装到本地目录（符号链接方式，支持 SKILLS_INSTALL_DIR 变量）
	@echo "正在安装技能到 $(SKILLS_INSTALL_DIR) ..."
	@mkdir -p $(SKILLS_INSTALL_DIR)
	@for skill in $(SKILLS_DIR)/*/; do \
		if [ -f "$$skill/SKILL.md" ]; then \
			skill_name=$$(basename $$skill); \
			if [ -L "$(SKILLS_INSTALL_DIR)/$$skill_name" ]; then \
				echo "  ✓ $$skill_name（已安装，跳过）"; \
			else \
				ln -s "$$skill" "$(SKILLS_INSTALL_DIR)/$$skill_name"; \
				echo "  + $$skill_name"; \
			fi; \
		fi; \
	done
	@echo "完成！技能已安装到 $(SKILLS_INSTALL_DIR)"

.PHONY: uninstall-skills
uninstall-skills: ##@技能管理 从本地目录移除所有技能符号链接
	@echo "正在从 $(SKILLS_INSTALL_DIR) 卸载技能 ..."
	@for skill in $(SKILLS_DIR)/*/; do \
		if [ -f "$$skill/SKILL.md" ]; then \
			skill_name=$$(basename $$skill); \
			if [ -L "$(SKILLS_INSTALL_DIR)/$$skill_name" ]; then \
				rm "$(SKILLS_INSTALL_DIR)/$$skill_name"; \
				echo "  - $$skill_name"; \
			fi; \
		fi; \
	done
	@echo "完成！技能已卸载。"

.PHONY: list-skills
list-skills: ##@技能管理 列出仓库中所有技能及安装状态
	@echo "仓库中可用的技能："
	@for skill in $(SKILLS_DIR)/*/; do \
		if [ -f "$$skill/SKILL.md" ]; then \
			skill_name=$$(basename $$skill); \
			if [ -L "$(SKILLS_INSTALL_DIR)/$$skill_name" ]; then \
				echo "  ✓ $$skill_name（已安装 → $(SKILLS_INSTALL_DIR))"; \
			else \
				echo "  ○ $$skill_name"; \
			fi; \
		fi; \
	done

.PHONY: build-skills
build-skills: ##@打包 将所有技能目录打包为 .skill zip 文件（供 npx skills 工具使用）
	@echo "正在打包技能为 .skill 文件 ..."
	@command -v zip >/dev/null 2>&1 || { echo "错误：未找到 zip 命令，请先安装。"; exit 1; }
	@for skill in $(SKILLS_DIR)/*/; do \
		if [ -f "$$skill/SKILL.md" ]; then \
			skill_name=$$(basename $$skill); \
			output="$(SKILLS_DIR)/$$skill_name.skill"; \
			rm -f "$$output"; \
			(cd "$$skill" && zip -r "$$output" . -x "*.DS_Store" -x "__MACOSX/*" -x ".git/*" -q); \
			echo "  ✓ $$skill_name.skill"; \
		fi; \
	done
	@echo "完成！.skill 文件已生成到 $(SKILLS_DIR)/"
