#!/usr/bin/env python3
"""Tests for check_post.py. Run: python3 test_check_post.py"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check_post import EN_TITLE, FOOTER, check, detect, fix, footer, read_minutes, summary_lines  # noqa: E402

GH_EN = f"""Adds retry to the upload step. Please review the backoff values.

---

<details><summary><b>{EN_TITLE}</b> · 1 min read</summary>

## Summary

- Retry three times.

</details>

{FOOTER}
"""

JA_BLOCK = """<details><summary><b>🇯🇵 詳細</b> · 読了目安1分</summary>

## 概要

- 3回まで再試行する。

</details>"""

EN_BLOCK = f"""<details><summary><b>{EN_TITLE}</b> · 1 min read</summary>

## Summary

- Retry three times.

</details>"""

# Lead japanese, english is the source: the english lead carries 原文:.
GH_JA_EN = f"""アップロードに再試行を足しました。待ち時間の値を見てください。

原文: Adds retry to the upload step. Please review the backoff values.

---

{JA_BLOCK}

{EN_BLOCK}

{FOOTER}
"""

# Lead english, also japanese: no label, english first.
GH_EN_JA = f"""Adds retry to the upload step. Please review the backoff values.

アップロードに再試行を足しました。待ち時間の値を見てください。

---

{EN_BLOCK}

{JA_BLOCK}

{FOOTER}
"""

# Lead portuguese, also japanese, no english at all.
GH_PT_JA = f"""Adiciona novas tentativas ao upload. Confira os tempos de espera.

アップロードに再試行を足しました。待ち時間の値を見てください。

---

<details><summary><b>🇧🇷 Mais detalhes</b> · 1 min de leitura</summary>

## Resumo

- Tenta três vezes.

</details>

{JA_BLOCK}

{FOOTER}
"""

# A repo PR template: its heading comes before the lead, its other sections after the block.
GH_TEMPLATE = f"""## Description

Adds retry to the upload step. Please review the backoff values.

---

{EN_BLOCK}

## Checklist

- [x] I ran the tests

{FOOTER}
"""

# The one-line footer from before 0.9.0.
OLD = ("🤖 Generated with [Claude Code](https://claude.com/claude-code) using "
       "[clins:post](https://github.com/clins1994/skills/blob/main/skills/post/SKILL.md)")

LINEAR_EN = f"""Fix the login redirect. Done when the e2e test passes.

---

>>> {EN_TITLE} · 1 min read

## Context

The redirect drops the query string.

>>>

{footer("post", "linear")}
"""

CASES = [
    ("English GitHub post passes", GH_EN, dict(platform="github"), []),
    ("English Linear post passes", LINEAR_EN, dict(platform="linear"), []),
    ("ja lead with english source passes", GH_JA_EN, dict(platform="github", langs=["ja", "en"], source="en"), []),
    ("en lead with japanese passes", GH_EN_JA, dict(platform="github", langs=["en", "ja"]), []),
    ("pt lead with japanese, no english, passes", GH_PT_JA, dict(langs=["pt", "ja"]), []),
    ("short post passes", "Fixed in abc1234. Please review again.\n", {}, []),
    ("open block fails", GH_EN.replace("<details>", "<details open>"), {}, ["open"]),
    ("missing footer fails", GH_EN.replace(FOOTER, ""), {}, ["footer"]),
    ("no blank line above divider fails", GH_EN.replace("values.\n\n---", "values.\n---"), {}, ["blank line above"]),
    ("heading in summary fails", GH_EN.replace("<b>", "<h3>").replace("</b>", "</h3>"), {}, ["heading in <summary>"]),
    ("contraction fails", GH_EN.replace("Retry three", "Don't retry three"), {}, ["contraction"]),
    ("Linear syntax on GitHub fails", LINEAR_EN, dict(platform="github"), ["Linear block syntax"]),
    ("missing original label fails", GH_JA_EN.replace("原文: ", ""), dict(langs=["ja", "en"], source="en"), ["原文:"]),
    ("missing lead fails", GH_EN, dict(langs=["en", "ja"]), ["one lead per language"]),
    ("structure mismatch fails", GH_JA_EN.replace("- 3回", "3回"), dict(langs=["ja", "en"], source="en"), ["list items"]),
    ("block order follows the languages", GH_JA_EN, dict(langs=["en", "ja"]), ["block titles"]),
    ("english style is not applied to portuguese", GH_PT_JA.replace("Tenta", "Should tenta"), dict(langs=["pt", "ja"]), []),
    ("japanese spacing fails", GH_EN_JA.replace("3回まで", "3 回まで"), dict(langs=["en", "ja"]), ["full-width"]),
    ("japanese length ignores a link's URL", GH_EN_JA.replace(
        "3回まで再試行する。",
        "[3回まで再試行する](https://developers.raycast.com/basics/prepare-an-extension-for-store#metadata-and-configuration)。"),
     dict(langs=["en", "ja"]), []),
    ("japanese length counts a link's text", GH_EN_JA.replace(
        "3回まで再試行する。", "[" + "再試行" * 30 + "](https://example.com)。"),
     dict(langs=["en", "ja"]), ["over 80 characters"]),
    ("long english sentence fails", GH_EN.replace("- Retry three times.", "- Retry " + "very " * 30 + "often."),
     {}, ["over 30 words (en)"]),
    ("long portuguese sentence fails", GH_PT_JA.replace("- Tenta três vezes.", "- Tenta " + "muitas " * 30 + "vezes."),
     dict(langs=["pt", "ja"]), ["over 30 words (pt)"]),
    ("long chinese sentence fails", GH_EN_JA.replace("🇯🇵 詳細</b> · 読了目安1分", "🇨🇳 详细信息</b> · 阅读约1分钟").replace("3回まで再試行する。", "重试" * 45 + "。"),
     dict(langs=["en", "zh"]), ["over 80 characters (zh)"]),
    ("chinese may space latin text", GH_EN_JA.replace("🇯🇵 詳細</b> · 読了目安1分", "🇨🇳 详细信息</b> · 阅读约1分钟").replace("3回まで再試行する。", "最多重试 3 次。"),
     dict(langs=["en", "zh"]), []),
    ("hindi sentences end at the danda", GH_EN_JA.replace("🇯🇵 詳細</b> · 読了目安1分", "🇮🇳 अधिक विवरण</b> · 1 मिनट में पढ़ें").replace(
        "3回まで再試行する。", " ".join(["यह छोटा वाक्य है।"] * 12)),
     dict(langs=["en", "hi"]), []),
    ("long hindi sentence fails", GH_EN_JA.replace("🇯🇵 詳細</b> · 読了目安1分", "🇮🇳 अधिक विवरण</b> · 1 मिनट में पढ़ें").replace(
        "3回まで再試行する。", "यह " * 32 + "वाक्य है।"),
     dict(langs=["en", "hi"]), ["over 30 words (hi)"]),
    ("short post with footer fails", "Fixed.\n\n" + FOOTER, {}, ["short post"]),
    ("unknown language needs a title", GH_EN, dict(langs=["xx"]), ["--title xx="]),
    ("unknown language needs a read time", GH_EN, dict(langs=["xx"], titles={"xx": "🇽🇽 Custom"}), ["--read xx="]),
    ("title override passes", GH_EN.replace(EN_TITLE, "🇽🇽 Custom").replace("1 min read", "1 xx"),
     dict(langs=["xx"], titles={"xx": "🇽🇽 Custom"}, reads={"xx": "{n} xx"}), []),
    ("missing read time fails", GH_EN.replace(" · 1 min read", ""), {}, ["'🇬🇧 More details · 1 min read'"]),
    ("wrong read time fails", GH_EN.replace("1 min read", "5 min read"), {}, ["not '5 min read'"]),
    ("read time grows with the text", GH_EN.replace("- Retry three times.", "Retry often. " * 120),
     {}, ["'🇬🇧 More details · 2 min read'"]),
    ("linear read time is checked", LINEAR_EN.replace(" · 1 min read", ""), dict(platform="linear"), ["1 min read"]),
    ("footer with a model and more lines passes", GH_EN.replace(FOOTER, footer("post", model="Opus 5.5").replace(
        "- Skills:", "- Models: Opus 5.5 (`claude-opus-5-5`) wrote it.\n- Skills:")), {}, []),
    ("old one-line footer fails", GH_EN.replace(FOOTER, OLD), {}, ["old one-line footer"]),
    ("footer before the blocks fails", GH_EN.replace(FOOTER, "").replace("---\n", "---\n\n" + FOOTER + "\n"),
     {}, ["after the details blocks"]),
    ("footer must link Claude Code", GH_EN.replace("[Claude Code](https://claude.com/claude-code)", "Claude Code"),
     {}, ["must link Claude Code"]),
    ("footer block is not a details block", GH_EN, dict(langs=["en"]), []),
    ("text below the footer block is not checked", GH_EN + "\n<details><summary>Greptile Summary</summary>\n\nbot—text\n</details>\n",
     {}, []),
    ("short post with the old footer fails", "Fixed.\n\n" + OLD, {}, ["short post"]),
    ("create-pr footer passes", GH_EN.replace(FOOTER, footer("create-pr")), dict(skill="create-pr"), []),
    ("footer name must match its link", GH_EN.replace("[clins:post]", "[clins:linear]"), {}, ["links to"]),
    ("footer title must match its link", GH_EN.replace("· clins:post", "· clins:linear"), {}, ["names clins:linear"]),
    ("footer must name the running skill", GH_EN, dict(skill="linear"), ["comes from clins:linear"]),
    ("template heading above the lead passes", GH_TEMPLATE, dict(platform="github", template=True), []),
    ("template heading needs --template", GH_TEMPLATE, dict(platform="github"), ["not a heading"]),
    ("template body still needs a lead", GH_TEMPLATE.replace(
        "Adds retry to the upload step. Please review the backoff values.\n\n", ""),
     dict(template=True), ["lead sentence"]),
]

# read_minutes: 200 words or 500 wide characters a minute, rounded up, URLs and markup not counted.
READS = [
    ("empty block is 1 minute", "", 1),
    ("200 words is 1 minute", "word " * 200, 1),
    ("201 words is 2 minutes", "word " * 201, 2),
    ("500 japanese characters is 1 minute", "あ" * 500, 1),
    ("501 japanese characters is 2 minutes", "あ" * 501, 2),
    ("100 words and 250 characters is 1 minute", "word " * 100 + "あ" * 250, 1),
    ("URLs and markup do not count", "[text](https://example.com/" + "a/" * 500 + ") <b>x</b> - | ---" * 100, 1),
    ("comparisons in code are read, not taken as HTML",
     "```\nif x < limit:\n" + "    total = total + step\n" * 100 + "if x > limit:\n```", 2),
    ("comparisons across lines in prose are read", "x < y\n" + "word " * 200 + "\ny > x", 2),
    ("thai counts characters", "ก" * 501, 2),
]

# summary_lines: what --read-time prints must pass check(), also with a custom title.
CUSTOM = GH_EN.replace(EN_TITLE, "🇺🇸 More details")
SUMMARIES = [
    ("built-in title", GH_EN, {}, {}, dict(), ["🇬🇧 More details · 1 min read"]),
    ("custom title for a built-in language", CUSTOM.replace("1 min read", "9 min read"), {"en": "🇺🇸 More details"}, {},
     dict(titles={"en": "🇺🇸 More details"}), ["🇺🇸 More details · 1 min read"]),
    ("custom title and read time", CUSTOM.replace("1 min read", "x"), {"xx": "🇺🇸 More details"}, {"xx": "{n} xx"},
     dict(langs=["xx"], titles={"xx": "🇺🇸 More details"}, reads={"xx": "{n} xx"}), ["🇺🇸 More details · 1 xx"]),
]

# detect: languages from the block titles, the source from the "original" label.
DETECTS = [
    ("english only", GH_EN, (["en"], "en")),
    ("english lead, also japanese", GH_EN_JA, (["en", "ja"], "en")),
    ("japanese lead, english source", GH_JA_EN, (["ja", "en"], "en")),
    ("portuguese and japanese", GH_PT_JA, (["pt", "ja"], "pt")),
    ("short post", "Fixed.\n", (["en"], "en")),
    ("template heading", "## Description\n\n" + GH_JA_EN, (["ja", "en"], "en"), True),
    ("mention line", "@reviewer\n\n" + GH_JA_EN, (["ja", "en"], "en")),
]

# fix: an old post (no read times, one-line footer) catches up, and only its format changes.
def old(post: str, platform: str = "github") -> str:
    post = re.sub(r" · (?:\d+ min read|読了目安\d+分|\d+ min de leitura)", "", post)
    new = footer("post", platform)
    return post.replace(new, OLD) if new in post else post


BOT = "\n<details><summary>🇬🇧 More details · 9 min read</summary>\n\nbot text\n</details>\n"
FIXES = [
    ("english github post", GH_EN, dict()),
    ("english linear post", LINEAR_EN, dict(platform="linear")),
    ("japanese lead, english source", GH_JA_EN, dict(langs=["ja", "en"], source="en")),
    ("portuguese and japanese", GH_PT_JA, dict(langs=["pt", "ja"])),
]

failed = 0
for name, post, kw in FIXES:
    before = old(post, kw.get("platform", "github"))
    after = fix(before)
    errs = check(after, kw.get("platform"), kw.get("langs"), kw.get("source"))
    ok = after == post and not errs and fix(after) == after and before != after
    print(("ok  " if ok else "FAIL"), "fix:", name, "" if ok else (errs, after))
    failed += not ok
for name, ok in [
    ("an up-to-date post does not change", fix(GH_EN) == GH_EN),
    ("a wrong read time is replaced", fix(GH_EN.replace("1 min read", "7 min read")) == GH_EN),
    ("text below the footer does not change", fix(old(GH_EN) + BOT) == GH_EN + BOT),
    ("CRLF stays CRLF", fix(old(GH_EN).replace("\n", "\r\n")) == GH_EN.replace("\n", "\r\n")),
    ("a CRLF post whose bot section uses LF is fixed", fix(old(GH_EN).replace("\n", "\r\n") + "\nbot\n")
     == GH_EN.replace("\n", "\r\n") + "\nbot\n"),
    ("mixed line endings are left alone", fix(old(GH_EN).replace("\n", "\r\n", 3)) == old(GH_EN).replace("\n", "\r\n", 3)),
    ("an old footer whose link does not match is left alone",
     OLD.replace("[clins:post]", "[clins:linear]") in fix(old(GH_EN).replace("[clins:post]", "[clins:linear]"))),
    ("a custom title gets its read time", fix(GH_EN.replace(EN_TITLE, "🇽🇽 Custom").replace(" · 1 min read", ""),
                                             {"xx": "🇽🇽 Custom"}, {"xx": "{n} xx"}).count("🇽🇽 Custom</b> · 1 xx") == 1),
]:
    print(("ok  " if ok else "FAIL"), "fix:", name)
    failed += not ok
for name, text, want, *template in DETECTS:
    got = detect(text, *template)
    print(("ok  " if got == want else "FAIL"), "detect:", name, "" if got == want else got)
    failed += got != want
for name, text, titles, reads, kw, want in SUMMARIES:
    got = list(summary_lines(text, titles, reads))
    fixed = text
    for line in got:
        t = line.partition(" · ")[0]
        fixed = re.sub(rf"(<b>{re.escape(t)}</b>) · [^<]*", lambda m: f"{m[1]} · {line.partition(' · ')[2]}", fixed)
    errs = check(fixed, None, kw.get("langs"), None, kw.get("titles"), None, None, False, kw.get("reads"))
    ok = got == want and not errs
    print(("ok  " if ok else "FAIL"), "summary:", name, "" if ok else (got, errs))
    failed += not ok
for name, body, want in READS:
    got = read_minutes(body)
    print(("ok  " if got == want else "FAIL"), name, "" if got == want else got)
    failed += got != want
for name, text, kw, want in CASES:
    errs = check(text, kw.get("platform"), kw.get("langs"), kw.get("source"), kw.get("titles"), None, kw.get("skill"),
                 kw.get("template", False), kw.get("reads"))
    ok = (not errs) if not want else all(any(w in e for e in errs) for w in want)
    print(("ok  " if ok else "FAIL"), name, "" if ok else errs)
    failed += not ok
print("all passed" if not failed else f"{failed} failed")
sys.exit(1 if failed else 0)
