# Evidence image

Use what the environment gives you. These are examples, not requirements. If none of them works, leave the image out.

## Capture

- Android (device or emulator): `adb -s <serial> exec-out screencap -p > shot.png`. Use `exec-out`, because `adb shell` breaks the PNG.
- iOS simulator: `xcrun simctl io booted screenshot shot.png`.
- Web: the browser tool's screenshot, for example `agent-browser screenshot shot.png`.
- Short video: `adb shell screenrecord --time-limit 5 /sdcard/bug.mp4`, then `adb pull`. Make a GIF with `ffmpeg -i bug.mp4 -vf "fps=8,scale=800:-1" bug.gif`.

## Mark the problem

Find the element's box. Do not guess it from the image.

- Android: `adb exec-out uiautomator dump /dev/tty` prints `bounds="[x1,y1][x2,y2]"` for each view. A web view inside the app often shows only its outer box.
- Web: `document.querySelector("<selector>").getBoundingClientRect()`. Multiply by `devicePixelRatio` if the screenshot is larger than the viewport.

Draw an ellipse a little larger than the box (ImageMagick 7, center and radii):

```bash
magick shot.png -fill none -stroke red -strokewidth 6 \
  -draw "ellipse <cx>,<cy> <rx>,<ry> 0,360" marked.png
```

Python with Pillow works too: `ImageDraw.Draw(img).ellipse(box, outline="red", width=6)`.

## Size

- Crop to the problem with some context around it: `magick marked.png -crop <w>x<h>+<x>+<y> +repage out.png`.
- Keep it under about 1 MB. A full tablet screen is about 5 MB. `-resize '1200x1200>'` helps.
- Open the result and look at it. The mark must sit on the problem, and the screen must not be blank or still loading.

## Place it

Directly after the leads, before the divider, with alt text that says what it shows, for example `![The Save button, circled in red, far from the form](<url>)`. The platform skill says how to upload the file and get the URL. If it has no upload step (Slack, for now), leave the image out.
