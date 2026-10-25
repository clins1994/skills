#!/usr/bin/env python3
"""Tests for check_post.py. Run: python3 test_check_post.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check_post import EN_TITLE, FOOTER, check, footer, read_minutes  # noqa: E402

GH_EN = f"""Adds retry to the upload step. Please review the backoff values.

---

<details><summary><b>{EN_TITLE}</b> · 1 min read</summary>

## Summary

- Retry three times.

</details>

{FOOTER}
"""

JA_BLOCK = """<details><summary><b>🇯🇵 詳細</b> · 1分で読めます</summary>

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

LINEAR_EN = f"""Fix the login redirect. Done when the e2e test passes.

---

>>> {EN_TITLE} · 1 min read

## Context

The redirect drops the query string.

>>>

{FOOTER}
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
    ("long chinese sentence fails", GH_EN_JA.replace("🇯🇵 詳細</b> · 1分で読めます", "🇨🇳 详细信息</b> · 阅读约1分钟").replace("3回まで再試行する。", "重试" * 45 + "。"),
     dict(langs=["en", "zh"]), ["over 80 characters (zh)"]),
    ("chinese may space latin text", GH_EN_JA.replace("🇯🇵 詳細</b> · 1分で読めます", "🇨🇳 详细信息</b> · 阅读约1分钟").replace("3回まで再試行する。", "最多重试 3 次。"),
     dict(langs=["en", "zh"]), []),
    ("hindi sentences end at the danda", GH_EN_JA.replace("🇯🇵 詳細</b> · 1分で読めます", "🇮🇳 अधिक विवरण</b> · 1 मिनट में पढ़ें").replace(
        "3回まで再試行する。", " ".join(["यह छोटा वाक्य है।"] * 12)),
     dict(langs=["en", "hi"]), []),
    ("long hindi sentence fails", GH_EN_JA.replace("🇯🇵 詳細</b> · 1分で読めます", "🇮🇳 अधिक विवरण</b> · 1 मिनट में पढ़ें").replace(
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
    ("create-pr footer passes", GH_EN.replace(FOOTER, footer("create-pr")), dict(skill="create-pr"), []),
    ("footer name must match its link", GH_EN.replace("[clins:post]", "[clins:linear]"), {}, ["links to"]),
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
]

failed = 0
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
