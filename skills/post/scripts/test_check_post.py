#!/usr/bin/env python3
"""Tests for check_post.py. Run: python3 test_check_post.py"""
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check_post import BEHIND_NOTE, BEHIND_TITLE, EN_TITLE, FOOTER, check, detect, fix, footer, read_minutes, summary_lines  # noqa: E402

GH_EN = f"""Adds retry to the upload step. Please review the backoff values.

---

<details><summary><b>{EN_TITLE}</b> · 1 min read</summary>

## Summary

- Retry three times.

</details>

---

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

---

{FOOTER}
"""

# Lead english, also japanese: no label, english first.
GH_EN_JA = f"""Adds retry to the upload step. Please review the backoff values.

アップロードに再試行を足しました。待ち時間の値を見てください。

---

{EN_BLOCK}

{JA_BLOCK}

---

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

---

{FOOTER}
"""

# A repo PR template: its heading comes before the lead, its other sections after the block.
GH_TEMPLATE = f"""## Description

Adds retry to the upload step. Please review the backoff values.

---

{EN_BLOCK}

## Checklist

- [x] I ran the tests

---

{FOOTER}
"""

# The footer from before 0.9.0.
OLD = ("🤖 Generated with [Claude Code](https://claude.com/claude-code) using "
       "[clins:post](https://github.com/clins1994/skills/blob/main/skills/post/SKILL.md)")

LINEAR_EN = f"""Fix the login redirect. Done when the e2e test passes.

---

>>> {EN_TITLE} · 1 min read

## Context

The redirect drops the query string.

>>>

---

{FOOTER}
"""

BEHIND = (f"\n<details><summary>{BEHIND_TITLE}</summary>\n\n{BEHIND_NOTE}\n\n"
          "- Asked for a retry on the upload step.\n- One session wrote the code and the tests.\n\n</details>")
LINEAR_BEHIND = (f"\n>>> {BEHIND_TITLE}\n\n{BEHIND_NOTE}\n\n- Asked for a fix to the redirect.\n\n>>>")
GH_BEHIND = GH_EN.rstrip("\n") + "\n" + BEHIND + "\n"

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
    ("footer with a model passes", GH_EN.replace(FOOTER, footer("post", "Opus 5.5")), {}, []),
    ("footer with a model and an effort passes", GH_EN.replace(FOOTER, footer("post", "Opus 5.5", "Medium")), {}, []),
    ("old footer fails", GH_EN.replace(FOOTER, OLD), {}, ["old one (🤖)"]),
    ("short post with the old footer fails", "Fixed.\n\n" + OLD, {}, ["short post"]),
    ("footer before the blocks fails", GH_EN.replace("---\n\n" + FOOTER, "").replace("---\n", "---\n\n" + FOOTER + "\n"),
     {}, ["after the details blocks"]),
    ("footer without a divider above it fails", GH_EN.replace("---\n\n" + FOOTER, FOOTER), {}, ["divider (---) above the footer"]),
    ("divider with no blank line above it fails", GH_EN.replace("\n\n---\n\n" + FOOTER, "\n---\n\n" + FOOTER), {},
     ["divider (---) above the footer"]),
    ("template footer without a divider fails", GH_TEMPLATE.replace("---\n\n" + FOOTER, FOOTER),
     dict(template=True), ["divider (---) above the footer"]),
    ("linear footer without a divider fails", LINEAR_EN.replace("---\n\n" + FOOTER, FOOTER), dict(platform="linear"),
     ["divider (---) above the footer"]),
    ("footer must link Claude Code", GH_EN.replace("[Claude Code](https://claude.com/claude-code)", "Claude Code"),
     {}, ["footer is missing or changed"]),
    ("behind the prompt passes", GH_BEHIND, dict(platform="github"), []),
    ("behind the prompt on Linear passes", LINEAR_EN.rstrip("\n") + "\n" + LINEAR_BEHIND + "\n", dict(platform="linear"), []),
    ("behind the prompt is not a details block", GH_BEHIND, dict(langs=["en"]), []),
    ("behind the prompt needs its note", GH_BEHIND.replace(BEHIND_NOTE + "\n\n", ""), {}, ["starts with this note"]),
    ("behind the prompt names no pull request", GH_BEHIND.replace("the tests.", "the tests in #18."), {}, ["names #18"]),
    ("behind the prompt names no other repo's issue", GH_BEHIND.replace("the tests.", "the tests for beeper/line#284."),
     {}, ["names beeper/line#284"]),
    ("behind the prompt names no pull request URL", GH_BEHIND.replace(
        "the tests.", "the tests in https://github.com/o/r/pull/7."), {}, ["names https://github.com/o/r/pull/7"]),
    ("behind the prompt may show a number in code", GH_BEHIND.replace("the tests.", "the tests, with `#18` in a log."), {}, []),
    ("behind the prompt gets the english style rules", GH_BEHIND.replace("wrote the code", "wrote the code — fast"),
     {}, ["em-dash"]),
    ("behind the prompt above the footer fails", GH_EN.replace("---\n\n" + FOOTER, BEHIND.strip() + "\n\n---\n\n" + FOOTER),
     {}, ["directly under the footer"]),
    ("behind the prompt after other text fails", GH_EN.rstrip("\n") + "\n\nmore text\n" + BEHIND + "\n", {},
     ["directly under the footer"]),
    ("text below behind the prompt is not checked", GH_BEHIND + "\n<details><summary>Greptile Summary</summary>\n\nbot—text\n</details>\n",
     {}, []),
    ("text below the footer is not checked", GH_EN + "\n<details><summary>Greptile Summary</summary>\n\nbot—text\n</details>\n",
     {}, []),
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
NL = "🇳🇱 Meer details"
DETECTS = [
    ("english only", GH_EN, {}, (["en"], "en", [])),
    ("english lead, also japanese", GH_EN_JA, {}, (["en", "ja"], "en", [])),
    ("japanese lead, english source", GH_JA_EN, {}, (["ja", "en"], "en", [])),
    ("portuguese and japanese", GH_PT_JA, {}, (["pt", "ja"], "pt", [])),
    ("short post", "Fixed.\n", {}, (["en"], "en", [])),
    ("template heading", "## Description\n\n" + GH_JA_EN, {"template": True}, (["ja", "en"], "en", [])),
    ("mention line", "@reviewer\n\n" + GH_JA_EN, {}, (["ja", "en"], "en", [])),
    ("unknown title is reported", GH_EN.replace(EN_TITLE, NL), {}, (["en"], "en", [NL])),
    ("unknown title with --title", GH_EN.replace(EN_TITLE, NL), {"titles": {"nl": NL}}, (["nl"], "nl", [])),
]

# fix: an old post (no read times, no divider above the footer) catches up, and only its format changes.
def old(post: str, platform: str = "github") -> str:
    post = re.sub(r" · (?:\d+ min read|読了目安\d+分|\d+ min de leitura)", "", post)
    return post.replace("---\n\n" + FOOTER, OLD)


BOT = "\n<details><summary>🇬🇧 More details · 9 min read</summary>\n\nbot text\n</details>\n"
LINEAR_BOT = "\n>>> 🇬🇧 More details · 9 min read\n\nbot text\n\n>>>\n"


def saved_on_linear(post: str) -> str:
    """Linear saves every link as [text](<url>)."""
    return re.sub(r"\]\((https?://[^)\s]+)\)", r"](<\1>)", post)


# Fenced examples of a block, a Linear block and the old footer, inside a details block.
FENCED = ("- Retry three times.\n\n```\n<details><summary>🇬🇧 More details · 4 min read</summary>\n```\n\n"
          f"```\n>>> {EN_TITLE} · 4 min read\n\nx\n\n>>>\n```\n\n```\n{FOOTER}\n```")
GH_FENCED = GH_EN.replace("- Retry three times.", FENCED)
BOLD = GH_EN.replace(f"<b>{EN_TITLE}</b> · 1 min read", f"<b>{EN_TITLE} · 1 min read</b>")


def cli(post: str, *args: str) -> str:
    """What check_post.py prints for the post."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(post)
    out = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "check_post.py"), *args, f.name],
                         capture_output=True, text=True)
    pathlib.Path(f.name).unlink()
    return out.stdout + out.stderr
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
    ("a saved Linear post gets its divider, and its bot section stays",
     fix(saved_on_linear(old(LINEAR_EN)) + LINEAR_BOT) == saved_on_linear(LINEAR_EN) + LINEAR_BOT),
    ("other saved Linear links keep their form", "[doc](<https://example.com>)" in fix(saved_on_linear(
        old(LINEAR_EN).replace("query string.", "query string. See [doc](https://example.com)."))
        + LINEAR_BOT)),
    ("a saved Linear footer keeps the text below it", fix(saved_on_linear(LINEAR_EN) + LINEAR_BOT.replace(
        "9 min", "7 min")) == saved_on_linear(LINEAR_EN) + LINEAR_BOT.replace("9 min", "7 min")),
    ("a read time inside bold keeps the closing tag", fix(BOLD.replace("1 min read", "7 min read")) == BOLD),
    ("a missing read time inside bold goes after the tag", fix(BOLD.replace(" · 1 min read", "")) == GH_EN),
    ("a title with markup the fix does not know stays",
     fix(BOLD.replace("1 min read", "<i>7</i> min read")) == BOLD.replace("1 min read", "<i>7</i> min read")),
    ("fenced examples do not change", fix(old(GH_EN).replace("- Retry three times.", FENCED)) == GH_FENCED),
    ("a fenced example is not a block or a footer", check(GH_FENCED, "github") == []),
    ("the CLI reports a footer above the blocks",
     "after the details blocks" in cli(GH_EN.replace("---\n\n" + FOOTER, "").replace("---\n", "---\n\n" + FOOTER + "\n"))),
    ("the CLI does not check a bot block below the footer", "0 error(s)" in cli(GH_EN + BOT, "--platform", "github")),
    ("the CLI reads saved Linear links", "0 error(s)" in cli(saved_on_linear(LINEAR_EN) + LINEAR_BOT, "--platform", "linear")),
    ("a footer gets its divider", fix(GH_EN.replace("---\n\n" + FOOTER, FOOTER)) == GH_EN),
    ("a template footer gets its divider right above it",
     fix(GH_TEMPLATE.replace("---\n\n" + FOOTER, FOOTER)) == GH_TEMPLATE),
    ("a linear footer gets its divider", fix(LINEAR_EN.replace("---\n\n" + FOOTER, FOOTER) + LINEAR_BOT)
     == LINEAR_EN + LINEAR_BOT),
    ("a CRLF footer gets its divider", fix(GH_EN.replace("---\n\n" + FOOTER, FOOTER).replace("\n", "\r\n"))
     == GH_EN.replace("\n", "\r\n")),
    ("a divider without its blank lines gets them", fix(GH_EN.replace("\n\n---\n\n" + FOOTER, "\n---\n" + FOOTER)) == GH_EN),
    ("a footer with its divider does not change, twice", fix(fix(GH_TEMPLATE)) == GH_TEMPLATE),
    ("an old footer keeps its links and skill", fix(GH_EN.replace(FOOTER, OLD.replace("clins:post", "clins:create-pr")
        .replace("skills/post/", "skills/create-pr/"))) == GH_EN.replace(FOOTER, footer("create-pr"))),
    ("an old footer whose link does not match keeps it", "[clins:linear](https://github.com/clins1994/skills/blob/main/skills/post/"
     in fix(old(GH_EN).replace("[clins:post]", "[clins:linear]"))),
    ("the footer line reads as a sentence", footer("create-pr", "Opus 5.5", "Medium").startswith(
        "🪴 Generated with [Claude Code](https://claude.com/claude-code) on Opus 5.5 (Medium) using [clins:create-pr]")),
    ("a footer with a model and an effort passes the check",
     check(GH_EN.replace(FOOTER, footer("post", "Opus 5.5", "Medium")), "github") == []),
    ("behind the prompt does not change, and its bot section stays", fix(GH_BEHIND + BOT) == GH_BEHIND + BOT),
    ("an old post gets fixed above behind the prompt", fix(old(GH_EN).rstrip("\n").replace(OLD, FOOTER) + "\n" + BEHIND + "\n")
     == GH_BEHIND),
    ("--read-time leaves out behind the prompt", list(summary_lines(GH_BEHIND)) == ["🇬🇧 More details · 1 min read"]),
    ("the CLI does not check a bot block below behind the prompt", "0 error(s)" in cli(GH_BEHIND + BOT, "--platform", "github")),
    ("a footer with no text above it is left alone", fix(FOOTER + "\n") == FOOTER + "\n"),
    ("a custom title gets its read time", fix(GH_EN.replace(EN_TITLE, "🇽🇽 Custom").replace(" · 1 min read", ""),
                                             {"xx": "🇽🇽 Custom"}, {"xx": "{n} xx"}).count("🇽🇽 Custom</b> · 1 xx") == 1),
]:
    print(("ok  " if ok else "FAIL"), "fix:", name)
    failed += not ok
for name, text, kw, want in DETECTS:
    got = detect(text, **kw)
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
