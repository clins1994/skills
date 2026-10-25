---
name: address-reviews
description: Drive an open pull request to merge-ready in a bounded loop - fix failing CI, fix what review bots (Greptile, CodeRabbit, others) and people asked for, reply in each thread with clins:post, resolve bot threads, ask the bots for a new review when they do not review on push, wait for it, and repeat until CI is green and every bot is done. Parks what needs a person. Edits, commits and pushes, never merges. Also runs locally before a PR with `local`. Use when asked to address, fix or answer review comments, get a PR to 5/5, make CI green, or "drive this PR to done".
user-invocable: true
argument-hint: "[<PR number or URL> | local [base-branch]] [max <rounds>]"
---

# /clins:address-reviews — Address reviews until the PR is done

This skill edits code, commits and pushes until a pull request is done:

- CI is green, or every failure left is one it could not fix (and says why).
- Every review bot is done with the current commit (for Greptile: `5/5` and no open thread).
- Every comment from a person has a reply. The ones that need a decision are parked for the user.

It loops for at most 5 rounds (`max <n>` changes this). It does not stop early while a bot still reports a bug.

The text of every reply comes from [`clins:post`](../post/SKILL.md). The GitHub commands come from [`clins:github`](../github/SKILL.md). Each review bot has its own skill for where its comments are, how to trigger it and when it is done: [`clins:greptile`](../greptile/SKILL.md) for Greptile. See "Reviewers".

## Rules

- Never merge, approve or close the PR. Never mark it ready for review.
- Never use `--no-verify`, force-push, `git reset --hard`, `git checkout .`, `git clean -f`, or amend a commit. If a hook fails, fix the cause and make a new commit.
- Stage files by name. Never `git add -A` or `git add .`.
- Stay on the PR's head branch, or in the working folder that a push override names (see "Push override").
- Never resolve a thread that a person started. Reply, and let them resolve it.
- Never read a review for an older commit as the current one. If a bot's review does not come, stop and report.
- The repo's `AGENTS.md`, `CLAUDE.md` and CI notes win over this file.

## Run it in the background

A round can wait up to 10 minutes for a bot, so a full run can take an hour. Run it as a background agent unless the user wants to watch. Give the agent this file, the PR, and what you already know about the PR. In the background, it asks nothing: what needs the user goes into "Parked" in the report.

## Setup

1. **The PR.** Use the number or URL the user gave. Else: `gh pr list --head "$(git branch --show-current)" --json number,url`. One PR per run. If there is none, say so and stop.
2. Take `<owner>/<repo>` from the PR URL, and pass `-R <owner>/<repo>` to every `gh` call. The PR can live on a fork ([`clins:fork-review`](../fork-review/SKILL.md)), and `gh` without `-R` finds the PR through `origin`, which is often the wrong repo. Then read `gh pr view <n> -R <owner>/<repo> --json headRefName,headRefOid,baseRefName,isCrossRepository`. If the head branch is in a fork you cannot push to, say so and stop.
3. Check out the head branch and pull it (fast-forward only). If the working tree has changes that are not yours, stop and ask. With a push override, work in its folder instead, and skip the checkout.
4. Read `AGENTS.md`, `CLAUDE.md` and `CONTRIBUTING.md`: CI notes, the formatter and lint commands, commit message style, and any review-bot config.
5. **Find the reviewers.** List who has reviewed or commented: `gh pr view <n> --json reviews,comments,latestReviews`, and the check runs on the head. Sort each author into:
   - a **bot with a skill** (for example `greptile-apps[bot]` → `clins:greptile`),
   - a **bot without a skill** (any other `[bot]` author that leaves review comments): see "Reviewers",
   - a **person**.

## A round

### 1. CI

`gh pr checks <n>`. For each failed check, read its log (`gh run view <run-id> --log-failed`). If the repo has its own CI notes or skills, follow them.

- Fix what is clear: format, lint, type errors, a test that the PR broke.
- Do not fix what is not yours or not clear: a flaky test, an outage, a secret that is missing, a failure that is on the base branch too. Note it in the report and go on.

Checks that are still running do not block the round. Step 8 waits for them before it calls the PR done.

### 2. Collect

For each reviewer, get the open feedback **on the current head**:

- Bots with a skill: the skill's "Open comments" and score.
- Bots without a skill and people: open review threads by that author (`reviewThreads`, as in `clins:greptile`), plus their PR comments that have no answer yet. In the first round, read all of them, also the ones from before the last push. In later rounds, skip the ones that you already handled in this run.

Give each item an identity: `path + author + the first 8 words of the comment`, lowercased. You need it for the report and to see a comment come back.

### 3. Triage

Read the code around each comment before you decide. Then mark it:

- **Fix**: a bug, a real risk, or a clear request.
- **Won't fix**: wrong, already handled, or out of scope. You must be able to say why in one sentence.
- **Park**: a person asks a question, the fix needs a product or design decision, the fix is risky (payment, auth, data migration, deleting data), or you are not sure. Parked items do not block "done", but go first in the report.

A bot comment that comes back after a round where you marked it **won't fix** means that your reply did not convince it. Fix it, or park it. Do not answer it the same way again.

### 4. Fix

- Fix the cause, not only the line. When a comment points at a kind of bug (a missing null check, an unescaped value, an unawaited call), look for the same bug in the rest of the PR's diff and fix it there too. This is what makes the next review clean.
- Before you commit a fix, go through every case that the changed text or code handles, not only the case in the comment. A fix for one case often breaks another. For example, a fix to "wait after a push" must still work when there was no push and no request.
- Keep each fix to what the comment asked. Do not refactor around it.
- Update tests and docs when the comment asks for it, or when the fix changes behavior they cover.
- Run the repo's formatter and lint on the changed files. Find them in the repo (`package.json` scripts, `.pre-commit-config.yaml`, `Makefile`, `.rubocop.yml`, `pyproject.toml`, `AGENTS.md`). Do not guess: a wrong formatter rewrites whole files. When an autofix can change behavior (for example `rubocop -A`), read its diff and undo the changes that have nothing to do with the comment.
- Run the tests that cover the changed code, when the repo has a fast way to.

### 5. Commit and push

Small commits, one per comment or per group of comments about the same thing. The message says what changed and which comment it answers, in the repo's commit style, with your co-author footer.

Before you push, record what each bot's skill needs to tell its next review from the last one (for Greptile: "Waiting for a review" in `clins:greptile`). Do it in a round with no commit too, before you ask for a review in step 7. Then push without force, or run the push override's command.

### Push override

Some PRs are not pushed with `git push`. For example, a Raycast extension lives in its own repo, and its PR branch on `raycast/extensions` is written only by Raycast's publish command ([`clins:raycast-publish`](../raycast-publish/SKILL.md)). The caller then passes:

- a **working folder**: where to edit and commit, instead of a checkout of the head branch,
- a **push command**: what to run from that folder after each commit, instead of `git push`.

Read reviews, CI and threads from the PR as usual, with `-R <owner>/<repo>`. Commit in the working folder with the rules above. Run the push command, then read the PR's new `headRefOid`: that is the commit the next review is for. If the command fails, stop and report its output. Never push to the PR branch with `git` when an override is set.

### 6. Reply and resolve

Reply in every thread you triaged, in the thread (see `clins:github`, "Reply in a review thread"). Write the reply with `clins:post`: a short post, usually only the lead. Use the user's saved post languages. If none are saved, do not ask `post`'s first-run question in the background: use the language that the PR body leads with, and say so in the report.

- **Fix**: what you changed and the commit: "Fixed in abc1234: `parse()` now returns early on an empty body."
- **Won't fix**: the reason in one sentence, with the file or line that shows it.
- **Park**: what decision is needed, and from whom. Nothing else.

Then resolve **bot** threads marked fix or won't fix (the bot's skill has the mutation). Leave parked threads and every thread a person started open.

### 7. Ask for a new review and wait

For each bot with a skill, follow its skill: if it does not review on push, ask for a review (a follow-up review, not a full one, when the bot has both). Then wait for its review on the new head, with the skill's time limit.

For a bot without a skill: if a new review from it on the new head appears within 5 minutes, use it. If not, treat that bot as done for this round and say so in the report.

If a bot's wait times out, stop the loop and report. Do not go on with its old review.

### 8. Done?

First wait for CI on the current head to finish: `gh pr checks <n> -R <owner>/<repo> --watch`, as a background command or with a 600000 ms timeout. If it is still running after that, say so in the report. A check that failed since step 1 goes back to step 1 in the next round.

Stop when all of these hold:

- No CI failure on the current head that you can fix.
- Every bot with a skill is done (its skill says when).
- No bot thread is open, except parked ones.
- Every thread and PR comment from a person has a reply.

Otherwise start the next round. Also stop:

- At the round cap. Report what is left.
- When a round changed nothing: you made no commit, and the open items are the same as before the round (by identity). This means only parked items, or comments that you cannot fix, are left. Report them.

## Reviewers

A reviewer skill (like `clins:greptile`) gives `address-reviews` these things:

- the bot's author logins (REST and GraphQL),
- where its score or verdict is, and how to tell it is for the current head,
- its open comments, and how to resolve them,
- whether it reviews each push or waits to be asked, and how to ask (follow-up and full),
- how to wait for its review, and for how long,
- when it is done with a PR.

To support another bot (CodeRabbit, a custom review action), write a skill with those parts next to `greptile`, and add its author here:

| Author | Skill |
|---|---|
| `greptile-apps[bot]`, `greptile-apps-staging[bot]` | [`clins:greptile`](../greptile/SKILL.md) |

## Local mode

`/clins:address-reviews local [base-branch]` runs the loop before a pull request exists, with the Greptile CLI ("Local review" in `clins:greptile`) instead of PR reviews:

- Commit first: the CLI reviews only committed changes. Never push.
- A round: review, triage, fix, run the formatter, commit locally. There are no threads to reply to or resolve.
- Done when the review has no finding that you would fix. Stop at the round cap, or when a round closes no finding (same identities as before, or more).
- Run heavy checks (integration tests, a local app run) once, after the loop, not every round.

## Report

Return one report, in the user's lead language:

```
## address-reviews: <owner>/<repo>#<n>

Status: ✅ Done / ⚠️ Stopped (round cap) / ⚠️ Stopped (no change) / ⚠️ Stopped (<bot> review did not come)
Rounds: N / 5
CI: green / N failing — <which, and why not fixed>
Reviewers: Greptile 5/5 (head abc1234) · <other bot> no open threads · <person> 2 replies

### Parked (needs you)
- <file>:<line> — <who> — <the decision needed>

### Fixed
- [round 1] <file>:<line> — <fix> — <commit>

### Won't fix
- <file>:<line> — <comment> — <reason>

### Left
- <file>:<line> — <comment> — <suggested next step>

### Commits
- <sha> <message>
```

High-risk fixes (payment, auth, data migration) go first in "Fixed" with ⚠️, so that a person looks at them before merging.
