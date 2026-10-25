#!/usr/bin/env python3
"""Check a post (PR description, issue or comment) before you send it.

    python3 check_post.py --platform github post.md
    python3 check_post.py --platform github --langs en,ja post.md
    python3 check_post.py --platform linear --langs ja,en --source en post.md
    python3 check_post.py --langs pt --title "pt=🇧🇷 Mais detalhes" post.md
    python3 check_post.py --read-time post.md   # print each block's read time and stop
    gh pr view 12 --json body -q .body | python3 check_post.py -

Every language gets a sentence-length check. English text also gets the english style
rules, and japanese text the JTF spacing rule.

--langs lists the post's languages in order, lead first (default: en).
--source is the language the post was written in (default: the lead). When
the source is not the lead, its lead comes after the lead language's
"original" label, for example "原文:".

Exit code 1 means at least one error. Text below the footer is not checked:
review bots (for example Greptile) add their own sections there.
"""
from __future__ import annotations

import argparse
import re
import sys

# Language code: (block title, "original" label, read time). {n} is the minutes.
KNOWN = {
    "en": ("🇬🇧 More details", "Original", "{n} min read"),
    "ja": ("🇯🇵 詳細", "原文", "読了目安{n}分"),
    "zh": ("🇨🇳 详细信息", "原文", "阅读约{n}分钟"),
    "zh-CN": ("🇨🇳 详细信息", "原文", "阅读约{n}分钟"),
    "zh-TW": ("🇹🇼 詳細資訊", "原文", "閱讀約{n}分鐘"),
    "ko": ("🇰🇷 자세한 내용", "원문", "{n}분 분량"),
    "pt": ("🇧🇷 Mais detalhes", "Original", "{n} min de leitura"),
    "pt-BR": ("🇧🇷 Mais detalhes", "Original", "{n} min de leitura"),
    "pt-PT": ("🇵🇹 Mais detalhes", "Original", "{n} min de leitura"),
    "es": ("🇪🇸 Más detalles", "Original", "{n} min de lectura"),
    "fr": ("🇫🇷 Plus de détails", "Original", "{n} min de lecture"),
    "de": ("🇩🇪 Weitere Details", "Original", "{n} Min. Lesezeit"),
    "it": ("🇮🇹 Altri dettagli", "Originale", "{n} min di lettura"),
    "hi": ("🇮🇳 अधिक विवरण", "मूल", "{n} मिनट में पढ़ें"),
    "da": ("🇩🇰 Flere detaljer", "Original", "{n} min. læsning"),
    "az": ("🇦🇿 Ətraflı", "Orijinal", "{n} dəq oxuma"),
}
EN_TITLE = KNOWN["en"][0]


def footer(skill: str = "post") -> str:
    return ("🤖 Generated with [Claude Code](https://claude.com/claude-code) using "
            f"[clins:{skill}](https://github.com/clins1994/skills/blob/main/skills/{skill}/SKILL.md)")


FOOTER = footer()
FOOTER_LINE = re.compile(r"^🤖 Generated with \[Claude Code\]\(https://claude\.com/claude-code\) using "
                         r"\[clins:([a-z0-9-]+)\]\(https://github\.com/clins1994/skills/blob/main/skills/([a-z0-9-]+)/SKILL\.md\)$",
                         re.M)
CJK = "぀-ヿ㐀-鿿！-｠"
# Sentence ends: latin punctuation before a space, and full stops that need no space
# (CJK 。！？ and the devanagari danda । used in hindi).
SENTENCE_END = r"(?<=[.!?])\s+|(?<=[。！？])|(?<=[।॥])\s*"
# Sentence length limits for every language. Languages written without spaces between
# words count characters; the others count words.
NO_SPACES = {"ja", "zh", "th"}
CHAR_LIMIT = 80
WORD_LIMIT = 30
# Languages whose style guide puts no space between full-width and half-width text
# (for japanese, the JTF style guide). Chinese guides differ, so it is not here.
TIGHT_MIX = {"ja"}
# Read time: 200 words a minute (adults read english non-fiction at about 238, Brysbaert 2019,
# and technical text is slower), and 500 characters a minute for text without spaces
# (Medium's rate for chinese, japanese and korean, used for thai too). Rounded up, at least 1 minute.
WPM = 200
CPM = 500
WIDE = "぀-ヿ㐀-鿿가-힯฀-๿"
READ_SEP = " · "

GITHUB = re.compile(r"<details[^>]*>\s*<summary>(?P<t>.*?)</summary>\n\n(?P<b>.*?)\n</details>", re.S)
LINEAR = re.compile(r"^>>> (?P<t>[^\n]+)\n(?P<b>.*?)\n>>>$", re.S | re.M)
EN_STYLE = [
    (r"—", "em-dash"),
    (r";", "semicolon"),
    (r"[“”‘’]", "curly quote"),
    (r"\b(should|would|might|could|may)\b", "weak modal (use can, will, must)"),
    (r"\b\w+n't\b|\b(it|that|there|we|you|they)'(s|re|ll|ve|d)\b", "contraction"),
]


def no_code(s: str) -> str:
    return re.sub(r"`[^`]*`", "`x`", s)


def prose(text: str):
    """Lines that are prose: not code, tables, headings, HTML or quotes."""
    fence = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s or s.startswith(("|", "#", "<", ">", "![")):
            continue
        yield no_code(re.sub(r"^(?:[-*+]|\d+\.)\s+", "", s))


def shape(body: str):
    return {"headings": len(re.findall(r"^#{1,6} ", body, re.M)),
            "list items": len(re.findall(r"^\s*(?:[-*+]|\d+\.) ", body, re.M)),
            "code fences": len(re.findall(r"^```", body, re.M))}


def read_minutes(body: str) -> int:
    """Minutes to read a block: what the reader sees, without URLs, HTML or Markdown marks."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Strip HTML tags only outside code, and never across lines: code such as `a < b` is read.
    parts = re.split(r"(^```.*?^```|`[^`\n]*`)", text, flags=re.S | re.M)
    text = "".join(p if i % 2 else re.sub(r"</?[A-Za-z][^<>\n]*>", " ", p) for i, p in enumerate(parts))
    text = re.sub(r"https?://\S+", " ", text)
    chars = len(re.findall(f"[{WIDE}]", text))
    words = [w for w in re.sub(f"[{WIDE}]", " ", text).split() if re.search(r"\w", w)]
    return max(1, -(-(chars * WPM + len(words) * CPM) // (WPM * CPM)))


def summary_lines(text: str, titles: dict[str, str] | None = None, reads: dict[str, str] | None = None):
    """Each block's summary line, "<title> · <read time>", as check() wants it."""
    titles, reads = titles or {}, reads or {}
    phrase = {}
    for code in [*KNOWN, *titles, *reads]:
        title = titles.get(code) or KNOWN.get(code, (None,) * 3)[0]
        read = reads.get(code) or KNOWN.get(code, (None,) * 3)[2]
        if title and read:
            phrase[title] = read
    for rx in (GITHUB, LINEAR):
        for m in rx.finditer(text):
            title = re.sub(r"<[^>]+>", "", m["t"]).strip().partition(READ_SEP)[0]
            yield f"{title}{READ_SEP}{phrase.get(title, '{n} min').format(n=read_minutes(m['b']))}"


def base(lang: str) -> str:
    return lang.split("-")[0]


def style(lang: str, lines) -> list[str]:
    err = []
    for line in lines:
        if base(lang) == "en":
            for pat, why in EN_STYLE:
                if re.search(pat, line, re.I):
                    err.append(f"English {why}: {line[:50]}…")
        # A reader sees a link's text, not its URL, so only the text counts toward the length.
        shown = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
        for sent in re.split(SENTENCE_END, shown):
            if base(lang) in NO_SPACES:
                if len(sent.strip()) > CHAR_LIMIT:
                    err.append(f"Sentence over {CHAR_LIMIT} characters ({lang}): {sent.strip()[:40]}…")
            elif len(sent.split()) > WORD_LIMIT:
                err.append(f"Sentence over {WORD_LIMIT} words ({lang}): {sent.strip()[:50]}…")
        if base(lang) in TIGHT_MIX and re.search(rf"[{CJK}] [A-Za-z0-9]|[A-Za-z0-9] [{CJK}]", line):
            err.append(f"Space between full-width and half-width text ({lang}): {line[:40]}…")
    return err


def check(text: str, platform: str | None, langs: list[str] | None = None, source: str | None = None,
          titles: dict[str, str] | None = None, labels: dict[str, str] | None = None,
          skill: str | None = None, template: bool = False, reads: dict[str, str] | None = None):
    err: list[str] = []
    langs = langs or ["en"]
    source = source or langs[0]
    titles, labels, reads = titles or {}, labels or {}, reads or {}
    if len(set(langs)) != len(langs):
        return [f"A language appears twice in --langs {','.join(langs)}."]
    want_titles = []
    for lang in langs:
        t = titles.get(lang) or KNOWN.get(lang, (None,) * 3)[0]
        if not t:
            return [f"No built-in title for {lang}. Pass --title {lang}=..."]
        if "{n}" not in (reads.get(lang) or KNOWN.get(lang, (None,) * 3)[2] or ""):
            return [f"No built-in read time for {lang}. Pass --read {lang}=... with {{n}} for the minutes."]
        want_titles.append(t)
    label = None
    if source in langs and source != langs[0]:
        label = labels.get(langs[0]) or KNOWN.get(langs[0], (None,) * 3)[1]
        if not label:
            return [f"No built-in 'original' label for {langs[0]}. Pass --label {langs[0]}=..."]
    foot = FOOTER_LINE.search(text)

    if "@greptileai" in text:
        err.append("The post contains @greptileai.")
    if re.search(r"<details\s+open", text):
        err.append("A block is open (<details open>). Every block must be collapsed.")
    if re.search(r"<summary>\s*<h[1-6]", text):
        err.append("A heading in <summary> doubles the gap under the divider. Use <b> instead.")
    if platform == "github" and LINEAR.search(text):
        err.append("Linear block syntax (>>>) in a GitHub post.")
    if platform == "linear" and GITHUB.search(text):
        err.append("GitHub block syntax (<details>) in a Linear post.")

    stripped = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
    if len(re.findall(r"<details[\s>]", stripped)) != stripped.count("</details>"):
        err.append("A <details> block is not closed.")
    if len(re.findall(r"^>>>", stripped, re.M)) != 2 * len(LINEAR.findall(stripped)):
        err.append("A >>> block is not closed.")

    # (position, title, read time, body). The summary line is "<title> · <read time>".
    blocks = sorted([(m.start(), *re.sub(r"<[^>]+>", "", m["t"]).strip().partition(READ_SEP)[::2], m["b"])
                     for rx in (GITHUB, LINEAR) for m in rx.finditer(text)])
    head = text[: blocks[0][0]] if blocks else text
    lines = head.strip().split("\n")
    lines = lines[1:] if lines and lines[0].startswith("@") else lines
    if template:  # The repo's PR template opens with its own heading, such as "## Description".
        while lines and (lines[0].startswith("#") or not lines[0].strip()):
            lines = lines[1:]

    # Leads: one paragraph per language, in order.
    paras = re.split(r"\n\s*\n", "\n".join(lines).strip())
    paras = [p.strip() for p in paras if p.strip() and p.strip() != "---" and not p.startswith(("|", "!["))]
    if not paras or paras[0].startswith("#"):
        err.append("The post must start with a lead sentence, not a heading.")
        return err
    if len(paras) < len(langs):
        err.append(f"Expected one lead per language ({', '.join(langs)}), found {len(paras)}.")
        return err
    leads = dict(zip(langs, paras))
    if label:
        if not leads[source].startswith(f"{label}:"):
            err.append(f"The {source} lead is the original. Start it with '{label}:'.")
        else:
            leads[source] = leads[source][len(label) + 1:].strip()
            if not leads[source]:
                err.append(f"The '{label}:' line is empty.")
    if len(re.findall(r"[.!?。！？।](?:\s|$)|[。！？।](?=\S)", no_code(leads[source]))) > 2:
        err.append("The lead is longer than two sentences. Move detail into the block.")

    # Divider, blocks, footer.
    if blocks:
        if "---" not in (l.strip() for l in lines):
            err.append("Put a divider (---) between the lead and the blocks.")
        else:
            i = [l.strip() for l in lines].index("---")
            if i > 0 and lines[i - 1].strip():
                err.append("Put a blank line above ---, or GitHub makes the lead a heading.")
        found = [b[1] for b in blocks]
        if found != want_titles:
            err.append(f"Expected the block titles {want_titles}, found {found}.")
        for lang, t in zip(langs, want_titles):
            for _, title, read, body in blocks:
                want = (reads.get(lang) or KNOWN[lang][2]).format(n=read_minutes(body))
                if title == t and read.strip() != want:
                    err.append(f"Put the read time after the title: '{t}{READ_SEP}{want}'"
                               f"{f', not {read!r}' if read else ''}.")
        if not foot:
            err.append("The footer is missing or changed. Copy it from SKILL.md.")
        elif foot[1] != foot[2]:
            err.append(f"The footer names clins:{foot[1]} but links to skills/{foot[2]}.")
        elif skill and foot[1] != skill:
            err.append(f"The footer names clins:{foot[1]}. This post comes from clins:{skill}.")
    elif "---" in (l.strip() for l in lines) or foot:
        err.append("A short post (no block) has no divider and no footer.")

    # Style per language, and every block shaped like the source block.
    bodies = {lang: next((b[3] for b in blocks if b[1] == t), "") for lang, t in zip(langs, want_titles)}
    for lang in langs:
        err += style(lang, [no_code(leads[lang]), *prose(bodies[lang])])
    src = bodies.get(source, "")
    for lang in langs:
        if lang != source and bodies[lang] and src:
            a, b = shape(bodies[lang]), shape(src)
            for k in a:
                if a[k] != b[k]:
                    err.append(f"Different number of {k}: {lang} {a[k]}, {source} {b[k]}.")
    return err


def pairs(values: list[str], flag: str) -> dict[str, str]:
    out = {}
    for v in values:
        code, sep, rest = v.partition("=")
        if not sep:
            sys.exit(f"{flag} takes code=value, for example {flag} pt=…")
        out[code.strip()] = rest.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="post file, or - for stdin")
    ap.add_argument("--platform", choices=("github", "linear"))
    ap.add_argument("--langs", default="en", help="language codes in order, lead first, for example en,ja")
    ap.add_argument("--source", help="the language the post was written in (default: the lead)")
    ap.add_argument("--title", action="append", default=[], help="block title for a language, code=title")
    ap.add_argument("--label", action="append", default=[], help="'original' label in a language, code=label")
    ap.add_argument("--read", action="append", default=[],
                    help="read time in a language, code=text with {n} for the minutes, for example pt={n} min de leitura")
    ap.add_argument("--skill", help="the skill the footer must name, for example create-pr")
    ap.add_argument("--read-time", action="store_true",
                    help="print each block's title with its read time, for the summary line, and stop")
    ap.add_argument("--template", action="store_true",
                    help="the post follows a repo template whose heading comes before the lead")
    a = ap.parse_args()
    text = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8").read()
    text = re.sub(r"\]\(<([^>\s]+)>\)", r"](\1)", text.replace("\r\n", "\n"))  # Linear links
    foot = FOOTER_LINE.search(text)
    if foot:
        text = text[: foot.end()] + "\n"  # Bot sections below the footer are not ours.
    if a.read_time:
        for line in summary_lines(text, pairs(a.title, "--title"), pairs(a.read, "--read")):
            print(line)
        return 0
    langs = [l.strip() for l in a.langs.split(",") if l.strip()]
    errors = check(text, a.platform, langs, a.source, pairs(a.title, "--title"), pairs(a.label, "--label"), a.skill,
                   a.template, pairs(a.read, "--read"))
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
