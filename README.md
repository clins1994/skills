# Caio's Skills

My [agent skills](https://agentskills.io/home) for coding agents (Claude Code, Codex, Cursor, opencode), packaged as one Claude Code plugin named `clins`. They are repository-agnostic: install once and run them in any repo. Each skill reads the target repo's own rules (`AGENTS.md`, `CLAUDE.md`) for team conventions.

Layout inspired by [antfu/skills](https://github.com/antfu/skills) and [mattpocock/skills](https://github.com/mattpocock/skills).

## Install

### Claude Code (plugin)

```
/plugin marketplace add clins1994/skills
/plugin install clins@clins-skills
```

The skills are named `clins:<skill>`, for example `/clins:post`. To get new and changed skills later:

```bash
claude plugin marketplace update clins-skills
claude plugin update clins@clins-skills
```

### Other agents (`npx skills`)

```bash
npx skills@latest add clins1994/skills
```

Pick the skills and which agents to install them on (project or global scope). `npx skills` installs each skill under its folder name without the `clins:` prefix (for example `post`).

Every skill preflights its own dependencies (a CLI, an MCP connection) and fails early with instructions if something is missing.

## Skills

- **[clins:post](./skills/post/SKILL.md)**: engineering posts (PR descriptions and comments, Linear issues and comments) as a short lead for humans plus a collapsed "🇬🇧 More details (for agents)" block. English by default. `--lang ja` (or another language) adds a translated lead and a second collapsed block. Includes a check script.
- **[clins:pr](./skills/pr/SKILL.md)**: opens or updates a GitHub PR with before/after images right under the lead, uploaded with `gh --attach` (nothing committed). Covers the title, capture on web and Android, and a render check. Text comes from `clins:post`, with the same `--lang` option.
