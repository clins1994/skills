# Migrations

Each entry is one change to how a post looks. `clins:migrate-posts` applies an entry to a post only when the new `check_post.py` prints the entry's check error for that post. Apply the entries oldest first. The newest is at the top.

An entry changes the format only: titles, markup, labels, the footer. Never the words of the lead or the details.

## 0.7.0: read time in each block title

**Check error:** `Put the read time after the title: '<title> · <time>'`

**Change:** each block's summary line only. The error gives the exact title. `check_post.py --read-time` prints all of them.

- GitHub: `<summary><b>🇬🇧 More details</b></summary>` becomes `<summary><b>🇬🇧 More details</b> · 3 min read</summary>`. Keep the read time outside the `<b>`.
- Linear: `>>> 🇬🇧 More details` becomes `>>> 🇬🇧 More details · 3 min read`.
- A title with a wrong time: replace the time only.

## 0.1.3: plain block titles

**Check errors:** `Expected the block titles [...]` when the titles found are the old ones below, and `A heading in <summary> doubles the gap under the divider`. When the titles are only in the wrong order, no migration fixes it: leave it as is.

**Change:** the block titles only.

- `🇬🇧 More details (for agents)` becomes `🇬🇧 More details`.
- `🇯🇵 詳細（エージェント向け）` becomes `🇯🇵 詳細`.
- GitHub: `<summary><h3>…</h3></summary>` becomes `<summary><b>…</b></summary>`.
