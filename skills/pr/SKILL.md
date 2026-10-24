---
name: pr
description: Open or update a GitHub PR whose body shows before/after images right under the lead, so a reader sees the change at a glance. Covers the title, which images to take, capturing them (web, Android), uploading them with `gh --attach`, the body order, checking that the images render, and later edits that keep review-bot sections. The text comes from clins:post, in English or, with `--lang <code>`, in two languages. Use whenever you open a PR, write or edit a PR description, or add screenshots to a PR.
user-invocable: true
argument-hint: "[open | update <PR number or URL>] [--lang <code>]"
---

# /clins:pr — PRs with before/after images

A reader opens the PR and sees, in this order:

1. The lead (or both leads, with `--lang`). From [`clins:post`](../post/SKILL.md).
2. **The images.** Before and after, side by side, with a one-line caption.
3. `---`, the collapsed details block(s) and the footer. From `clins:post`.
4. Whatever a review bot appends later. Nobody edits it.

This skill owns the title, the images and the `gh` steps. The text rules live in `clins:post`. Pass `--lang` through to it.

## Rules

- Never merge, approve or close a PR. People do that, with the merge method the repo uses.
- Never post `@greptileai`. Greptile reviews every push by itself.
- Never commit screenshots. Upload them with `gh --attach`.
- In a public repo an attached image is public. Leave out client data, secrets and personal data.
- Say what you checked and what you did not. Green CI proves only what CI runs.

## Step 0: Preflight

1. `gh --version` is 2.99 or newer (for `--attach`). If not, tell the user to upgrade `gh` and stop.
2. `gh auth status`, with push access to the repo.
3. `gh repo view --json visibility -q .visibility`.
4. Read the repo's `AGENTS.md`, `CLAUDE.md` and `.github/pull_request_template.md`.

## Step 1: Title

Imperative, under about 70 characters, no period. Use the scope style the repo already uses (`git log --oneline`, `gh pr list --state merged -L 10`), for example `api: ...` or `fix(auth): ...`. Add the issue ID if the repo's titles carry one. Say what changes, not which files.

## Step 2: Pick the images

- **The UI changes:** one before/after pair per state that changed (screen, dialog, error, size, language).
- **No UI change:** a small diagram only when it shows something the text cannot (a new flow, a changed call order). Skip it if a review bot already draws one.
- **Nothing to show:** no images.

Each image must show a difference the reader would otherwise have to imagine.

## Step 3: Capture

Follow [`references/capture.md`](references/capture.md): "before" from the base, "after" from the head, same size and data on both sides, cropped to the change. Open every image before you use it. A blank, loading or wrong image blocks the step. Keep the files in one folder outside the repo, with names that say what they show (`login-before.png`).

## Step 4: Write the body

1. Write the text with `clins:post` (PR description).
2. Put the images between the lead and `---`, with **relative local paths**. `gh` swaps them for uploaded URLs in step 5:

   ```markdown
   <lead>

   | Before | After |
   |---|---|
   | ![Login form with no error message](./login-before.png) | ![Login form showing "Wrong password"](./login-after.png) |
   | A wrong password shows nothing. | A wrong password shows an error. |

   ---
   ```

   - With `--lang`, put both languages in the header (`前 / Before`) and in each caption (`<other language><br><English>`).
   - Alt text says what the image shows, never "screenshot".
   - A new state with no "before" goes below the table, alone, with its caption.
   - A video goes in its own paragraph as `![](./flow.mp4)`.
3. In the Screenshots section of the details, do not repeat the images. Say they are at the top and how you made them (device or browser, size, base and head commits).
4. Run `clins:post`'s `check_post.py` on the file.

## Step 5: Upload and post

Push the branch first. Run `gh` from the image folder so the `./` paths match. That folder is outside the repo, so pass `-R` and `--head`. Every `--attach` path must match a path in the body exactly.

```bash
cd <image folder>
gh pr create -R <owner>/<repo> --head <branch> --title "<title>" --body-file body.md --assignee <login> \
  --attach ./login-before.png --attach ./login-after.png     # add --draft if not ready
gh pr edit <n> -R <owner>/<repo> --body-file body.md --attach ./new.png    # open PR
```

`gh` uploads each file to GitHub's attachment store and writes a `https://github.com/user-attachments/assets/...` URL into the body. Nothing is committed, so no review bot runs.

## Step 6: Check the images render

1. `gh pr view <n> -R <owner>/<repo> --json body -q .body`: every image is a `user-attachments` URL and no `./` path is left.
2. Fetch each image from the HTML GitHub renders for you:

   ```bash
   gh api repos/<owner>/<repo>/pulls/<n> -H "Accept: application/vnd.github.html+json" --jq .body_html \
     | grep -oE 'src="https://[^"]*(user-images|user-attachments)[^"]*"' | sed 's/^src="//;s/"$//;s/&amp;/\&/g' \
     | while read -r u; do curl -sL -o /dev/null -w '%{http_code} %{content_type}\n' "$u"; done
   ```

   Every line must be `200 image/...` or `200 video/...`.
3. In a private repo, an unauthenticated request to `github.com/user-attachments/...` returns 404 even when the image works for members. That is expected.

## Updating a body later

1. `gh pr view <n> -R <owner>/<repo> --json body -q .body > body.md`.
2. Change the text with `clins:post` ("Updating a post"). Keep the existing image URLs unless you replace those images.
3. Keep everything below the footer exactly as it is.
4. New image: write its local path in the body and pass it with `--attach`.
5. `gh pr edit <n> -R <owner>/<repo> --body-file body.md [--attach ...]`, then step 6 again.
6. Do not change draft or ready state unless the user asked.

Editing the body starts no review. A push does.
