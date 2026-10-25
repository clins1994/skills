# Contributing

Thanks for wanting to help. These skills are small on purpose, so most contributions are small too: a sharper rule, a missing case, or support for another tool.

## Using AI

You can use AI to help you contribute. Two rules, adapted from [Anthony Fu's contribution guide](https://github.com/antfu/contribute):

1. **Never let an LLM speak for you.** Write issues, comments and PR descriptions in your own words. Short and plain beats long and polished.
2. **Never let an LLM think for you.** Understand every line you send. Tell us what *you* think, not what a model said.

A pull request that looks fully generated and unreviewed may be closed without discussion.

## Discuss first

For a new skill, or a big change to one, open an issue first. Say what problem it solves and how you would do it. For a typo or a small fix, send the pull request directly.

## How a skill is laid out

```
skills/<name>/
  SKILL.md          # frontmatter (name, description) + the instructions
  references/       # longer detail the agent reads only when it needs it
  scripts/          # helpers the skill runs, with their tests
```

- Name the folder and `name:` without a prefix (`skills/linear/`, `name: linear`). The plugin adds `clins:`.
- Keep `SKILL.md` short. Move long detail into `references/`.
- Keep skills general: no org names, private repos, channel IDs or internal data. Use placeholders such as `<owner>/<repo>` and `ENG-123`.
- Each skill reads the target repo's own rules (`AGENTS.md`, `CLAUDE.md`, templates) instead of hard-coding team conventions.
- Text belongs to `post`. A platform skill (`github`, `linear`) owns only the syntax, commands and updates for its platform. `create-pr` owns the pull request workflow and works with any host skill.
- Every skill is listed in the `README.md` table, with its name linked to its `SKILL.md`.

See [`AGENTS.md`](AGENTS.md) for the short version that agents read.

## Before you submit

- [ ] `claude plugin validate .` passes.
- [ ] `python3 skills/post/scripts/test_check_post.py` passes, if you touched `post`. Add a test for a new check.
- [ ] `check_post.py --fix` has a fix and a test, if the change alters how a post looks. See "Adding a fix" in [`migrate-posts`](skills/migrate-posts/SKILL.md).
- [ ] `version` in `.claude-plugin/plugin.json` is bumped: minor for a new skill, patch for a fix. Without a bump, installed plugins do not update.
- [ ] The `README.md` table matches the skills.
- [ ] You tried the skill once on a real task, and you say in the PR what you tried.

## Commits and pull requests

- Small commits, one change each, with the skill as the prefix: `linear: reply in threads with parentId`. Use `README:`, `plugin:` or no prefix for repo-wide changes.
- Pull requests are merged with a merge commit, so keep your commits clean. No need to squash them yourself.
- Link the issue: `closes #123`.

## Ideas

Good places to start. Open an issue to claim one, or to suggest your own.

**Other ways in**

- **`linear` without the MCP server.** The skill only uses the Linear MCP tools. Add a path for the [Linear GraphQL API](https://linear.app/developers/graphql) with a personal API key (`curl` or a small script): create and update issues, comments, replies, and description patches that keep issue tags.
- **`github` with the official MCP server.** The skill only uses the `gh` CLI. Add a path for the [GitHub MCP server](https://github.com/github/github-mcp-server) for agents that have it and no `gh`. Image upload with `gh --attach` has no MCP equivalent yet, so say what falls back.

**New host and tracker skills**

- **`gitlab`**, a host skill for `create-pr` built on `glab`: merge request bodies with uploads, comments, thread replies and issues.
- **`jira`**, a tracker skill next to `linear`: issues with fields, safe description updates, comments and replies, through the Jira REST API or an MCP server. Its collapsed block is the `{expand}` macro, or an expand node in the new editor.
- **Other trackers** (GitHub Projects, and more), as platform skills that use `post` for the text.

**`post`**

- **Try the skills in your language** and report what reads badly or fails the check. The README lists the languages tested so far.
- **More built-in languages** in `check_post.py` (block title and "original" label), with tests.
- **Rules for another language** in `check_post.py`, like the japanese spacing rule (`TIGHT_MIX`) or a language written without spaces (`NO_SPACES`).
- **GitLab and Jira block syntax** in the check script, once a `gitlab` or `jira` skill exists.

**Demo**

- An example for each new skill or path on the demo page.

## License

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE).
