#!/usr/bin/env python3
"""Tests for check_post.py. Run: python3 test_check_post.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check_post import EN_TITLE, FOOTER, check, footer  # noqa: E402

GH_EN = f"""Adds retry to the upload step. Please review the backoff values.

---

<details><summary><b>{EN_TITLE}</b></summary>

## Summary

- Retry three times.

</details>

{FOOTER}
"""

JA_BLOCK = """<details><summary><b>🇯🇵 詳細</b></summary>

## 概要

- 3回まで再試行する。

</details>"""

EN_BLOCK = f"""<details><summary><b>{EN_TITLE}</b></summary>

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

<details><summary><b>🇧🇷 Mais detalhes</b></summary>

## Resumo

- Tenta três vezes.

</details>

{JA_BLOCK}

{FOOTER}
"""

LINEAR_EN = f"""Fix the login redirect. Done when the e2e test passes.

---

>>> {EN_TITLE}

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
    ("short post with footer fails", "Fixed.\n\n" + FOOTER, {}, ["short post"]),
    ("unknown language needs a title", GH_EN, dict(langs=["xx"]), ["--title xx="]),
    ("title override passes", GH_EN.replace(EN_TITLE, "🇽🇽 Custom"), dict(langs=["xx"], titles={"xx": "🇽🇽 Custom"}), []),
    ("create-pr footer passes", GH_EN.replace(FOOTER, footer("create-pr")), dict(skill="create-pr"), []),
    ("footer name must match its link", GH_EN.replace("[clins:post]", "[clins:linear]"), {}, ["links to"]),
    ("footer must name the running skill", GH_EN, dict(skill="linear"), ["comes from clins:linear"]),
]

failed = 0
for name, text, kw, want in CASES:
    errs = check(text, kw.get("platform"), kw.get("langs"), kw.get("source"), kw.get("titles"), None, kw.get("skill"))
    ok = (not errs) if not want else all(any(w in e for e in errs) for w in want)
    print(("ok  " if ok else "FAIL"), name, "" if ok else errs)
    failed += not ok
print("all passed" if not failed else f"{failed} failed")
sys.exit(1 if failed else 0)
