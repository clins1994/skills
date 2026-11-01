# Capture before/after images

## Same conditions on both sides

- **Before** comes from the base: a build of the merge base, or a capture you took before you started the edit.
- **After** comes from the PR head.
- Use the same device or window size, theme, language, test data and wait condition for both. Otherwise the reader sees differences that the PR did not make.
- Run the same commands for both sides. Write them down for the `Screenshots` section.

To build the base without touching your branch, use a detached worktree:

```bash
base=$(git merge-base origin/<default> HEAD)
git worktree add --detach "$SCRATCH/pr-base" "$base"
# build and capture from there, then:
git worktree remove "$SCRATCH/pr-base"
```

## Web

Use the `agent-browser` CLI. Run `agent-browser skills get core` first and follow it. Use a named session:

```bash
export AGENT_BROWSER_SESSION="$(agent-browser session id --scope worktree --prefix task)"
agent-browser set viewport 1280 800
agent-browser open http://localhost:3000/<page>
agent-browser screenshot "$SCRATCH/shots/settings-before.png"
agent-browser close
```

Prefer a page state that the repo already has (a story, an e2e scenario, seed data) over one you click together by hand.

## Android

Use an emulator when you can. A real tablet is fine when the change needs one.

```bash
adb -s emulator-5554 exec-out screencap -p > "$SCRATCH/shots/screen-before.png"
```

- `exec-out` keeps the PNG intact. `adb shell screencap` breaks it with line endings.
- To get the same state on both builds, drive the app with the same `adb shell input` steps, or with the same test.
- A short screen recording: `adb shell screenrecord --time-limit 8 /sdcard/flow.mp4`, then `adb pull /sdcard/flow.mp4`.

## Desktop app

Use the `agent-desktop` CLI for a native app (macOS, Windows or Linux). Run `agent-desktop skills get desktop` first and follow it. Capture one window:

```bash
agent-desktop list-windows --app <app>
agent-desktop resize-window --app <app> --width 1280 --height 800
agent-desktop screenshot --app <app> "$SCRATCH/shots/settings-before.png"
```

- If the app has more than one window, pass `--window-id` from `list-windows` to both commands.
- To get the same state on both builds, drive the app with the same `agent-desktop` steps: take a snapshot, act on a ref, then take a snapshot again to check.
- A window can show private content from other apps or accounts. Look at the image before you upload it.

## Crop and size

- Crop each image to the part that changed, with a little context around it. A full tablet screen at 2560x1600 is about 5 MB. The input bar alone is about 200 KB.
- Crop the before and after to the same box, so they line up in the table.
- macOS: `sips -c <height> <width> --cropOffset <y> <x> in.png --out out.png`. Or use Python with Pillow.
- Aim for less than about 500 KB per image. For an animation, a GIF or MP4 of a few seconds is enough.

## Look at every image

Open each file and check:

- It shows the state named in its file name and caption.
- It is not blank, still loading, or an error screen (unless that state is the change).
- The before and after differ in the way the PR says, and in no other way.

If a capture fails, say so in "Not tested (and why)". Do not drop the state without a word.
