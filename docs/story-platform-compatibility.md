# Story: Multi-Platform Compatibility & Open Source Best Practices

**Status:** Backlog
**Priority:** Medium
**Reference:** [inference-sh/skills](https://github.com/inference-sh/skills) as benchmark

## Background

After publishing `consistent-portrait-set` to GitHub and Hermes Skills Hub, we found:

1. **Skills.sh** — 通过 `npx skills add` 触发遥测后等待索引中，当前页面 404
2. **Hermes CLI** — 通过 `hermes skills tap add` 可搜可装
3. **Claude Code / Cursor / 其他 agent 平台** — 完全不支持

分析了 [inference-sh/skills](https://github.com/inference-sh/skills)（376 stars）的做法后，发现以下值得学习的点。

## 可学之处

### 1. 多平台安装兼容

inference-sh 支持三种安装方式：

```bash
# Claude Code plugin
/plugin install inference-sh

# npx skills (Vercel 生态)
npx skills add inference-sh/skills

# 手动复制
cp -r tools/* ~/.claude/skills/
```

我们目前只有：
- `hermes skills tap add` + `hermes skills install`（Hermes 专属）
- `npx skills add`（已做，等索引）

**Action:** 加 `.claude-plugin/plugin.json`，让 Claude Code 用户也能用。README 里补充所有平台的安装方式。

### 2. CONTRIBUTING.md

inference-sh 有完整的贡献指南：
- SKILL.md 格式要求
- 目录规范
- 测试要求
- 如何添加 Related Skills

**Action:** 写 CONTRIBUTING.md，为社区贡献做准备。

### 3. 分类目录结构

inference-sh 按功能分大类：
```
tools/
├── image/       # 图片相关（9 个 skill）
├── video/       # 视频
├── audio/       # 音频
├── llm/         # 语言模型
└── social/      # 社交媒体
```

我们目前只有一个 skill，暂不需要。但如果后续扩展（daily-news-briefing 等），应该按类似方式组织。

### 4. 跨 Skill 互引

每个 skill 底部有 "Related Skills" 区域，互相链接。

**Action:** 后续有多个 skill 时加互引。

### 5. allowed-tools 声明

inference-sh 在 SKILL.md frontmatter 里声明 `allowed-tools`，明确告诉 agent 需要哪些工具权限（如 Bash 命令）。

我们用 `requires_toolsets`，思路类似。无需改动。

### 6. 公开路线图 (TODO.md)

inference-sh 有公开的 TODO.md，让用户知道未来方向。

**Action:** 可选，加 TODO.md 或 ROADMAP.md。

## Deliverables

- [ ] `.claude-plugin/plugin.json` — Claude Code plugin 配置
- [ ] `CONTRIBUTING.md` — 贡献指南
- [ ] README 更新 — 多平台安装说明（Hermes、npx skills、Claude Code、手动）
- [ ] TODO.md 或 ROADMAP.md — 公开路线图（可选）
- [ ] 确认 Skills.sh 收录状态
- [ ] 验证 Claude Code 安装可用

## Notes

- 核心目标是让 skill 能被更多 agent 平台发现和使用，不只局限于 Hermes
- agentskills.io 开放标准理论上兼容所有遵循该标准的 agent
- 实际兼容性取决于各平台的 skill 加载机制
