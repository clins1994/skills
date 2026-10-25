---
name: post
description: The writing format for engineering posts - a short lead for humans, then the full text in a collapsed "More details" block that says how many minutes it takes to read, then a footer. Writes in the user's own languages - a lead language and any other languages under it, saved once as a default and changed per post in plain words ("japanese as well", "only the lead", "swap them"). Asks for the default the first time. Runs a style pass per language, writes the lead last, and checks the result with a bundled script. clins:create-pr, clins:github and clins:linear use it for the text. Use it directly for any other post, or when asked to "write this up", "draft a post", or "translate the post".
user-invocable: true
argument-hint: "[what to write, and any language changes]"
---

# /clins:post — The post format

A person reads the lead. An agent, or a person who wants everything, opens the details. So every post is a short lead, then the full text in a collapsed block.

This skill owns the **text**: format, languages, style and the check. The platform skills own **where it goes**:

- [`clins:create-pr`](../create-pr/SKILL.md): the pull request workflow (range, checks, title, before/after images). It uses this skill for the body.
- [`clins:github`](../github/SKILL.md): GitHub commands and syntax for PR bodies, PR comments, review replies and issues.
- [`clins:linear`](../linear/SKILL.md): issues and comments.

Each one gives the block syntax, the headings and the commands for its platform, and sends you here for the text. For another platform, use the closest collapsible syntax it has.

## Languages

A post has a **lead language**, shown first, and zero or more **other languages** under it. People name languages in plain words ("japanese", "brazilian portuguese", "azerbaijani"). They never need a language code. You map each name to its code, flag and block title.

### The default

The default lives in one line of an instructions file the agent already reads:

```
clins:post languages: lead english; also japanese
```

Look for it in this order, and use the first one you find:

1. What the user says for this post (below).
2. The repo's `AGENTS.md` or `CLAUDE.md`. A team can set its own default there.
3. The user's global instructions file, for example `~/.claude/CLAUDE.md` for Claude Code or `~/.codex/AGENTS.md` for Codex.

### First run

If no default exists, ask before you write. Ask in the language the user writes to you in, so a user never has to read a language they did not choose. Use the agent's question tool with options when it has one, and plain text when it does not. The wording below is an example for a user who writes in english:

1. "Which language should your posts lead with?" Options: **the language the user writes to you in** (the default, here english), and **another language**, where the user types it, for example "azerbaijani".
2. "Add other languages under it?" Options: **no, just the lead**, and **yes**, where the user types them, for example "japanese and portuguese".

Then show the line, save it to the user's global instructions file, and say how to change it, in the same language: "Saved. To change it, just tell me, for example: change my post languages to portuguese and japanese." The saved line uses english language names, so every agent reads it the same way. If the user does not want it saved, use the answer for this post only.

If you cannot ask (CI, or a run with no prompts), use the language of the request, or english if that is not clear, and say so in your result.

### Changes for one post

The user changes the languages in plain words when they call the skill. These change this post only. The saved default changes only when the user says so ("change my default to …"). With the default "lead english; also japanese":

| The user says | Languages for this post |
|---|---|
| nothing | english, then japanese |
| "this time no japanese" or "only the lead" | english |
| "portuguese as well" | english, then japanese and portuguese |
| "japanese and chinese" | english, then japanese and chinese. The lead stays unless the user moves it. |
| "japanese lead, english second" | japanese, then english |
| "swap them" | japanese, then english |
| "use only portuguese" | portuguese |

"Swap" works when there is one other language. With several, ask which one leads.

### Which language is the original

The **source** is the user's default lead language. Write the post there first, and translate every other language from the finished source text.

- Usually the source is also the lead, so the lead is the original.
- If the user puts another language first, the source lead goes second or later, after a label that means "original" in the lead language: `原文:` for japanese and chinese, `Original:` for english and portuguese. This tells readers which text is authoritative.
- If the source is not in this post's languages at all ("use only portuguese" for an english user), the lead language is the source.

## The format

One language:

```
<lead: what it is, and what the reader must do>

---

▸ 🇬🇧 More details · 3 min read   (collapsed: the full text)

🤖 footer
```

Lead english, also japanese:

```
<english lead>

<japanese lead>

---

▸ 🇬🇧 More details · 3 min read   (collapsed: the full english)
▸ 🇯🇵 詳細 · 読了目安3分      (collapsed: the full japanese)

🤖 footer
```

Lead japanese, also english, when english is the source:

```
<japanese lead>

原文: <english lead>

---

▸ 🇯🇵 詳細 · 読了目安3分      (collapsed: the full japanese)
▸ 🇬🇧 More details · 3 min read   (collapsed: the full english)

🤖 footer
```

Block titles: 🇬🇧 More details, 🇯🇵 詳細, 🇨🇳 详细信息, 🇹🇼 詳細資訊, 🇰🇷 자세한 내용, 🇧🇷 Mais detalhes, 🇵🇹 Mais detalhes, 🇪🇸 Más detalles, 🇫🇷 Plus de détails, 🇩🇪 Weitere Details, 🇮🇹 Altri dettagli, 🇮🇳 अधिक विवरण, 🇩🇰 Flere detaljer, 🇦🇿 Ətraflı. For another language, use its flag and translate "More details" in the same short way.

- An @mention line, if any, goes first.
- When the repo's template has its own sections (for example `## Description`, `## Checklist`), keep every one of them. The lead and the blocks go in the first section, under its heading. The other sections follow in the template's order, and the footer comes after them.
- One lead per language, each its own paragraph, in the post's language order. Then one block per language, in the same order.
- A blank line goes above `---`. Without it, Markdown can turn the lead into a heading.
- Every block is collapsed.
- Each block title ends with its read time, after ` · `, so a reader knows the cost before they open it. The script counts it from that block's own text: 200 words a minute, or 500 characters a minute for japanese, chinese, korean and thai, rounded up, at least 1 minute. Run `check_post.py --read-time post.md` to print every title with its time, and copy those titles. Read times: `{n} min read`, `読了目安{n}分`, `阅读约{n}分钟`, `閱讀約{n}分鐘`, `{n}분 분량`, `{n} min de leitura`, `{n} min de lectura`, `{n} min de lecture`, `{n} Min. Lesezeit`, `{n} min di lettura`, `{n} मिनट में पढ़ें`, `{n} min. læsning`, `{n} dəq oxuma`. For another language, translate `{n} min read` in the same short way.
- With more than one language, all blocks say the same thing, with the same headings, lists and code. Edit them together.
- Footer, last. It names the skill the user ran, so a reader knows what to run to get the same result:

  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code) using [clins:<skill>](https://github.com/clins1994/skills/blob/main/skills/<skill>/SKILL.md)
  ```

  `<skill>` is the skill that sent you here (for example `create-pr`, `github` or `linear`), and `post` when the user ran this skill directly. Name only that one skill. It links to the skills it uses.
- **Short post:** when the details add nothing ("Fixed in abc1234. Please review again."), post only the leads. No divider, no block, no footer.
- Anything a bot adds below the footer (for example a review summary) is not yours. Never edit it.

## Steps

1. **Settle the languages:** the default, the user's changes for this post, and the source (above).
2. **Draft the full text in the source language.** Use the platform skill's headings, or the repo's. Facts in: commits, files, numbers, links.
3. **Style pass in the source language.** For english, follow [`references/english-pass.md`](references/english-pass.md), and use the `simple-english` skill in Plain mode for part 1 if it is installed. For any language, if a plain-writing skill for it is installed, use it. Otherwise apply the same ideas: short sentences, concrete words, no filler.
4. **Translate** into each other language, from the finished source text. Never from a draft, and never from another translation. Short sentences, no translated tone, and the same headings, lists and code as the source. One translation per term. Follow each language's own conventions: its punctuation, how it mixes in latin text, and its usual style guide (for japanese, the JTF style guide: `、` and `。`, half-width letters and digits, no space between full-width and half-width text). If english is a translation, run the english pass on it too.
5. **Write the leads last.** One or two sentences in the source language: what this is, and what the reader must do. If there is nothing to do, say what changed. No preamble ("This PR...", "I wanted to..."). Then translate the lead.
6. **Assemble** in the format above, with the platform's block syntax. Get each block's read time from `check_post.py --read-time`.
7. **Check** (below).

Never change code, identifiers, commands, file paths, quoted errors, product names, numbers, or text quoted from another person. Copy quotes, logs and bot output unchanged.

## Updating a post

1. Change the source language first, then the same paragraphs in every other language. Never edit only one language.
2. Reread the leads. Rewrite them if a fact or the action changed.
3. Update the read time in each block title (`check_post.py --read-time`).
4. Leave other people's text, and everything below the footer, as it is.
5. Check again. The platform skill says how to fetch and save the text.

## Check before you post

The script takes language codes. Pass the post's languages in order, lead first, and the source when it is not the lead:

```bash
python3 <skill-dir>/scripts/check_post.py --platform github post.md                          # english only
python3 <skill-dir>/scripts/check_post.py --platform github --langs en,ja post.md            # lead english, also japanese
python3 <skill-dir>/scripts/check_post.py --platform linear --langs ja,en --source en post.md # lead japanese, english is the original
python3 <skill-dir>/scripts/check_post.py --langs pt --title "pt=🇧🇷 Mais detalhes" post.md     # set a title the script does not know
python3 <skill-dir>/scripts/check_post.py --read-time post.md                                # print each block title with its read time
```

Add `--skill <name>` to require that skill in the footer. Add `--template` when the post follows a repo template whose heading comes before the lead. It checks:

- one lead per language, the "original" label when the source is not the lead, and a lead of at most two sentences
- the divider, the block titles and their order, that blocks are collapsed and closed, and that no `<summary>` holds a heading
- the read time after each block title, counted from that block's text
- the footer: a `clins:<skill>` name that matches its link
- english style on english text: em-dash, semicolon, curly quote, contraction, weak modal
- sentence length in every language: 30 words, or 80 characters for languages written without spaces (japanese, chinese, thai). A link counts its text, not its URL.
- no space between full-width and half-width text, for languages whose style guide asks for it (japanese)
- that every other block has the same headings, list items and code as the source block
- `@greptileai`, and the other platform's block syntax

It ignores everything below the footer. Fix every error and run it again. For a language without a built-in title or label, pass `--title code=...`, `--label code=...` and `--read code=...` (with `{n}` for the minutes, for example `--read "xx={n} min"`).

The script cannot check meaning. Also make sure that a reader of the lead alone knows what to do, and that the post does not end with "Let me know" or a recap.

## Dependencies

None are required. The rules this skill needs are in `references/`. These public skills make it better when they are installed:

- [`simple-english`](https://github.com/AminBlg/SimpleEnglish) (step 3, Plain mode, for english): `npx skills add AminBlg/SimpleEnglish`
- [`i-have-adhd`](https://github.com/ayghri/i-have-adhd): the "lead with the next action" rule in step 5 comes from it.
- [`unslop`](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop) from `pstack`: part 2 of the english pass is copied from it, because agents cannot call it.
