---
name: times
description: Keep your updates in one place of your own, your "times", and keep team channels short. Writes the full post to your times destination. If the team needs to know, it also writes a short pointer in a team channel that links to the post. The destination is one saved line, for example a personal Slack channel, and works with any platform skill. The text comes from clins:post. Use when the user wants to share an update, a learning or something interesting, or asks to "post this to my times".
user-invocable: true
argument-hint: "[what to share] [also point to <team channel>] [any language changes]"
---

# /clins:times — Your updates, in one place

A "times" is a place of your own for updates: what you did, what you learned, what you found interesting. Anyone can read it, and nobody has to. Team channels stay short. If the team needs to know, a team channel gets a pointer to the full post.

This skill owns **where** a post goes. The text comes from [`clins:post`](../post/SKILL.md). The platform skill for the destination owns the syntax and the commands.

## The destination

The destination lives in one line of an instructions file the agent already reads:

```
clins:times: slack #times-alice
```

The first word is the platform, and the rest is the place on it. Look for the line in the same order as `clins:post` looks for its language line: what the user says now, then the repo's `AGENTS.md` or `CLAUDE.md`, then the user's global instructions file.

If there is no line, ask the user where their times is. If the agent has a question tool, use it. Then show the line, save it to the user's global instructions file, and say how to change it: "Saved. To change it, just tell me, for example: move my times to #times-bob."

## Rules

- A post to a team channel notifies people. If the user did not ask for a pointer or agree to one, do not send it.
- Many platforms cannot edit or delete through the agent's tools (Slack is one). Show the text, and send only after the user approves it. When the user asked you to send in their own words, that is the approval.
- Never put a private detail in a times post: secrets, customer data, or anything the user did not want shared. A times is readable by everyone who can see the place.

## Steps

1. **Find the destination** (above), and the platform skill for it: `clins:slack` for `slack`. If that skill is not installed, use the platform's own tools and the closest shape it has, and tell the user.
2. **Write the post with `clins:post`**, in the platform's shape. On Slack, the channel message holds the leads, and one thread reply holds the details.
3. **Send it to the times** through the platform skill. Keep the link to the post.
4. **Pointer.** Do this step only for a pointer the user asked for (see "Rules"). A pointer is a short post in the team channel. It has the leads, with the link to the times post as label text, and no details:

   ```
   <japanese lead>。詳細は[こちらのスレッド](<times post link>)へ。

   原文：<english lead>. Details are in [this thread](<times post link>).
   ```

   Write it with `clins:post` as a short post, and send it through the same platform skill.
5. **Give the user the links** to the times post and to the pointer.

## What goes where

| Kind | Times | Team channel |
|---|---|---|
| An update the team must act on | Full post | Pointer, with the action in the lead |
| An update for the record | Full post | Nothing, or a weekly summary pointer |
| A learning, a tool tip, an interesting find | Full post | Nothing, unless the user asks |
| A question for the team | Nothing | The question itself, as a normal post |
