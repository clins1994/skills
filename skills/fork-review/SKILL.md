---
name: fork-review
description: Review a pull request on your own fork before it goes to the upstream repo. Syncs the fork, pushes the branch, opens the same PR on the fork (ready, not draft), runs the review steps from the user's setting (an agent loop such as /clins:address-reviews, a person or bot to wait for, or a plain wait), stops for the user's OK, then opens the upstream PR from the same branch with the same title and body, and keeps both bodies in sync. A setting picks ask, always fork, or always origin, per user or per repo. Includes an optional Claude Code hook that stops `gh pr create` from skipping the fork. clins:create-pr hands off here. Use when opening a PR on a repo you don't own, or when asked to "review on my fork first".
user-invocable: true
argument-hint: "[fork | origin] [PR number or URL to continue] [review steps for this PR]"
---

# /clins:fork-review — Review on your fork first

Some repos have no reviewer you like, or you want a clean PR before people see it. So the PR goes to your fork first. Whatever review you choose runs there, and you push the fixes there. Only then does the same branch go upstream, with nothing left to fix in public.

This skill owns the **route**: fork, review, upstream. [`clins:create-pr`](../create-pr/SKILL.md) owns the PR content (range, checks, title, images, body). [`clins:github`](../github/SKILL.md) owns the commands. [`clins:post`](../post/SKILL.md) owns the text.

## Rules

- Never open the upstream PR before the review steps are done and the user says go.
- Never merge the fork PR. Merging it would make the fork's base branch drift from upstream.
- Never force-push the fork's base branch. If it has diverged from upstream, stop and ask.
- Start a review bot only the way its skill says (for Greptile, [`clins:greptile`](../greptile/SKILL.md)). Without a skill for it, request a review or wait.
- Open the fork PR ready, not draft. Many review bots skip drafts.

## Settings

One line in an instructions file the agent already reads:

```
clins:fork-review: mode ask; review /clins:address-reviews
clins:fork-review <owner>/<repo>: mode fork; review /clins:address-reviews, then @alice
```

- `mode` is one of:
  - `ask`: ask each time whether to go through the fork or straight to upstream.
  - `fork`: always go through the fork.
  - `origin`: always go straight to upstream. This skill does nothing.
- `review` is a list of steps, run in order, separated by commas or `then` (see "Review steps").
- `fork <owner>/<name>` (optional) names your fork, when the agent can't find it.
- A line with `<owner>/<repo>` applies to that upstream repo only. Use it in the global file for repos you work on in many worktrees, where a `CLAUDE.local.md` would not follow you.

**Repos that already review upstream.** Some upstream repos run a review bot on every PR, so a fork review adds nothing. For example, `raycast/extensions` runs Greptile, and [`clins:raycast-publish`](../raycast-publish/SKILL.md) reviews there on the draft. Give such a repo its own line, which beats a plain `mode fork` line and keeps the hook quiet:

```
clins:fork-review raycast/extensions: mode origin
```

Look in this order. Each part (`mode`, `review`, `fork`) comes from the first place that has it:

1. What the user says for this PR ("straight to upstream this time", "also wait for @bob").
2. The repo's `CLAUDE.local.md`, then `AGENTS.md` or `CLAUDE.md`. In each file, a line for this repo wins over a plain line.
3. The user's global instructions file, for example `~/.claude/CLAUDE.md` for Claude Code or `~/.codex/AGENTS.md` for Codex. Again, a line for this repo wins over a plain line.

**First run.** If no `mode` is found and the PR targets a repo the user doesn't own, ask, in the language the user writes in:

1. "Review PRs on your fork before they go upstream?" Options: **ask each time** (`ask`), **always** (`fork`), **never** (`origin`). Then ask whether that answer is for this repo only or for every repo.
2. Only for `ask` or `fork`: "How should the fork PR be reviewed?" Options: **wait for me** (`wait`), and **something else**, where the user types it, for example "/clins:address-reviews" or "@alice".

Show the line, save it to the user's global file, and say how to change it: "Saved. To change it, just tell me, for example: always review beeper/line on my fork."

## When it applies

Only when the PR targets a repo whose owner isn't the user (`gh api user -q .login`) and the user has a fork of it. On the user's own repos, or with no fork, open the PR normally and say why. Find the fork with:

```bash
gh api graphql -f query='query($o:String!,$n:String!){repository(owner:$o,name:$n){forks(first:1,affiliations:[OWNER]){nodes{nameWithOwner}}}}' -f o=<owner> -f n=<repo> \
  -q '.data.repository.forks.nodes[0].nameWithOwner'
```

The fork can have another name (`<you>/<owner>-<repo>`). Use the `fork` setting when it's set.

With `mode ask`, ask now: "Open this PR on your fork <fork> first, or straight on <owner>/<repo>?" With `origin`, or if the user picks upstream, go back to `clins:create-pr` and post normally.

## Workflow

1. **Prepare the PR** with `clins:create-pr` steps 1–7: range, diff, checks, images, title, body. The base is the upstream base branch.
2. **Sync the fork's base branch** with upstream:

   ```bash
   gh repo sync <fork> --source <owner>/<repo> -b <base>
   ```

   If it fails because the fork's branch has commits upstream doesn't have, stop and ask. Don't pass `--force` on your own.
3. **Push the branch to the fork.** Add a remote for it if there is none (`git remote add fork https://github.com/<fork>.git`), then `git push -u fork <branch>`.
4. **Open the fork PR**, ready, with `clins:github`: `gh pr create -R <fork> --base <base> --head <branch>`, with the same title and body file and the same `--attach` images. You own the fork, so `--attach` works even when upstream would need the no-write-access path. Write down the fork PR's URL.
5. **Run the review steps** on the fork PR (below).
6. **Stop for the user.** Show the fork PR URL, what each step found and fixed, and the commits pushed since step 4. Ask: "Open it on <owner>/<repo> now?" Wait for a clear yes.
7. **Open the upstream PR** with `clins:github`, from the same branch, with the same title and body:

   ```bash
   gh pr create -R <owner>/<repo> --base <base> --head <you>:<branch> --title "<title>" --body-file body.md
   ```

   Images: upload them only once. Reuse the `user-attachments` URLs from the fork PR's body (`gh pr view <n> -R <fork> --json body -q .body`), and leave out `--attach`. Then run the render check from `clins:github` on the upstream PR.
8. **Link them** for the user: fork PR URL, upstream PR URL.

Later pushes to the branch update both PRs, because they share the branch. So a review bot on the fork reviews each push again.

## Review steps

Run them in order. Each step is one of:

| Step | What to do |
|---|---|
| A slash command or skill, such as `/clins:address-reviews` or `/clins:code-review` | Run it on the fork PR, passing the fork PR's URL or `-R <fork>` and number. Many loops find "the PR for this branch" through `origin`, which in a clone of upstream finds the wrong PR or none. Let it push its fixes to the branch. That's the point: they land before upstream sees anything. |
| `@login` or `@org/team` | Request a review on the fork PR: `gh pr edit <n> -R <fork> --add-reviewer <login>` (the reviewer needs access to the fork). Then stop and tell the user who you asked. When the user comes back, read `gh pr view <n> -R <fork> --json reviews,reviewDecision`. Fix what they asked for, push, and say what changed. Go on when the decision is `APPROVED` or the user says so. |
| `wait`, or any words such as `wait for human review` | Stop. Tell the user the fork PR is ready for that review, with its URL. Go on when the user says so. A review bot that reviews every push by itself (Greptile, CodeRabbit) fits here. |

With no `review` set, use `wait`.

## Keeping the bodies in sync

The two bodies stay the same above the `clins:post` footer. Each PR's bot sections below the footer are its own.

- To change the body, change it once with `clins:create-pr` ("Updating a pull request"). Then save it to both PRs with `gh pr edit <n> -R <repo> --body-file body.md`. Before each save, fetch that PR's current body and keep everything below its footer as it is.
- Same for the title: `gh pr edit --title` on both.
- Check that the two leads match after each change: fetch both bodies and compare the text above the footer.

## After upstream merges or closes

Offer to close the fork PR with a comment that links the upstream PR. Close it only on the user's yes. Never merge it.

## The hook (Claude Code only)

The plugin ships a `PreToolUse` hook ([`scripts/pr_guard.py`](scripts/pr_guard.py)) on `Bash`. It acts only on `gh pr create` aimed at a repo the user doesn't own and has a fork of, and reads the same setting:

- `mode origin`, or no setting: does nothing. Installing the plugin changes nothing until you add the line.
- The fork already has a PR (open or closed) for the same branch: does nothing.
- `mode ask`: asks the user to allow or deny the upstream PR.
- `mode fork`: blocks it, and tells the agent to run this skill. To go straight to upstream anyway, the agent needs the user's explicit OK, then puts `CLINS_FORK_REVIEW=skip` in front of the command.
- A failed check under `ask` or `fork` (`gh` missing, offline, timeout): asks the user instead of blocking.

It checks that the fork PR exists, not that the review is done. Step 6 of the workflow holds that line. It doesn't see `gh pr create` run in another folder without `-R` (`cd other && gh pr create`), or PRs opened through a GitHub MCP server.

Other agents (Codex, Cursor, others installed with `npx skills`) get this skill only, with no hook. There, following it is up to the agent.

Run its tests with `python3 skills/fork-review/scripts/pr_guard.py --test`.
