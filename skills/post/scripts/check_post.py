#!/usr/bin/env python3
"""Check a post (PR description, issue or comment) before you send it.

    python3 check_post.py --platform github post.md
    python3 check_post.py --platform linear --lang ja post.md
    python3 check_post.py --lang pt --title "🇧🇷 Mais detalhes (para agentes)" --label "Original" post.md
    gh pr view 12 --json body -q .body | python3 check_post.py -

Exit code 1 means at least one error. Text below the footer is not checked:
review bots (for example Greptile) add their own sections there.
"""
from __future__ import annotations

import argparse
import re
import sys

EN_TITLE = "🇬🇧 More details (for agents)"
KNOWN = {"ja": ("🇯🇵 詳細（エージェント向け）", "原文")}
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


def check(text: str, platform: str | None, lang: str | None, title: str | None, label: str | None,
          skill: str | None = None):
    err: list[str] = []
    foot = FOOTER_LINE.search(text)
    if lang and lang != "en":
        title = title or KNOWN.get(lang, (None, None))[0]
        label = label or KNOWN.get(lang, (None, None))[1]
        if not title or not label:
            return [f"No built-in title for --lang {lang}. Pass --title and --label."]
        titles = [title, EN_TITLE]
    else:
        lang = None
        titles = [EN_TITLE]

    if "@greptileai" in text:
        err.append("The post contains @greptileai.")
    if re.search(r"<details\s+open", text):
        err.append("A block is open (<details open>). Every block must be collapsed.")
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

    # Leads.
    paras = re.split(r"\n\s*\n", "\n".join(lines).strip())
    paras = [p.strip() for p in paras if p.strip() and p.strip() != "---" and not p.startswith(("|", "!["))]
    if not paras or paras[0].startswith("#"):
        err.append("The post must start with a lead sentence, not a heading.")
        return err
    en_lead = paras[0]
    if lang:
        if len(paras) < 2 or not paras[1].startswith(f"{label}:"):
            err.append(f"Two-language lead: the {lang} lead, a blank line, then '{label}: <English lead>'.")
        else:
            en_lead = paras[1][len(label) + 1:].strip()
            if not en_lead:
                err.append(f"The '{label}:' line is empty.")
            for sent in re.split(r"(?<=。)", no_code(paras[0])):
                if lang == "ja" and len(sent.strip()) > JA_LIMIT:
                    err.append(f"Japanese lead sentence over {JA_LIMIT} chars: {sent[:40]}…")
    if len(re.findall(r"[.!?。](?:\s|$)", en_lead)) > 2:
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
        if found != titles:
            err.append(f"Expected the block titles {titles}, found {found}.")
        if not foot:
            err.append("The footer is missing or changed. Copy it from SKILL.md.")
        elif foot[1] != foot[2]:
            err.append(f"The footer names clins:{foot[1]} but links to skills/{foot[2]}.")
        elif skill and foot[1] != skill:
            err.append(f"The footer names clins:{foot[1]}. This post comes from clins:{skill}.")
    elif "---" in (l.strip() for l in lines) or foot:
        err.append("A short post (no block) has no divider and no footer.")

    # English style.
    en = next((b[2] for b in blocks if b[1] == EN_TITLE), "")
    for line in [no_code(en_lead), *prose(en)]:
        for pat, why in EN_STYLE:
            if re.search(pat, line, re.I):
                err.append(f"English {why}: {line[:50]}…")

    # Second language.
    other = next((b[2] for b in blocks if lang and b[1] == title), "")
    if lang == "ja":
        for line in prose(other):
            for sent in re.split(r"(?<=。)", line):
                if len(sent.strip()) > JA_LIMIT:
                    err.append(f"Japanese sentence over {JA_LIMIT} chars: {sent[:40]}…")
            if re.search(rf"[{CJK}] [A-Za-z0-9]|[A-Za-z0-9] [{CJK}]", line):
                err.append(f"Space between full-width and half-width text: {line[:40]}…")
    if other and en:
        a, b = shape(other), shape(en)
        for k in a:
            if a[k] != b[k]:
                err.append(f"Different number of {k}: {lang} {a[k]}, English {b[k]}.")
    return err


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="post file, or - for stdin")
    ap.add_argument("--platform", choices=("github", "linear"))
    ap.add_argument("--lang", help="second language code, for example ja")
    ap.add_argument("--title", help="block title for a --lang without a built-in one")
    ap.add_argument("--label", help="'original' label for a --lang without a built-in one")
    ap.add_argument("--skill", help="the skill the footer must name, for example create-pr")
    a = ap.parse_args()
    text = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8").read()
    text = re.sub(r"\]\(<([^>\s]+)>\)", r"](\1)", text.replace("\r\n", "\n"))  # Linear links
    foot = FOOTER_LINE.search(text)
    if foot:
        text = text[: foot.end()] + "\n"  # Bot sections below the footer are not ours.
    errors = check(text, a.platform, a.lang, a.title, a.label, a.skill)
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
