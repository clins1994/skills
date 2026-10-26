---
name: slack
description: Post to Slack through the Slack MCP server. A post is a channel message with the leads and one thread reply with the details. Slack has no collapsed block, so the thread is the fold. Gives the message syntax, mentions, link previews, and what the connector cannot do (edit, delete). The text comes from clins:post, in the user's languages. Use whenever you write, draft or send a Slack post, an update, or a link to a thread.
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

## Preflight

1. The Slack MCP tools are connected: `slack_send_message`, `slack_send_message_draft`, `slack_search_channels`, `slack_search_users`, `slack_read_thread`. If they are deferred, load them first. If they are missing, tell the user to connect the Slack connector, and stop.
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

## Slack syntax

The MCP message tools take standard Markdown and convert it. Do not write Slack's older mrkdwn (`*bold*`, `~strike~`).

- **No footer and no divider.** The post already shows who sent it, and the connector adds "Sent using" under each message. Slack shows a `---` line as text.
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
4. **Send the channel message** with `slack_send_message` (or `slack_send_message_draft`). Keep the `message_ts` it returns.
5. **Send the thread reply** with `slack_send_message` and `thread_ts` set to that `message_ts`. Leave `reply_broadcast` off.
6. **Give the user the links** to both messages. To link to the post from another channel, use the channel message's link as label text, for example `[this thread](<link>)`.

## Updating a post

You cannot edit a sent message. Write the changed text with `clins:post` ("Updating a post"), check it, and give it to the user to paste over the old message by hand. To add news, reply in the same thread instead.
