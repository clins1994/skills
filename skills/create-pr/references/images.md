# Before/after images in a PR

## Pick the images

- **The UI changes:** one before/after pair per state that changed (screen, dialog, error, size, language).
- **No UI change:** a small diagram only when it shows something the text cannot (a new flow, a changed call order). Skip it if a review bot already draws one.
- **Nothing to show:** no images.

Each image must show a difference the reader would otherwise have to imagine.

## Capture

Follow [`capture.md`](capture.md): "before" from the base, "after" from the head, same size and data on both sides, cropped to the change. Open every image before you use it. A blank, loading or wrong image blocks the step. Keep the files in one folder outside the repo, with names that say what they show (`login-before.png`).

## Put them in the body

Between the lead and `---`, with **relative local paths**. The host skill swaps them for uploaded URLs:

```markdown
<lead>

| Before | After |
|---|---|
| ![Login form with no error message](./login-before.png) | ![Login form showing "Wrong password"](./login-after.png) |
| A wrong password shows nothing. | A wrong password shows an error. |

---
```

- With more than one language, put every language in the header (`Before / 前`) and in each caption, one line per language (`<lead language><br><next language>`), in the post's language order.
- Alt text says what the image shows, never "screenshot".
- A new state with no "before" goes below the table, alone, with its caption.
- A video goes in its own paragraph as `![](./flow.mp4)`.
- In the Screenshots section of the details, do not repeat the images. Say they are at the top and how you made them (device or browser, size, base and head commits).

The host skill uploads the files and swaps the local paths for hosted URLs (on GitHub: `gh --attach`, see [`clins:github`](../../github/SKILL.md)). Then it checks that every image renders.

If the user cannot upload images from the CLI, post the body with placeholders. This happens on GitHub without write access to the repo, which is usually the case for a PR from a fork. Put the placeholder in the same cell as the image and keep the caption row:

```markdown
| Before | After |
|---|---|
| 📎 **Paste `login-before.png` here** | 📎 **Paste `login-after.png` here** |
| A wrong password shows nothing. | A wrong password shows an error. |
```

Then give the user the local path of each file. They paste each image over its placeholder in the browser. Run the render check only after the images are in. Until then, make sure that no `./` path is left in the body. The host skill has the steps ("Without write access" in [`clins:github`](../../github/SKILL.md)).
