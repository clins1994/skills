# Caio's Skills

My [agent skills](https://agentskills.io/home) for coding agents (Claude Code, Codex, Cursor, OpenCode and [others](https://github.com/vercel-labs/skills#supported-agents)). They are small and repository-agnostic: install once, then use them in any repo. Each skill reads the repo's own rules (`AGENTS.md`, `CLAUDE.md`, templates) before it writes anything.

See what each skill writes in the [demo](https://clins.me/skills). Read why I made them in the [blog post](https://clins.me/2026/writing-for-people-and-agents).

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
| [post](skills/post/SKILL.md) | The writing format: a short lead for people, then the full text in a collapsed "More details" block that shows its read time. Writes in your languages: a lead language and any others under it. Includes a check script. |
| [create-pr](skills/create-pr/SKILL.md) | Creates or updates a reviewable pull request: exact range, checks, title, before/after images right under the lead, body from `post`. Works with any host. Never merges. |
| [fork-review](skills/fork-review/SKILL.md) | Opens a PR on your fork first, runs your review steps there (an agent loop such as `/clins:address-reviews`, a person, or a wait), then opens the same PR upstream and keeps both bodies in sync. Includes an optional Claude Code hook. |
| [address-reviews](skills/address-reviews/SKILL.md) | Drives an open PR to done in a bounded loop: fixes failing CI and review comments from bots and people, replies in each thread with `post`, asks bots for a new review when they need it, and waits for it. Parks what needs you. Never merges. |
| [greptile](skills/greptile/SKILL.md) | Works with Greptile reviews: finds the score and open comments, tells whether Greptile reviews each push, asks for a review and waits for it, and runs a local review with the Greptile CLI. `address-reviews` uses it. |
| [raycast-publish](skills/raycast-publish/SKILL.md) | Publishes a Raycast extension through a PR on `raycast/extensions`: syncs your fork, pulls contributions, prepares the extension against Raycast's live guidelines, writes the full description from Raycast's template before publishing, gets Greptile to 5/5 on the draft with `address-reviews`, then marks it ready on your OK. Never merges. |
| [github](skills/github/SKILL.md) | Posts to GitHub with `gh`: PR bodies with images uploaded by `gh --attach` and a render check, PR comments, replies in review threads, and issues. |
| [linear](skills/linear/SKILL.md) | Posts to Linear through its MCP server: new issues with fields, safe description updates with `patch`, comments and thread replies. |
| [slack](skills/slack/SKILL.md) | Posts to Slack through its MCP server: the leads in the channel message and the details in one thread reply, since Slack has no collapsed block. Shares images and videos through the connector's upload. Says what Slack and the connector cannot do. |
| [times](skills/times/SKILL.md) | Keeps your updates in one place of your own, your "times", set with one saved line. Writes the full post there, and on request a short pointer in a team channel that links to it. Works with any platform skill. |
| [migrate-posts](skills/migrate-posts/SKILL.md) | Brings your open PRs, GitHub issues, comments and Linear issues up to date after the skills change. Updates the skills, shows a dry run for every signed-in account, then changes only the format, with a backup per post. A second run does nothing. |

How they fit together:

```
create-pr ──► post (text) ──► github (commands)
    └──────► fork-review (fork first, then upstream)
address-reviews ──► greptile (reviewer) · post (replies) · github (commands)
raycast-publish ──► post (text) · github (commands) · address-reviews (review on the draft)
linear ─────► post (text)
slack ──────► post (text)
times ──────► post (text) · slack (or another platform skill)
```

`post` owns the text. `github`, `linear` and `slack` own the platform: syntax, commands and updates. `create-pr` owns the pull request workflow and works with any host skill, so a `gitlab` skill can sit next to `github` later. A `jira` skill can sit next to `linear` the same way. `fork-review` owns the route when a PR goes to your fork before upstream. `address-reviews` owns the fix loop on an open PR, and each review bot gets its own skill (`greptile` today), so a `coderabbit` skill can sit next to it later. `times` owns where your updates go, and works with any platform skill. `raycast-publish` owns the route to the Raycast Store, and reads Raycast's own docs and CLI on every run instead of copying them.

## Fork review

For repos you don't own, `fork-review` can open each PR on your fork first. Whatever review you choose runs there, and only a clean branch goes upstream. Set it with one line in your global instructions file, and add lines for single repos:

```
clins:fork-review: mode ask; review /clins:address-reviews
clins:fork-review <owner>/<repo>: mode fork; review /clins:address-reviews, then @alice
```

`mode` is `ask` (ask each time), `fork` (always) or `origin` (never). `review` lists the steps: a command for the agent to run, `@someone` to request a review from, or `wait`.

The Claude Code plugin also ships a hook that asks before, or blocks, a `gh pr create` that skips the fork, depending on `mode`. It does nothing until you add the line. For a repo that already reviews every PR upstream (for example `raycast/extensions`, which runs Greptile), add `clins:fork-review <owner>/<repo>: mode origin`. Agents that install with `npx skills` (Codex, Cursor, others) get the skill only, with no hook.

## Languages

The first time you run `post`, it asks, in the language you write to it in, which language your posts lead with (that language by default) and whether to add others. It saves one line to your agent's global instructions file:

```
clins:post languages: lead english; also japanese
```

If you post from more than one account, for example a work and a personal GitHub account, each one can have its own languages:

```
clins:post languages github:alice-personal: lead english
clins:post accounts: github:alice-work, github:alice-personal
```

`post` asks about each account the first time it sees it, and saves the answer. The line without an account stays the default.

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
- [natural-japanese](https://github.com/coji/natural-japanese) by coji
- [i-have-adhd](https://github.com/ayghri/i-have-adhd) by ayghri
- [unslop](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop) from Cursor's `pstack`

`create-pr` takes ideas from [antfu-create-pr](https://github.com/antfu/skills/tree/main/skills/antfu-create-pr) by Anthony Fu.

## License

[MIT](LICENSE)
