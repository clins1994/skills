#!/usr/bin/env python3
"""Tests for check_post.py. Run: python3 test_check_post.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check_post import EN_TITLE, FOOTER, check  # noqa: E402

GH_EN = f"""Adds retry to the upload step. Please review the backoff values.

---

<details><summary><h3>{EN_TITLE}</h3></summary>

## Summary

- Retry three times.

</details>

{FOOTER}
"""

GH_JA = f"""アップロードに再試行を足しました。待ち時間の値を見てください。

原文: Adds retry to the upload step. Please review the backoff values.

---

<details><summary><h3>🇯🇵 詳細（エージェント向け）</h3></summary>

## 概要

- 3回まで再試行する。

</details>

<details><summary><h3>{EN_TITLE}</h3></summary>

## Summary

- Retry three times.

</details>

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
    ("Japanese GitHub post passes", GH_JA, dict(platform="github", lang="ja"), []),
    ("English Linear post passes", LINEAR_EN, dict(platform="linear"), []),
    ("short post passes", "Fixed in abc1234. Please review again.\n", {}, []),
    ("open block fails", GH_EN.replace("<details>", "<details open>"), {}, ["open"]),
    ("missing footer fails", GH_EN.replace(FOOTER, ""), {}, ["footer"]),
    ("no blank line above divider fails", GH_EN.replace("values.\n\n---", "values.\n---"), {}, ["blank line above"]),
    ("contraction fails", GH_EN.replace("Retry three", "Don't retry three"), {}, ["contraction"]),
    ("Linear syntax on GitHub fails", LINEAR_EN, dict(platform="github"), ["Linear block syntax"]),
    ("missing English lead fails", GH_JA.replace("原文: ", ""), dict(lang="ja"), ["Two-language lead"]),
    ("structure mismatch fails", GH_JA.replace("- 3回", "3回"), dict(lang="ja"), ["list items"]),
    ("short post with footer fails", "Fixed.\n\n" + FOOTER, {}, ["short post"]),
    ("unknown language needs a title", GH_EN, dict(lang="pt"), ["--title"]),
]

failed = 0
for name, text, kw, want in CASES:
    errs = check(text, kw.get("platform"), kw.get("lang"), None, None)
    ok = (not errs) if not want else all(any(w in e for e in errs) for w in want)
    print(("ok  " if ok else "FAIL"), name, "" if ok else errs)
    failed += not ok
print("all passed" if not failed else f"{failed} failed")
sys.exit(1 if failed else 0)
