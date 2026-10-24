# Caio's Skills

My [agent skills](https://agentskills.io/home) for coding agents (Claude Code, Codex, Cursor, OpenCode and [others](https://github.com/vercel-labs/skills#supported-agents)). They are small and repository-agnostic: install once, then use them in any repo. Each skill reads the repo's own rules (`AGENTS.md`, `CLAUDE.md`, templates) before it writes anything.

See what each skill writes in the [demo](https://clins.me/skills).

Layout inspired by [antfu/skills](https://github.com/antfu/skills) and [mattpocock/skills](https://github.com/mattpocock/skills).

## Install

With the [skills CLI](https://github.com/vercel-labs/skills) (any agent):

```bash
npx skills add clins1994/skills                     # pick skills and agents
npx skills add clins1994/skills --skill='*' -g      # all skills, globally
npx skills add clins1994/skills --skill post -a claude-code
```

Update later with `npx skills update`.

As a Claude Code plugin (updates with `claude plugin update`):

```
/plugin marketplace add clins1994/skills
/plugin install clins@clins-skills
```

The plugin names each skill `clins:<skill>`, for example `/clins:post`. The skills CLI installs it as `post`.

## Skills

| Skill | What it does |
|-------|--------------|
| [post](skills/post/SKILL.md) | The writing format: a short lead for people, then the full text in a collapsed "More details" block. Writes in your languages: a lead language and any others under it. Includes a check script. |
| [create-pr](skills/create-pr/SKILL.md) | Creates or updates a reviewable pull request: exact range, checks, title, before/after images right under the lead, body from `post`. Works with any host. Never merges. |
| [github](skills/github/SKILL.md) | Posts to GitHub with `gh`: PR bodies with images uploaded by `gh --attach` and a render check, PR comments, replies in review threads, and issues. |
| [linear](skills/linear/SKILL.md) | Posts to Linear through its MCP server: new issues with fields, safe description updates with `patch`, comments and thread replies. |

How they fit together:

```
create-pr ──► post (text) ──► github (commands)
linear ─────► post (text)
```

`post` owns the text. `github` and `linear` own the platform: syntax, commands and updates. `create-pr` owns the pull request workflow and works with any host skill, so a `gitlab` skill can sit next to `github` later. A `jira` skill can sit next to `linear` the same way.

## Languages

The first time you run `post`, it asks, in the language you write to it in, which language your posts lead with (that language by default) and whether to add others. It saves one line to your agent's global instructions file:

```
clins:post languages: lead english; also japanese
```

After that, change languages for one post in plain words: "japanese as well", "only the lead", "swap them", "use only portuguese". To change the default, say so: "change my post languages to portuguese and japanese". A repo can set its own default in its `AGENTS.md` or `CLAUDE.md`.

### Tested languages

The skills work in any language, but only these have been used for real so far:

| Language | Used in | Checks in `check_post.py` |
|---|---|---|
| english | pull requests, issues, Linear issues, comments | sentence length (words), english style rules |
| japanese | pull requests, a Linear issue | sentence length (characters), no space between full-width and half-width text |
| portuguese | one pull request | sentence length (words) |
| chinese | one pull request | sentence length (characters) |
| hindi | one pull request | sentence length (words), sentences end at `।` |

The first run (the language questions) has only been tried in english.

If you write in another language, or one of these looks wrong, please open an issue or a pull request: a post that reads badly, a check that fails on good text, or a block title or "original" label your language needs. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing

Ideas and pull requests are welcome. Some starting points: a Linear API path for `linear`, a GitHub MCP path for `github`, a `gitlab` host skill for `create-pr`, and a `jira` tracker skill next to `linear`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

`post` builds on these public skills, and works better with them installed:

- [simple-english](https://github.com/AminBlg/SimpleEnglish) by AminBlg
- [i-have-adhd](https://github.com/ayghri/i-have-adhd) by ayghri
- [unslop](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop) from Cursor's `pstack`

`create-pr` takes ideas from [antfu-create-pr](https://github.com/antfu/skills/tree/main/skills/antfu-create-pr) by Anthony Fu.

## License

[MIT](LICENSE)
