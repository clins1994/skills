---
name: post
description: The writing format for engineering posts - a short lead for humans, then the full text in a collapsed "More details" block, then a footer. English by default. With `--lang <code>` (for example `ja`), a translated lead and one collapsed block per language. Runs an English style pass, writes the lead last, and checks the result with a bundled script. clins:create-pr, clins:github and clins:linear use it for the text. Use it directly for any other post, or when asked to "write this up", "draft a post", or "translate the post".
user-invocable: true
argument-hint: "[--lang <code>] [what to write]"
---

# /clins:post — The post format

A person reads the lead. An agent, or a person who wants everything, opens the details. So every post is a short lead, then the full text in a collapsed block.

This skill owns the **text**: format, language, style and the check. The platform skills own **where it goes**:

- [`clins:create-pr`](../create-pr/SKILL.md): the pull request workflow (range, checks, title, before/after images). It uses this skill for the body.
- [`clins:github`](../github/SKILL.md): GitHub commands and syntax for PR bodies, PR comments, review replies and issues.
- [`clins:linear`](../linear/SKILL.md): issues and comments.

Each one gives the block syntax, the headings and the commands for its platform, and sends you here for the text. For another platform, use the closest collapsible syntax it has.

## Language

- No `--lang`: English only.
- `--lang <code>`: the lead in that language first, then the English lead after a label that means "original" (`原文:` for Japanese), then one collapsed block per language. The English is the original. You write it first and translate from it.
- If the repo's `AGENTS.md`/`CLAUDE.md` sets a language, use it when `--lang` is not given.

## The format

English only:

```
<lead: what it is, and what the reader must do>

---

▸ 🇬🇧 More details   (collapsed: the full text)

🤖 footer
```

With `--lang ja`:

```
<Japanese lead>

原文: <English lead>

---

▸ 🇯🇵 詳細   (collapsed: the full Japanese)
▸ 🇬🇧 More details  (collapsed: the full English)

🤖 footer
```

For another language, use its flag, and translate the block title and the "original" label in the same way.

- An @mention line, if any, goes first.
- A blank line goes above `---`. Without it, Markdown can turn the lead into a heading.
- Every block is collapsed.
- With two languages, both blocks say the same thing, with the same headings, lists and code. Edit them together.
- Footer, last. It names the skill the user ran, so a reader knows what to run to get the same result:

  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code) using [clins:<skill>](https://github.com/clins1994/skills/blob/main/skills/<skill>/SKILL.md)
  ```

  `<skill>` is `create-pr`, `github` or `linear` when one of them sent you here, and `post` when the user ran this skill directly. Name only that one skill. It links to the skills it uses.
- **Short post:** when the details add nothing ("Fixed in abc1234. Please review again."), post only the lead (or both leads). No divider, no block, no footer.
- Anything a bot adds below the footer (for example a review summary) is not yours. Never edit it.

## Steps

1. **Draft the full English.** Use the platform skill's headings, or the repo's. Facts in: commits, files, numbers, links.
2. **English pass.** Follow [`references/english-pass.md`](references/english-pass.md). If the `simple-english` skill is installed, use it in Plain mode for part 1.
3. **Translate** (only with `--lang`). From the finished English, never from the draft. Short sentences, no translated tone, and the same headings, lists and code as the English. One translation per English term. If a plain-writing skill for that language is installed, use it. For Japanese, follow the JTF style guide: `、` and `。`, half-width letters and digits, and no space between full-width and half-width text.
4. **Write the lead last.** One or two sentences: what this is, and what the reader must do. If there is nothing to do, say what changed. No preamble ("This PR...", "I wanted to..."). With `--lang`, translate the lead too.
5. **Assemble** in the format above, with the platform's block syntax.
6. **Check** (below).

Never change code, identifiers, commands, file paths, quoted errors, product names, numbers, or text quoted from another person. Copy quotes, logs and bot output unchanged.

## Updating a post

1. Change the English first, then the same paragraphs in the other language. Never edit only one language.
2. Reread the lead. Rewrite it if a fact or the action changed.
3. Leave other people's text, and everything below the footer, as it is.
4. Check again. The platform skill says how to fetch and save the text.

## Check before you post

```bash
python3 <skill-dir>/scripts/check_post.py --platform github post.md            # English only
python3 <skill-dir>/scripts/check_post.py --platform linear --lang ja post.md   # two languages
python3 <skill-dir>/scripts/check_post.py --lang pt --title "🇧🇷 Mais detalhes" --label "Original" post.md
```

Add `--skill <name>` to require that skill in the footer. It checks the lead, the divider, the block titles and order, that blocks are collapsed and closed, that no `<summary>` holds a heading, the footer (a `clins:<skill>` name that matches its link), English style (em-dash, semicolon, curly quote, contraction, weak modal), `@greptileai`, the other platform's block syntax, and, with two languages, that both blocks have the same structure (for Japanese, also 80 characters per sentence and no space between full-width and half-width text). It ignores everything below the footer. Fix every error and run it again.

The script cannot check meaning. Also make sure that a reader of the lead alone knows what to do, and that the post does not end with "Let me know" or a recap.

## Dependencies

None are required. The rules this skill needs are in `references/`. These public skills make it better when they are installed:

- [`simple-english`](https://github.com/AminBlg/SimpleEnglish) (step 2, Plain mode): `npx skills add AminBlg/SimpleEnglish`
- [`i-have-adhd`](https://github.com/ayghri/i-have-adhd): the "lead with the next action" rule in step 4 comes from it.
- [`unslop`](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop) from `pstack`: part 2 of the English pass is copied from it, because agents cannot call it.
