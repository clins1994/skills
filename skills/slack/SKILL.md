---
name: slack
description: Post to Slack through the Slack MCP server, or as the user's own bot through a poster command they name. A post is a channel message with the leads and one thread reply with the details. Slack has no collapsed block, so the thread is the fold. Gives the message syntax, mentions, link previews, image and video uploads, and what the connector cannot do (edit, delete). The text comes from clins:post, in the user's languages. Use whenever you write, draft or send a Slack post, an update, or a link to a thread.
user-invocable: true
argument-hint: "[post | reply] [channel, or a message link to reply to] [any language changes]"
---

# /clins:slack — Post to Slack

This skill sends a post to Slack. The text (leads, details, languages, check) comes from [`clins:post`](../post/SKILL.md). Pass any language changes the user asked for through to it.

Slack has no collapsed block. The thread does the same job: the channel shows the leads, and the details wait one click away.

## Rules

- **A sent message is final.** The Slack MCP tools cannot edit or delete a message. Only the user can, by hand. So:
  - Show the full text in chat, and send only after the user approves it. When the user asked you to send in their own words ("post it", "send it to #channel"), that is the approval.
  - If the user wants to look at it in Slack first, use `slack_send_message_draft`. The draft waits in the user's Slack, and the user sends it.
  - Run format tests in the user's own DM, not in a team channel.
- Send each message once. If a tool call fails, read the error before you try again: `is_archived`, for example, never works on retry.
- Do not mention people or groups unless the post needs their action. A mention notifies them.
- A shared file is final too. After `slack_complete_file_upload` shares a file, you cannot share it again or move it. Make sure that the user approved the destination (the channel and the thread) before you share.

## Post as a bot

By default the post goes out through the Slack MCP connector, so Slack shows the user as the author. A user can name a command that posts as a bot (their own Slack app) in a line in an instructions file the agent already reads, for example `~/.claude/CLAUDE.md`:

```
clins:slack poster: <command>
```

Look for the line in the same order as `clins:post` looks for its language line. The command must:

- take `--channel <id>` and an optional `--thread <ts>`,
- read the message as standard Markdown from stdin,
- print the new message's `ts`, and exit with a non-zero code when Slack rejects the message.

With a poster line:

- Send each message with `<command> --channel <id> [--thread <ts>] < message.md`. Do not use `slack_send_message`.
- Slack shows the bot as the author. Do not add a line that says an agent wrote the post.
- The bot can post only in channels where it is a member. If the command fails, show the error to the user. Do not fall back to the connector, because that posts as the user.
- Drafts and file uploads still go through the connector, as the user. Tell the user before you share a file that way.
- Read channels and find IDs with the connector, as before.

## Preflight

1. The Slack MCP tools are connected: `slack_send_message`, `slack_send_message_draft`, `slack_search_channels`, `slack_search_users`, `slack_read_thread`. For media, also `slack_get_file_upload_url` and `slack_complete_file_upload`. If they are deferred, load them first. If they are missing, tell the user to connect the Slack connector, and stop.
2. Find the channel ID with `slack_search_channels`. To post in the user's DM, use the user's own ID as the channel.
3. Read the channel's recent messages (`slack_read_channel`) for its language and tone, unless the user already said how to write there.

## The post

**The channel message** has one lead per language, in the post's language order, and nothing else. A lead can carry its key link as label text: the pull request, the issue or the doc.

```
<japanese lead, with [the key link](url)>

原文：<english lead, with [the key link](url)>
```

**The thread reply** has the details. It is one reply, with one section per language in the same order. Each section starts with a bold title line that ends with its read time:

```
**🇯🇵 詳細** · 読了目安1分

**変更点**
- …

**🇬🇧 More details** · 1 min read

**Changes**
- …
```

A short post (nothing more to say than the leads) is only the channel message, with no thread reply.

## Media

When `clins:post` adds an evidence image or a short video, upload the file and share it in the post. Slack message formatting has no image syntax, so never put `![alt](url)` in the text. `check_post.py` rejects it.

**Where it goes:**

- With the leads, by default. Pick the one file that shows the result most clearly, and share it with the leads as its `initial_comment`. The file and the leads are then one channel message.
- Two files with the leads at most, and only when one cannot show the result, for example a before and an after. The tool shares one file per call, so share the second file directly after the first, with no `initial_comment`. It shows as a second message in the channel.
- Every other file goes in the thread, as one more reply directly after the details reply. A short post has no details reply, so the file is the first thread reply. Do not spam the channel.

**Upload:**

1. Get the exact size in bytes: `stat -f %z shot.png` on macOS, `stat -c %s shot.png` on Linux.
2. Call `slack_get_file_upload_url` with `filename`, `content_length` (that size) and, for an image, `alt_txt` that says what it shows, for example "The Save button, circled in red, far from the form". It returns a file ID and an upload URL.
3. POST the raw bytes to the URL. Put the URL in a shell variable, byte for byte. Do not decode it, encode it or type it again:

   ```bash
   URL='<upload_url>'
   curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$URL" -H "Content-Type: image/png" --data-binary @shot.png
   ```

   Use the file's type: `image/png`, `image/gif`, `video/mp4`. The answer must be `200`. A `401` means that the URL changed on the way or expired (after about 1 hour). Ask for a new URL.
4. Call `slack_complete_file_upload` with `file_id` and `channel_id`. The channel ID is an encoded `C`, `D` or `G` ID, not a name and not a user ID. For your own DM, find the `D` ID with `slack_list_user_channels` and `types="im"`. To put the file in the thread, set `thread_ts` to the channel message's `message_ts`. To put it with the channel message, leave out `thread_ts` and pass the leads as `initial_comment`. A `title` is optional.

**Size:** the Slack API sets no fixed file size, but a workspace can block large files (`file_upload_size_restricted`). Keep an image under about 1 MB and a video to a few seconds, as [`clins:post`](../post/references/evidence.md) says. A 300 KB PNG and a 2.8 MB MP4 uploaded on 2026-10-28.

If an upload fails, send the post without the file and tell the user. Do not paste the file's local path into the post.

## Slack syntax

The MCP message tools take standard Markdown and convert it. Do not write Slack's older mrkdwn (`*bold*`, `~strike~`).

- **No footer and no divider.** The post already shows who sent it, and the connector adds "Sent using" under each message. A bot's message also shows the bot as its author. Slack shows a `---` line as text.
- **No collapsed block.** No `<details>`, no `>>>`.
- **Headings** inside a section are bold lines (`**Changes**`). `#` headings render, but they are large in a chat message.
- **A blank line after every list.** Slack joins a line that comes straight after a list to the list's last item.
- **The "original" label** in japanese and chinese ends with a full-width colon: `原文：`.
- **Mentions:** a person is `<@U123>` (find the ID with `slack_search_users`), a channel is `<#C123>`, a user group is `<!subteam^S123>`.
- **Links:** `[label](url)`. Slack and external links did not show a large preview in our tests. See [`references/behavior.md`](references/behavior.md).
- **Length:** keep each message under 4,000 characters. Slack does not fold a long message reliably, so the channel message must be short by design.

## Steps

1. **Write the text with `clins:post`**: the leads, and the details for the thread. Use the Slack shape above, not a collapsed block.
2. **Check it.** Save the channel message and the reply as two files:

   ```bash
   python3 <post-skill-dir>/scripts/check_post.py --platform slack --langs ja,en --source en message.md reply.md
   python3 <post-skill-dir>/scripts/check_post.py --platform slack --read-time reply.md   # section titles with read times
   ```

   Leave out `reply.md` for a short post.
3. **Show the text to the user** and wait for the approval (see "Rules").
4. **Send the channel message** with `slack_send_message`, or with the poster command when there is a poster line (see "Post as a bot"). Keep the `message_ts`, or the `ts` the command prints.
   - If the post has media, share the lead file with the leads as `initial_comment` in place of `slack_send_message` (see "Media"). The tool returns no `message_ts`, so read the channel with `slack_read_channel` and take the `ts` of the file's message. Share a second lead file, if any, after it.
   - If the user wants a draft, make it with `slack_send_message_draft`, and stop until the user sends it. Then ask for the link to the sent message, and read it with `slack_read_thread` to get its `message_ts`.
5. **Send the thread reply** after the channel message is sent. Use `slack_send_message` with `thread_ts` set to that `message_ts`, or the poster command with `--thread <ts>`. Leave `reply_broadcast` off.
   - Share the other files now, in the thread after this reply (see "Media"). A short post has no thread reply: share the other files as the first thread replies.
6. **Give the user the links** to both messages. To link to the post from another channel, use the channel message's link as label text, for example `[this thread](<link>)`.

## Updating a post

You cannot edit a sent message. Write the changed text with `clins:post` ("Updating a post"), check it, and give it to the user to paste over the old message by hand. To add news, reply in the same thread instead.
