---
name: raycast-publish
description: Publish a Raycast extension to the Raycast Store through a pull request on raycast/extensions - sync your fork and pull contributions, prepare the extension against the store guidelines read live from Raycast's docs, write the full PR description from Raycast's template with clins:post before publishing, run `ray publish`, fill the draft PR at once, get Greptile to 5/5 with clins:address-reviews while it is still a draft, then mark it ready on the user's OK. A setting moves "ready" before the review loop. Never merges. Use when asked to publish, submit, ship or update a Raycast extension in the Store, or to open its PR on raycast/extensions.
user-invocable: true
argument-hint: "[extension folder] [ready after-review | after-description]"
---

# /clins:raycast-publish — Publish a Raycast extension

Raycast publishes extensions from pull requests on [`raycast/extensions`](https://github.com/raycast/extensions). Its CLI opens that PR with an empty description, and Greptile and the Raycast reviewers see whatever is there. This skill makes sure the PR has a full description from the first minute, and that Greptile has nothing left to say before the reviewers are called in.

This skill owns the **route**: sync, prepare, describe, publish, review, ready. [`clins:post`](../post/SKILL.md) owns the text. [`clins:github`](../github/SKILL.md) owns the `gh` commands. [`clins:address-reviews`](../address-reviews/SKILL.md) owns the fix loop, and [`clins:greptile`](../greptile/SKILL.md) owns the Greptile parts.

## Raycast's workflow is read live

This skill encodes one way of working: description first, Greptile 5/5, a stop for the user's OK. Raycast's side belongs to the Raycast team and can change at any time: CLI commands and flags, store rules, the PR template, bot behavior. So:

- Run the CLI as `npx @raycast/api@latest <command>`, and say which version ran.
- Read the store rules and the PR template from `raycast/extensions` on every run (see "Live sources"). They win over this file.
- Everything this file says about Raycast is marked **last seen**, with a date and a CLI version. Check it before you rely on it (see "Re-check on every run").
- When a live source disagrees with this file, follow the live source and tell the user what changed.
- When a step no longer fits what Raycast does, stop and ask. Do not force the old way.

## Rules

- Never merge, approve or close the PR.
- Never run the publish command before the user says go (step 5). Never mark the PR ready before the user says go (step 8).
- Never push to the PR branch (`ext/<name>`) with `git`. Every change goes through the extension folder and the publish command. A direct push makes the next publish fail until you pull contributions.
- Never paste a token. Pass `gh`'s token by command substitution only, as in step 6.
- Never post `@greptileai` except as `clins:greptile` says.
- The extension repo's `AGENTS.md` and `CLAUDE.md` win over this file. Raycast's live docs win over both for store rules.

## Settings

One line in an instructions file the agent already reads:

```
clins:raycast-publish: ready after-review
```

- `ready after-review` (default): describe, run the review loop on the draft until Greptile is done, stop for the user's OK, then mark it ready. Raycast reviewers first see a PR with no open Greptile issues.
- `ready after-description`: describe, stop for the user's OK, mark it ready, then run the review loop. The PR reaches the reviewers' queue sooner, and they may see Greptile's comments while the loop works on them.

Look in this order, and use the first one you find: what the user says for this run, the extension repo's `CLAUDE.local.md`, `AGENTS.md` or `CLAUDE.md`, then the user's global instructions file (for example `~/.claude/CLAUDE.md`). With no line, use `after-review`, and do not ask.

### clins:fork-review

Raycast PRs need no review on your fork: Greptile reviews them on `raycast/extensions`. The `clins:fork-review` hook watches only `gh pr create`, which this skill never runs, so it does not get in the way. If the user has a global `clins:fork-review` line with `mode ask` or `mode fork`, offer once to add this line to the global file, so a manual `gh pr create` to Raycast is not blocked either:

```
clins:fork-review raycast/extensions: mode origin
```

A line for one repo wins over a plain line.

## Live sources

Fetch these at the start of every run:

```bash
gh api repos/raycast/extensions/contents/docs/basics/prepare-an-extension-for-store.md -H "Accept: application/vnd.github.raw"
gh api repos/raycast/extensions/contents/docs/basics/publish-an-extension.md -H "Accept: application/vnd.github.raw"
gh api repos/raycast/extensions/contents/docs/basics/contribute-to-an-extension.md -H "Accept: application/vnd.github.raw"
gh api repos/raycast/extensions/contents/.github/pull_request_template.md -H "Accept: application/vnd.github.raw"
npm view @raycast/api version
npx @raycast/api@latest --help
```

If a path is gone, list the folder (`gh api repos/raycast/extensions/contents/docs/basics -q '.[].name'`) and find the page that took its place.

## Re-check on every run

What Raycast did when this skill was written (last seen: October 2026, `@raycast/api` 2.9.0), how to check it, and what to do when it changed:

| Last seen | Check | If it changed |
|---|---|---|
| The tools: `ray publish` opens the PR (the docs say `npm run publish`, and the template's script is `npx @raycast/api@latest publish`), and `ray pull-contributions` merges changes made upstream. | `npx @raycast/api@latest --help`, the publish docs, and `scripts.publish` in the extension's `package.json`. | Use the commands the docs name now. If publish or pull-contributions is gone, stop and ask. |
| The extension should use the latest `@raycast/api`. | `npm view @raycast/api version` against the extension's `package.json`. | Offer the upgrade (and `ray migrate` when the docs say so) before you publish. |
| `ray publish` needs a git repo with a clean working tree. | `git status` in the extension folder. | Follow the CLI's message. |
| `ray publish` forks `raycast/extensions` as `<you>/raycast-extensions`, keeps its own clone, copies the whole extension folder into it, pushes the branch `ext/<name>`, and opens a **draft** PR with Raycast's template and every section empty. | Right after publishing: `gh pr view <n> -R raycast/extensions --json isDraft,headRefName,body`. | If it opened ready, tell the user, and go to the review loop at once. If the CLI wrote a full body, merge your text into it instead of replacing it. |
| The copy ignores `.gitignore`. It skips only a fixed list (`.git`, `node_modules`, `raycast-env.d.ts` and a few build folders). | After publishing, compare the extension folder with the files in the PR (`gh pr view <n> -R raycast/extensions --json files`). | Flag any file that should not be there, and offer to remove it and publish again. |
| A second `ray publish` finds the open PR, pushes to the same branch, and leaves the body alone. | The publish output, and the PR body after it. | Fix the body again if it changed. |
| `ray publish` uses the token in `GITHUB_ACCESS_TOKEN` when it is set, and asks for a GitHub sign-in when it is not. | The publish output: did it ask for a sign-in? | Let the CLI's own sign-in run. |
| Greptile reviews drafts on `raycast/extensions`, about 5 to 20 minutes after the PR opens. | `clins:greptile` on this PR. | If no review comes, ask for one as `clins:greptile` says. If that fails too, stop, and offer `ready after-description`. |
| Raycast's own checks run as GitHub Actions (app `github-actions`). Third-party apps (`socket-security`) add checks that can start after Greptile finishes. | The app slugs in the check runs on the head (step 7, "The ready gate"). | Put the checks that build and lint the extension in the gate, whatever app runs them. Leave the rest out. |
| `raycastbot` comments as soon as a PR opens, drafts too. On an update to an extension with other contributors, it pings them. | Its comments on recent PRs of the same kind (new extension or update). | Describe what it does now in the warning in step 5. |

## Workflow

### 1. Detect

1. **The extension folder:** the one the user named, or the current folder. Its `package.json` has `"$schema": "https://www.raycast.com/schemas/extension.json"`. Read `name`, `title`, `author`, `version` of `@raycast/api`, `commands`.
2. **The user's Raycast username:** `npx @raycast/api@latest profile`. If nobody is signed in, ask the user to run `npx @raycast/api@latest login` in a terminal.
3. **The user's GitHub login and fork:** `gh api user -q .login`, then the fork query from `clins:fork-review` ("When it applies"). No fork is fine: the CLI makes one.
4. **New or update:** it is an update when `gh api repos/raycast/extensions/contents/extensions/<name>/package.json` exists. Raycast may keep it under another folder name: check `.github/extensionName2Folder.json` in `raycast/extensions`.
5. **The setting** (above), and the live sources.

### 2. Sync

1. If the user has a fork, sync it: `gh repo sync <you>/raycast-extensions --source raycast/extensions -b main`. If it fails because the fork has commits upstream does not have, stop and ask. Do not pass `--force` on your own.
2. **Update only:** pull what others changed in the Store version, with the command the docs name (last seen: `npx @raycast/api@latest pull-contributions`). It needs a clean working tree, and it merges with `git merge`. Resolve conflicts with the user. Never take one side of a conflict without saying which.

### 3. Prepare

Go through the store guidelines from the live docs, item by item. Last seen, they asked for:

- `package.json`: `author` is the Raycast username, `license` is `MIT`, the latest `@raycast/api`, `platforms` that match the APIs the code uses, at least one category in Title Case. A contributor to someone else's extension is in `contributors`.
- Titles and descriptions that follow the docs' naming rules (Apple Style Guide, noun titles, a subtitle only when it adds context).
- A 512×512 PNG icon that is not the default Raycast icon, and works in light and dark themes. An extension with the default icon is rejected.
- `package-lock.json` from `npm`.
- `CHANGELOG.md` with a new top entry: `## [<title>] - {PR_MERGE_DATE}`.
- Screenshots in `metadata/`: PNG, 2000×1250, at most six, at least three suggested. Raycast's Window Capture saves them there.
- A `README.md` when setup is needed (and media in a top-level `media/` folder), or a `help.md` for required preferences.
- No unused files in `assets/`. No analytics, no Keychain access, US English.
- `npm run lint` and `npm run build` pass. The user opens the distribution build in Raycast and checks that it works.

Then:

1. Fix what is mechanical (lint fixes, the changelog entry, the API version, `platforms`). Ask about what needs a person: the icon, titles, screenshots, anything the docs call a judgment.
2. Tell the user which items the live docs added or dropped compared with the list above.
3. **What will ship:** the CLI copies the whole folder. List what is in it beyond the tracked files: `git status --short --ignored`. Anything that should not ship must be deleted, not only ignored.
4. Commit in the extension repo, staging files by name. The CLI reuses your commit subjects as its commit message, so write them as you want them in Raycast's history. The tree must be clean before step 6.

### 4. Write the PR text

Write it before publishing, so the PR is never empty for long.

1. **Title:** the CLI uses "Add <name> extension" or "Update <name> extension". Keep that form unless recent merged titles in `raycast/extensions` show another (`gh pr list -R raycast/extensions --state merged -L 10`).
2. **Body:** start from the live `.github/pull_request_template.md`. Keep every heading, in its order, and every checklist line word for word. Replace each section's `<!-- ... -->` hint with that section's content. Leave no section empty.
   - The first section (last seen: `## Description`) holds the `clins:post` lead and the details block(s). For a new extension, say what it does and for whom. For an update, say what changed and why.
   - The screencast section holds images or a short video. Screenshots already in `metadata/` can be linked from the PR branch after publishing (step 6). For other images, follow "Without write access" in `clins:github`: the user has no write access to `raycast/extensions`, so `--attach` does not work there.
   - The checklist: tick a line only when it is true for this PR. Leave the rest unticked, and say why in the details.
   - The footer goes last, after the checklist, and names `clins:raycast-publish`.
3. Check it: `python3 <post-skill-dir>/scripts/check_post.py --platform github --skill raycast-publish --template body.md`, with `--langs` from `clins:post`.

### 5. Stop for the user

Show:

- the title and the body,
- the list of files that will ship (step 3),
- for an update, who the bot will ping when the PR opens (see "Re-check on every run").

Ask: "Publish it now? This opens a draft PR on raycast/extensions." Wait for a clear yes.

### 6. Publish and describe

1. From the extension folder, run the publish command with the same CLI whose help you checked, and with `gh`'s token so the CLI needs no sign-in of its own:

   ```bash
   GITHUB_ACCESS_TOKEN=$(gh auth token) npx @raycast/api@latest publish 2>&1 | tee <temp-folder>/publish.log
   ```

   If the extension's `scripts.publish` does something more than `ray publish` (a build step, a custom command), show it to the user and ask which to run.

   Give the call a 600000 ms timeout. If it waits for input (a GitHub sign-in, or a question about a half-finished merge in its clone), stop and ask the user to run it in a terminal.
2. Take the PR URL from the log. If there is none, read the log, report, and stop.
3. Run the checks in "Re-check on every run" for the PR: draft or not, the body, the files.
4. Fill in any image placeholders that point at `metadata/`, using the PR's head commit, so the links outlive the branch: `https://github.com/<you>/raycast-extensions/blob/<headRefOid>/extensions/<folder>/metadata/<file>.png?raw=true`.
5. Save the title and body with `clins:github` (`gh pr edit <n> -R raycast/extensions --title ... --body-file body.md`), and run its render check.

### 7. Review

With `ready after-review`, run this on the draft. With `ready after-description`, run step 8 first.

Hand off to `clins:address-reviews` with:

- the PR URL, and `-R raycast/extensions`,
- the working folder: the extension folder (not the CLI's clone),
- the push command: `GITHUB_ACCESS_TOKEN=$(gh auth token) npx @raycast/api@latest publish` (or the command the user chose in step 6), run from that folder after each commit. Pass it without the `| tee` from step 6, so that a failed publish fails the command.

It loops until the ready gate below holds and every person has a reply. Tell it that checks outside the gate do not block "done": it does not wait for them. A new publish can change the body: check it after each round, and fix it as in step 6.

**The ready gate.** Sort the check runs on the head by the app that runs them:

```bash
gh api "repos/raycast/extensions/commits/<headRefOid>/check-runs?per_page=100" \
  --jq '.check_runs[] | "\(.app.slug) | \(.name) | \(.status) \(.conclusion // "")"'
```

- **Raycast's own checks** (last seen: app `github-actions`: the extension's build check named after its folder, `Check`, `changelog`, `metadata-images`): every one completed, with no failure. Skipped is fine.
- **Greptile** (app `greptile-apps`): `5/5` on the current head and no open Greptile thread. If `clins:greptile` is installed, read both the way it says. Without it, read the score in Greptile's summary comment, check that its "Last reviewed commit" is the head, and count the open review threads by `greptile-apps`.
- **Any other app** (last seen: `socket-security`): does not block. These often start after Greptile finishes and run again on every push. Show their state to the user. If one failed, show what it flagged, and let the user decide.

### 8. Stop for the user, then mark it ready

With `ready after-review`, ask as soon as the ready gate (step 7) holds on the current head. Check the gate yourself. Do not wait for checks outside it, and do not wait for the loop to time out on them. If the gate does not hold (round cap, no change, a review that did not come, a failed Raycast check), keep the PR a draft, show what is left, and stop.

Show the PR URL, Greptile's score, what the loop fixed, what it parked, and any check still running outside the gate. Ask: "Mark it ready for review? This puts it in the Raycast reviewers' queue." On a clear yes:

```bash
gh pr ready <n> -R raycast/extensions
```

### 9. After

Link the PR. Raycast reviewers may ask for changes later: fix them the same way (step 7). When the PR merges, Raycast publishes the extension to the Store. Offer to delete the CLI's local branch state only if the user asks.

## Updating a published extension later

Run this skill again. Step 1 finds the extension upstream, step 2 pulls contributions, and step 4 writes a new body for the new PR.

## Report

```
## raycast-publish: <extension> → raycast/extensions#<n>

- PR: <url> (draft | ready)
- Greptile: <score> on <short sha>
- Fixed by the loop: <n>, parked: <n>
- Shipped files outside git: <none | list>
- Raycast changes since this skill was written: <none | what the live docs or CLI did differently>
```
