---
name: github
description: Post to GitHub with gh - pull request bodies with uploaded images (`gh --attach`) and a render check, PR comments, replies inside review threads, and issues. Gives the GitHub block syntax and safe edits that keep bot sections below the footer. The text comes from clins:post; clins:create-pr uses this skill for its GitHub steps. Use whenever you post, comment, reply, or file an issue on GitHub, or upload images to a GitHub post.
user-invocable: true
argument-hint: "[pr | comment | reply | issue] [number or URL to update] [--lang <code>]"
---

# /clins:github — Post to GitHub

This skill sends a post to GitHub. The text (lead, details block, language, footer, check) comes from [`clins:post`](../post/SKILL.md). To open a pull request, start with [`clins:create-pr`](../create-pr/SKILL.md). It uses this skill for the GitHub steps.

## Rules

- Never merge, approve or close a PR.
- Never post `@greptileai`. Greptile reviews every push by itself.
- Send text from a file (`--body-file`, `-F body=@file`), never inline, so newlines and backticks survive.
- In a public repo, an attached image is public.

## Preflight

1. `gh auth status`. For images, also push access to the repo and `gh --version` 2.99 or newer (for `--attach`). If it is older, tell the user to upgrade `gh`, and stop.
2. `gh repo view --json nameWithOwner,visibility`.
3. Read the repo's `AGENTS.md`, `CLAUDE.md`, and `.github/` templates. Their headings and required lines win.

## GitHub syntax

- Collapsed block: `<details><summary><h3>🇬🇧 More details (for agents)</h3></summary>`, a blank line, the content, a blank line, `</details>`. The blank line after `</summary>` is required, or GitHub shows raw Markdown. The `<h3>` makes the title bigger.
- Never `<details open>`. Never Linear's `>>>`.
- Mention: `@login`. Link: `#123` or `owner/repo#123`.
- Check with `check_post.py --platform github`.

## Pull request body with images

Run `gh` from the folder that holds the body and the images, so the `./` paths in the body match. That folder is outside the repo, so pass `-R` and `--head`. Push the branch first.

```bash
gh pr create -R <owner>/<repo> --head <branch> --title "<title>" --body-file body.md --assignee <login> \
  --attach ./login-before.png --attach ./login-after.png     # add --draft if not ready
gh pr edit <n> -R <owner>/<repo> --body-file body.md [--attach ./new.png]
gh pr view <n> -R <owner>/<repo> --json body -q .body > body.md                # fetch to update
```

Every `--attach` path must match a path in the body exactly. `gh` uploads each file to GitHub's attachment store and writes a `https://github.com/user-attachments/assets/...` URL in its place. Nothing is committed, so no review runs.

**Check that the images render:**

1. The body from `gh pr view` has only `user-attachments` URLs, and no `./` path.
2. Fetch each image from the HTML GitHub renders for you:

   ```bash
   gh api repos/<owner>/<repo>/pulls/<n> -H "Accept: application/vnd.github.html+json" --jq .body_html \
     | grep -oE 'src="https://[^"]*(user-images|user-attachments)[^"]*"' | sed 's/^src="//;s/"$//;s/&amp;/\&/g' \
     | while read -r u; do curl -sL -o /dev/null -w '%{http_code} %{content_type}\n' "$u"; done
   ```

   Every line must be `200 image/...` or `200 video/...`.
3. In a private repo, an unauthenticated request to `github.com/user-attachments/...` returns 404 even when members see the image. That is expected.

## PR comment

```bash
gh pr comment <n> -R <owner>/<repo> --body-file post.md
gh api repos/<owner>/<repo>/issues/comments/<id> -q .body > post.md            # fetch to update
gh api -X PATCH repos/<owner>/<repo>/issues/comments/<id> -F body=@post.md
```

## Reply in a review thread

Reply in the thread, not as a new top-level comment. `<id>` is the review comment's id, from `gh api repos/<owner>/<repo>/pulls/<n>/comments`:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments/<id>/replies -F body=@post.md
```

A short post is usually right: "Fixed in abc1234." Resolve the thread only if the user asked, or if the fix does exactly what the comment asked.

## Issue

Headings, unless the repo's issue template has its own: Context, Work, Done when. With `--lang ja`: 背景, やること, 完了条件.

```bash
gh issue create -R <owner>/<repo> --title "<title>" --body-file post.md [--assignee <login>] [--label <name>]
gh issue view <n> -R <owner>/<repo> --json body -q .body > post.md            # fetch to update
gh issue edit <n> -R <owner>/<repo> --body-file post.md
```

## Updating any post

Fetch it, change it with `clins:post` ("Updating a post"), keep everything below the footer exactly as it is, check, then save with the matching command. Keep image URLs that are already there unless you replace those images.
