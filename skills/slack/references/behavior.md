# What Slack does and does not do

The Slack docs answer most format questions. The rest comes from test posts sent through the Slack MCP connector on 2026-10-26 and 2026-10-28, and seen in the Slack desktop app. If the connector or Slack changes, test again.

| Behavior | Result | Source |
|---|---|---|
| A collapsed block in a message (`<details>`, a spoiler) | Not possible. Message formatting has no such syntax. | [Formatting message text](https://docs.slack.dev/messaging/formatting-message-text), [markdown block](https://docs.slack.dev/reference/block-kit/blocks/markdown-block) |
| A thread reply as the fold | Works. A reply with `thread_ts` stays out of the channel unless `reply_broadcast` is `true`, and the default is `false`. | [`chat.postMessage`](https://docs.slack.dev/reference/methods/chat.postMessage) |
| A long message folds with "Show more" | Not by line count: 40 short lines showed in full on desktop. Do not rely on it. | Test |
| A raw link to a Slack message, same channel | A small chip, such as "<name> in #<channel>". No message text. | Test |
| A raw link to a Slack message, other channel | A small chip, such as "<name> in #<channel>". No message text. | Test |
| A link to a deleted message | A "Private message" chip. | Test |
| A link with label text, `[label](url)` | Plain link text. No preview. | Test |
| A raw external URL | The connector saves it with a label equal to the URL without `https://`. It shows as a small link chip. Slack never unfurls a link whose label is the full URL without its protocol. | Test, [unfurling](https://docs.slack.dev/messaging/unfurling-links-in-messages) |
| Turn off previews per message | The API has `unfurl_links` and `unfurl_media`. The MCP tool exposes only `unfurl_app_links`. | [`chat.postMessage`](https://docs.slack.dev/reference/methods/chat.postMessage) |
| Remove a preview by hand | On desktop: hover over the preview and remove it. Not on mobile. | [Help center](https://slack.com/help/articles/204399343-Share-links-and-set-preview-preferences) |
| Turn off previews for yourself | Preferences > Messages & media. It changes only your own view. | [Help center](https://slack.com/help/articles/204399343-Share-links-and-set-preview-preferences) |
| "Sent using @Claude" | The connector adds it under every message it sends. No setting to turn it off was found. | Test |
| A line straight after a list | Joined to the list's last item in a draft. Put a blank line after every list. | Test |
| Edit or delete through the MCP tools | Not possible. The API's `chat.delete` exists, but the connector has no tool for it. | MCP tools, [`chat.delete`](https://docs.slack.dev/reference/methods/chat.delete) |
| An image in the text, `![alt](url)` | Slack message formatting has no image syntax. Do not rely on it. Upload the file instead. | [Formatting message text](https://docs.slack.dev/messaging/formatting-message-text) |
| Upload a file through the MCP tools | Works: `slack_get_file_upload_url`, a POST of the raw bytes with `curl`, then `slack_complete_file_upload`. A 300 KB PNG and a 2.8 MB MP4 went into a thread on 2026-10-28. | Test, [`files.getUploadURLExternal`](https://docs.slack.dev/reference/methods/files.getUploadURLExternal) |
| File size limit | The API docs give no fixed limit. A workspace can block large files (`file_upload_size_restricted`), and a free workspace stops at 5 GB of files. | [`files.getUploadURLExternal`](https://docs.slack.dev/reference/methods/files.getUploadURLExternal) |
| Share a file again, or move it | Not possible after `slack_complete_file_upload` shares it. Use the file link it returns to point to it. | MCP tools |
| Message length | Keep `text` under 4,000 characters. Slack truncates above 40,000. | [`chat.postMessage`](https://docs.slack.dev/reference/methods/chat.postMessage) |

These results cover messages sent through the connector. A message the user types in the Slack app can behave differently: the composer can show a preview, and the user removes it with ×.
