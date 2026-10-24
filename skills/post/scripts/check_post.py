#!/usr/bin/env python3
"""Check a post (PR description, issue or comment) before you send it.

    python3 check_post.py --platform github post.md
    python3 check_post.py --platform github --langs en,ja post.md
    python3 check_post.py --platform linear --langs ja,en --source en post.md
    python3 check_post.py --langs pt --title "pt=🇧🇷 Mais detalhes" post.md
    gh pr view 12 --json body -q .body | python3 check_post.py -

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

# Language code: (block title, "original" label in that language).
KNOWN = {
    "en": ("🇬🇧 More details", "Original"),
    "ja": ("🇯🇵 詳細", "原文"),
    "zh": ("🇨🇳 详细信息", "原文"),
    "zh-CN": ("🇨🇳 详细信息", "原文"),
    "zh-TW": ("🇹🇼 詳細資訊", "原文"),
    "ko": ("🇰🇷 자세한 내용", "원문"),
    "pt": ("🇧🇷 Mais detalhes", "Original"),
    "pt-BR": ("🇧🇷 Mais detalhes", "Original"),
    "pt-PT": ("🇵🇹 Mais detalhes", "Original"),
    "es": ("🇪🇸 Más detalles", "Original"),
    "fr": ("🇫🇷 Plus de détails", "Original"),
    "de": ("🇩🇪 Weitere Details", "Original"),
    "it": ("🇮🇹 Altri dettagli", "Originale"),
    "hi": ("🇮🇳 अधिक विवरण", "मूल"),
    "da": ("🇩🇰 Flere detaljer", "Original"),
    "az": ("🇦🇿 Ətraflı", "Orijinal"),
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
JA_LIMIT = 80

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


def base(lang: str) -> str:
    return lang.split("-")[0]


def style(lang: str, lines) -> list[str]:
    err = []
    for line in lines:
        if base(lang) == "en":
            for pat, why in EN_STYLE:
                if re.search(pat, line, re.I):
                    err.append(f"English {why}: {line[:50]}…")
        elif base(lang) == "ja":
            for sent in re.split(r"(?<=。)", line):
                if len(sent.strip()) > JA_LIMIT:
                    err.append(f"Japanese sentence over {JA_LIMIT} chars: {sent[:40]}…")
            if re.search(rf"[{CJK}] [A-Za-z0-9]|[A-Za-z0-9] [{CJK}]", line):
                err.append(f"Space between full-width and half-width text: {line[:40]}…")
    return err


def check(text: str, platform: str | None, langs: list[str] | None = None, source: str | None = None,
          titles: dict[str, str] | None = None, labels: dict[str, str] | None = None,
          skill: str | None = None):
    err: list[str] = []
    langs = langs or ["en"]
    source = source or langs[0]
    titles, labels = titles or {}, labels or {}
    if len(set(langs)) != len(langs):
        return [f"A language appears twice in --langs {','.join(langs)}."]
    want_titles = []
    for lang in langs:
        t = titles.get(lang) or KNOWN.get(lang, (None, None))[0]
        if not t:
            return [f"No built-in title for {lang}. Pass --title {lang}=..."]
        want_titles.append(t)
    label = None
    if source in langs and source != langs[0]:
        label = labels.get(langs[0]) or KNOWN.get(langs[0], (None, None))[1]
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

    blocks = sorted([(m.start(), re.sub(r"<[^>]+>", "", m["t"]).strip(), m["b"])
                     for rx in (GITHUB, LINEAR) for m in rx.finditer(text)])
    head = text[: blocks[0][0]] if blocks else text
    lines = head.strip().split("\n")
    lines = lines[1:] if lines and lines[0].startswith("@") else lines

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
    if len(re.findall(r"[.!?。！？](?:\s|$)", leads[source])) > 2:
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
        if not foot:
            err.append("The footer is missing or changed. Copy it from SKILL.md.")
        elif foot[1] != foot[2]:
            err.append(f"The footer names clins:{foot[1]} but links to skills/{foot[2]}.")
        elif skill and foot[1] != skill:
            err.append(f"The footer names clins:{foot[1]}. This post comes from clins:{skill}.")
    elif "---" in (l.strip() for l in lines) or foot:
        err.append("A short post (no block) has no divider and no footer.")

    # Style per language, and every block shaped like the source block.
    bodies = {lang: next((b[2] for b in blocks if b[1] == t), "") for lang, t in zip(langs, want_titles)}
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
    ap.add_argument("--skill", help="the skill the footer must name, for example create-pr")
    a = ap.parse_args()
    text = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8").read()
    text = re.sub(r"\]\(<([^>\s]+)>\)", r"](\1)", text.replace("\r\n", "\n"))  # Linear links
    foot = FOOTER_LINE.search(text)
    if foot:
        text = text[: foot.end()] + "\n"  # Bot sections below the footer are not ours.
    langs = [l.strip() for l in a.langs.split(",") if l.strip()]
    errors = check(text, a.platform, langs, a.source, pairs(a.title, "--title"), pairs(a.label, "--label"), a.skill)
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
