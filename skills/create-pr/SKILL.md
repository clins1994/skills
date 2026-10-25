---
name: create-pr
description: Create or update a pull request that a reviewer understands from the top of the page - a clear title, a lead, before/after images right under it for UI changes, and the full description in a collapsed block. Reads the diff and the exact base...head range, runs the checks that match the change, captures the images, writes the text with clins:post in the user's languages, and posts through the host skill (clins:github for GitHub). Hands off to clins:fork-review when the setting wants a review on the user's fork first. Never merges. Use when asked to open, create, publish, prepare or update a PR or merge request, or to add screenshots to one.
user-invocable: true
argument-hint: "[update <number or URL>] [--draft] [any language changes]"
---

# /clins:create-pr — Create a reviewable pull request

A reviewer opens the pull request and sees, in this order:

1. The lead (one per language), from [`clins:post`](../post/SKILL.md).
2. **The images.** Before and after, side by side, with a one-line caption. Only when the change is visible.
3. `---`, the collapsed details block(s) and the footer, from `clins:post`. The footer names `clins:create-pr`.
4. Whatever a review bot appends later. Nobody edits it.

This skill owns the **workflow**: what goes in, and in what order. `clins:post` owns the text. The host skill owns the commands: [`clins:github`](../github/SKILL.md) for GitHub. For another host (GitLab, Gitea, ...), use its CLI with the same steps.

## Rules

- Never merge, approve or close. People do that, with the merge method the repo uses.
- Say what is verified, what is assumed, and what is not verified. Green CI proves only what CI runs.
- Do not describe changes inherited from a parent branch as this one's.
- Never commit screenshots or other artifacts that only the pull request needs.
- No tokens, secrets, user records or full payloads in the body.

## Workflow

1. **Inspect the repo:** `git status`, current branch, remote, default branch, the PR template, and the rules in `AGENTS.md`, `CLAUDE.md` or `CONTRIBUTING.md`.
2. **Find the range.** Compute the merge base with the target branch and note the exact `base...head` range. If the branch sits on another unmerged branch, target that branch and describe only this one's changes.
3. **Read the full diff.** Separate runtime code from generated files, lockfiles and snapshots. Back every claim about behavior with a file path or symbol.
4. **Run the checks** that match the changed parts (focused tests, typecheck, lint). Write down the exact commands and results.
5. **Images:** if the change is visible, follow [`references/images.md`](references/images.md).
6. **Title:** imperative, under about 70 characters, no period. Match the style the repo already uses (`git log --oneline`, recent merged titles), for example `fix(auth): show an error on a wrong password`. Add the issue ID if the repo's titles carry one. If the repo squash-merges, write the title as the commit you want in history.
7. **Body:** write it with `clins:post`, with `create-pr` as the footer's skill (`check_post.py --skill create-pr`). Headings inside the details, unless the repo's template has its own: Summary, Why, Changes, How it was tested, Not tested (and why), Screenshots (UI only), Related. Translate them for each other language, for example in japanese: 概要, なぜ, 変更点, 確かめたこと, 確かめていないこと・理由, スクショ, 関連. The languages come from `clins:post`: the user's default, and any change they asked for. Link issues the way the host closes them (`closes #123`). In Screenshots, do not repeat the images: say they are at the top, and how you made them.
8. **Route:** if the target repo isn't the user's, read the [`clins:fork-review`](../fork-review/SKILL.md) setting. If it says `fork`, or says `ask` and the user picks the fork, hand off to `clins:fork-review` with the title and body from steps 6–7. It posts the PR on the fork first and comes back to step 9 for each PR. Otherwise go on.
9. **Post:** push the branch, then create or update the pull request with the host skill. Use draft when checks are still running or more work is coming, and tell the user when to mark it ready.
10. **Verify:** open the result and check the title, base, head, and that every image renders (the host skill has the check).

## Updating a pull request

1. Fetch the current body with the host skill.
2. Change the text with `clins:post` ("Updating a post"). Keep image URLs that are already there unless you replace those images.
3. Keep everything below the footer exactly as it is.
4. New image: add its local path to the body and let the host skill upload it.
5. Do not change draft or ready state unless the user asked.

Editing the body starts no review. A push does.
