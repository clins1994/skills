---
name: post
description: Write or update an engineering post (GitHub PR description or comment, Linear issue or comment) as a short lead for humans plus a collapsed "More details (for agents)" block. English by default. Pass a language (for example `--lang ja`) to add a second language, with a translated lead and a collapsed block per language. Runs an English style pass, writes the lead last, and checks the post with a bundled script. For a PR description, start with clins:pr, which adds before/after images and uses this skill for the text. Use whenever you write or edit one of these posts, or when asked to "post", "write the PR description", "reply on the PR", or "file a Linear issue".
user-invocable: true
argument-hint: "[issue | pr | comment] [--lang <code>] [URL or ID to update]"
---

# /clins:post — Engineering posts

A person reads the lead. An agent (or a person who wants everything) opens the details. So every post is a short lead, then the full text in a collapsed block.

**For a PR description, start with [`clins:pr`](../pr/SKILL.md).** It adds the images and uses this skill for the text.

## Language

- No `--lang`: English only.
- `--lang <code>` (for example `ja`): the lead in that language first, then the English lead after a label that means "original" (`原文:` for Japanese), then one collapsed block per language. The English is always the original. You write it first and translate from it.
- If the repo's `AGENTS.md`/`CLAUDE.md` sets a language, use it when `--lang` is not given.

## The format

English only:

```
<lead: what it is, and what the reader must do>

---

▸ 🇬🇧 More details (for agents)   (collapsed: the full text)

🤖 footer
```

With `--lang ja`:

```
<Japanese lead>

原文: <English lead>

---

▸ 🇯🇵 詳細（エージェント向け）   (collapsed: the full Japanese)
▸ 🇬🇧 More details (for agents)  (collapsed: the full English)

🤖 footer
```

For another language, use its flag and translate the title and the "original" label the same way, then pass them to the check script with `--title` and `--label`.

- A blank line above `---`. Without it, GitHub turns the lead into a heading.
- Every block is collapsed. Never `<details open>`.
- With two languages, both blocks say the same thing, with the same headings, lists and code. Edit them together.
- GitHub block: `<details><summary><h3>🇬🇧 More details (for agents)</h3></summary>`, a blank line, the content, a blank line, `</details>`. The blank line after `</summary>` is required, or GitHub shows raw Markdown.
- Linear block: `>>> 🇬🇧 More details (for agents)`, a blank line, the content, a blank line, `>>>`. Never mix the two syntaxes.
- Footer, after the blocks: `🤖 Generated with [Claude Code](https://claude.com/claude-code) using [clins:post](https://github.com/clins1994/skills/blob/main/skills/post/SKILL.md)`
- Short post: when the details add nothing ("Fixed in abc1234. Please review again."), post only the lead (or both leads). No divider, no block, no footer.

## Sections inside the details

Use the repo's headings if `AGENTS.md`, `CLAUDE.md` or `.github/pull_request_template.md` defines them. Otherwise:

- PR description: Summary, Why, Changes, How it was tested, Not tested (and why), Screenshots (UI only), Related.
- Linear issue: Context, Work, Done when. Add To decide or Sub-issues only when they have content.
- Comment: no headings unless the reply is long.

With `--lang ja`, the Japanese headings are 概要, なぜ, 変更点, 確かめたこと, 確かめていないこと・理由, スクショ, 関連, and 背景, やること, 完了条件.

## Steps

1. **Draft the full English.** Facts in: commits, files, numbers, links.
2. **English pass.** Follow [`references/english-pass.md`](references/english-pass.md). If the `simple-english` skill is installed, use it in Plain mode for part 1.
3. **Translate** (only with `--lang`). From the finished English, never from the draft. Short sentences, no translated tone, and the same headings, lists and code as the English. Keep terms fixed: one translation per English term. If a plain-writing skill for that language is installed, use it. For Japanese, follow the JTF style guide: `、` and `。`, half-width letters and digits, and no space between full-width and half-width text.
4. **Write the lead last.** One or two sentences: what this is, and what the reader must do. If there is nothing to do, say what changed. No preamble ("This PR...", "I wanted to..."). With `--lang`, translate the lead too.
5. **Assemble** in the format above. An @mention line, if any, goes first.
6. **Check** (below).

Never change code, identifiers, commands, file paths, quoted errors, product names, numbers, or text quoted from another person. Copy quotes, logs and bot output unchanged.

## Dependencies

None are required. The rules this skill needs are in `references/`. These public skills make it better when they are installed:

- [`simple-english`](https://github.com/AminBlg/SimpleEnglish) (step 2, Plain mode): `npx skills add AminBlg/SimpleEnglish`
- [`i-have-adhd`](https://github.com/ayghri/i-have-adhd): the "lead with the next action" rule in step 4 comes from it.
- [`unslop`](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop) from `pstack`: part 2 of the English pass is copied from it, because agents cannot call it.

## Check before you post

```bash
python3 <skill-dir>/scripts/check_post.py --platform github post.md            # English only
python3 <skill-dir>/scripts/check_post.py --platform linear --lang ja post.md   # two languages
```

It checks the lead, the divider, the block titles and order, collapsed and closed blocks, the footer, English style (em-dash, semicolon, curly quote, contraction, weak modal), `@greptileai`, the other platform's syntax, and, with two languages, that both blocks have the same structure (and, for Japanese, 80 characters per sentence and no space between full-width and half-width text). It ignores everything below the footer (review-bot sections). Fix every error and run it again.

The script cannot check meaning. Also make sure that a reader of the lead alone knows what to do, and that the post does not end with "Let me know" or a recap.

## Updating a post

1. Get the current text: `gh pr view <n> --json body -q .body`, `gh api repos/<owner>/<repo>/issues/comments/<id> -q .body`, or Linear `get_issue` / `list_comments`.
2. Change the English first, then the same paragraphs in the other language. Never edit only one language.
3. Reread the lead. Rewrite it if a fact or the action changed.
4. Leave other people's text and everything below the footer as it is.
5. Linear descriptions turn `ENG-123` into `<issue ...>` tags. Update with `save_issue` and `patch` anchors copied from `get_issue`, not a full rewrite.
6. Check, then post.

## Posting

- PR description: [`clins:pr`](../pr/SKILL.md).
- PR comment: `gh pr comment <n> --body-file post.md`. Edit: `gh api -X PATCH repos/<owner>/<repo>/issues/comments/<id> -F body=@post.md`.
- Linear: `save_issue` (description) or `save_comment`, with real newlines, not `\n`.
- Never put `@greptileai` in a post. A comment meant only for a bot is written as the bot expects, outside this skill.
