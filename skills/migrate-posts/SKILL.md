---
name: migrate-posts
description: Bring your open posts up to date after the clins skills change - pull request bodies, GitHub issues and Linear issues written with clins:post. Updates the installed skills, finds your open posts on every GitHub account you are signed in to and in Linear, and shows a dry run of what each one needs. Then applies only the format changes in its migrations list, one post at a time, with a backup, and leaves the content as it is. Remembers the version it last ran for each account, so a second run does nothing. Use after the skills change, or when asked to migrate, refresh, restyle or update open posts, PRs or issues.
user-invocable: true
argument-hint: "[no dry run] [check again] [github | linear] [account]"
---

# /clins:migrate-posts — Bring open posts up to date

The clins skills change the look of a post from time to time: a new block title, a read time, a new rule. This skill applies those changes to the posts that are still open, the way a database migration applies a schema change to the rows that already exist. It changes the format, never the content.

The list of changes is [`references/migrations.md`](references/migrations.md). Each entry says which check error it fixes and exactly what to change. **A post changes only where an entry says so.**

## Rules

- Change only what a migration describes. Never rewrite, shorten, translate again or "improve" a post. When the check reports an error that no migration fixes, report it and leave the text as it is.
- Only posts that the account wrote, and that end with the clins footer (`🤖 Generated with [Claude Code](...) using [clins:...]`).
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

The new version lands in `~/.claude/plugins/cache/<marketplace>/clins/<version>/`. Claude Code loads it after a restart, so for this run read the new files from that folder: this `SKILL.md` (if it changed, follow the new one), `references/migrations.md`, and `skills/post/scripts/check_post.py`. For another install (`npx skills`, a clone), update it the way it was installed, and use its folder.

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
gh search prs --author @me --state open --limit 200 --json url,repository,number,title
gh search issues --author @me --state open --limit 200 --json url,repository,number,title
```

For Linear, list the issues the user created (`creator: "me"`) that are not done or canceled. Ask only for the fields you need, since descriptions are long. When the account has a last run, pass `updatedAt` with that date: a post written or migrated since then was updated then.

Fetch each body (`gh pr view <url> --json body -q .body`, `gh issue view`, or `get_issue`) and keep only the ones with the clins footer.

### 5. Plan each post

1. Cut the body after the footer line, and keep the rest aside. Bots own it.
2. Run the new check on the part above:

   ```bash
   python3 <new-folder>/skills/post/scripts/check_post.py --platform <github|linear> --langs auto body.md
   ```

   It prints the languages it found, then the errors. If it says the post must start with a lead, not a heading, run it again with `--template`.
3. Match each error to the migrations. An error that no migration fixes goes in **Left as is**.
4. No errors that a migration fixes: the post is up to date.

### 6. Dry run

Show one table for all accounts, then ask once (with the question tool, if the agent has one): apply all, pick some, or stop.

| Account | Post | Changes | Left as is |
|---|---|---|---|
| github.com/&lt;login&gt; | [&lt;owner&gt;/&lt;repo&gt;#12](url) "Add retry" | 0.7.0 read time (2 blocks) | 1 sentence over 30 words |
| linear/&lt;workspace&gt; | [ENG-123](url) "Fix the login redirect" | none, up to date | |

**No dry run:** when the user says so ("no dry run", "just do it"), skip the question and apply every planned change. Every other step still runs: the plan, the backup, the fetch before the write and the check after it. Show the same table at the end, with the result of each post.

### 7. Apply, one post at a time

1. Save the current body to `~/.config/clins/migrate-posts/backups/<date>/<host>-<owner>-<repo>-<number>.md` (`linear-<ID>.md` for Linear).
2. Fetch it again. If it differs from the plan, plan it again and, outside "no dry run", ask again.
3. Apply the migrations, oldest version first, exactly as written.
4. Check the new text. The errors you fixed are gone and no new error appears. Otherwise, do not write the post. Report it.
5. Write it with the host skill: [`clins:github`](../github/SKILL.md) (`gh pr edit` or `gh issue edit` with `--body-file`, the part below the footer put back unchanged) or [`clins:linear`](../linear/SKILL.md) (`save_issue` with `patch`, only the lines that change).
6. Fetch it once more, and make sure that it matches what you wrote.

### 8. Record and report

For each account where every post is now up to date, or was skipped on purpose, write the current version and today's date to the state file. Do not record an account with a failed post, so the next run tries it again.

Report the table with the results, the backup folder, and the "Left as is" errors. A person fixes those with `clins:post` ("Updating a post") if they want to.

## Adding a migration

When a change to `post`, `create-pr`, `github` or `linear` changes how a post looks, add an entry to [`references/migrations.md`](references/migrations.md) in the same pull request. Give it the version from `plugin.json`, the check error it fixes, and the exact change. If the check cannot see the change, add a check first.
