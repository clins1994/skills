---
name: migrate-posts
description: Bring your open posts up to date after the clins skills change - pull request bodies, GitHub issues and Linear issues written with clins:post. Updates the installed skills, finds your open posts on every GitHub account you are signed in to and in Linear, and shows a dry run of what each one needs. Then applies only the format fixes that check_post.py --fix makes, one post at a time, with a backup, and leaves the content as it is. Remembers the version it last ran for each account, so a second run does nothing. Use after the skills change, or when asked to migrate, refresh, restyle or update open posts, PRs or issues.
user-invocable: true
argument-hint: "[no dry run] [check again] [github | linear] [account]"
---

# /clins:migrate-posts — Bring open posts up to date

The clins skills change the look of a post from time to time: a new block title, a read time, a new rule. This skill applies those changes to the posts that are still open, the way a database migration applies a schema change to the rows that already exist. It changes the format, never the content.

The changes are code, not instructions: `check_post.py --fix` from [`clins:post`](../post/SKILL.md) makes each format change by itself, and only on a post that has the old format. **A post changes only where `--fix` changes it.** You never edit a post by hand here.

## Rules

- Write only what `--fix` returned. Never rewrite, shorten, translate again or "improve" a post. When the check still reports an error after `--fix`, report it and leave the text as it is.
- Only posts that the account wrote, and that end with the clins footer: the `🤖 Generated with Claude Code · ... · clins:<skill>` block, or the one-line `🤖 Generated with [Claude Code](...) using [clins:...]` from before 0.9.0.
- Never touch text below the footer, other people's text, titles, labels, state, reviewers or draft state.
- Fetch each post again right before you write it. If it changed since you planned it, plan it again.
- Back up each body before you write it.
- Never post a comment, and never ask a review bot for a review. Editing a body starts no review.

## Steps

### 1. Update the skills

For a Claude Code plugin install, find the marketplace with `claude plugin list`, then:

```bash
claude plugin marketplace update <marketplace>
claude plugin update clins@<marketplace>
```

The new version lands in `~/.claude/plugins/cache/<marketplace>/clins/<version>/`. Claude Code loads it after a restart, so for this run read the new files from that folder: this `SKILL.md` (if it changed, follow the new one) and `skills/post/scripts/check_post.py`. For another install (`npx skills`, a clone), update it the way it was installed, and use its folder.

The **current version** is `version` in the new `.claude-plugin/plugin.json`.

### 2. Find the accounts

- **GitHub:** every login on every host in `gh auth status --json hosts`. Run each command as that account with `GH_HOST=<host> GH_TOKEN=$(gh auth token -h <host> -u <login>)`. Never `gh auth switch`: it changes the active account for the user's other work.
- **Linear:** the workspace that the Linear MCP server is signed in to, if it is connected.

The user can limit the run ("only github", "only my work account").

### 3. Skip the accounts that are up to date

The state file is `~/.config/clins/migrate-posts.json`:

```json
{"accounts": {"github.com/<login>": {"version": "0.7.0", "date": "2026-10-26"},
              "linear/<workspace>": {"version": "0.7.0", "date": "2026-10-26"}}}
```

When an account's `version` is the current version, say "`<account>`: up to date since `<date>`" and skip it. "Check again" ignores the file. If the file does not exist, every account runs.

### 4. Find the posts

For each account that runs:

```bash
gh search prs --author @me --state open --limit 1000 --json url,repository,number,title
gh search issues --author @me --state open --limit 1000 --json url,repository,number,title
```

GitHub search returns at most 1000 results. If a search returns 1000, some posts can be missing: say so in the report, and do not record the account in step 8.

For Linear, list all the issues the user created (`creator: "me"`) that are not done or canceled, and read every page. Ask only for the fields you need, since descriptions are long. Do not filter by `updatedAt`: a post that needed no change in the last run was not updated then, but a new migration can apply to it.

Fetch each body (`gh pr view <url> --json body -q .body`, `gh issue view`, or `get_issue`) and keep only the ones with the clins footer.

### 5. Plan each post

Save the body exactly as it came back, then:

```bash
python3 <new-folder>/skills/post/scripts/check_post.py --fix body.md > fixed.md
python3 <new-folder>/skills/post/scripts/check_post.py --platform <github|linear> --langs auto fixed.md
diff body.md fixed.md
```

- `--fix` keeps everything below the footer, and the line endings, as they were. It leaves a post with mixed line endings alone.
- If the check says the post must start with a lead, not a heading, run it again with `--template`.
- `fixed.md` the same as `body.md`: the post is up to date.
- Otherwise the plan is the diff. Read it: it may change only block titles and the footer. Any other change is a bug in `--fix`. Stop and report it.
- Errors the check still shows go in **Left as is**.

### 6. Dry run

Show one table for all accounts, then ask once (with the question tool, if the agent has one): apply all, pick some, or stop.

| Account | Post | Changes | Left as is |
|---|---|---|---|
| github.com/&lt;login&gt; | [&lt;owner&gt;/&lt;repo&gt;#12](url) "Add retry" | read time (2 blocks), footer block | 1 sentence over 30 words |
| linear/&lt;workspace&gt; | [ENG-123](url) "Fix the login redirect" | none, up to date | |

**No dry run:** when the user says so ("no dry run", "just do it"), skip the question and apply every planned change. Every other step still runs: the plan, the backup, the fetch before the write and the check after it. Show the same table at the end, with the result of each post.

### 7. Apply, one post at a time

1. Fetch it again. If it differs from the plan, plan it again and, outside "no dry run", ask again.
2. Save the body you just fetched, the one you will change, to `~/.config/clins/migrate-posts/backups/<date>/<host>-<owner>-<repo>-<number>.md` (`linear-<ID>.md` for Linear).
3. Run `--fix` on it, and check the result. Only the **Left as is** errors may remain, and the diff is the one you planned. Otherwise, do not write the post. Report it.
4. Write it with the host skill: [`clins:github`](../github/SKILL.md) (`gh pr edit` or `gh issue edit` with `--body-file fixed.md`) or [`clins:linear`](../linear/SKILL.md) (`save_issue` with `patch`, one `replace` per changed line from the diff).
5. Fetch it once more, and make sure that it matches what you wrote.

### 8. Record and report

For each account where every post is now up to date, or was skipped on purpose, write the current version and today's date to the state file. Do not record an account with a failed post, or with a search that hit the limit, so the next run tries it again.

Report the table with the results, the backup folder, and the "Left as is" errors. A person fixes those with `clins:post` ("Updating a post") if they want to.

## Adding a fix

When a change to `post`, `create-pr`, `github` or `linear` changes how a post looks, add a fix to `--fix` in `check_post.py`, with a test, in the same pull request. A fix changes markup only, runs only on a post that has the old format, and does nothing the second time. If the check cannot see the change, add a check first. A change that needs judgment (a new section, a rewritten lead) gets no fix: the check reports it, and a person updates the post.

Delete a fix, and its test, once no open post needs it: after this skill has run on every account past that version.
