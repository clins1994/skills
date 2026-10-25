#!/usr/bin/env python3
"""PreToolUse hook for Claude Code: stop `gh pr create` from going straight to
an upstream repo when the user's clins:fork-review setting wants a fork review.

Reads the hook input (JSON) on stdin. Prints a permission decision as JSON, or
nothing to let the command run. Every unexpected case lets the command run,
except under `mode fork`, where a failed check asks the user instead.

Run `python3 pr_guard.py --test` for the self-tests.
"""

import json
import os
import re
import shlex
import subprocess
import sys

PR_CREATE = re.compile(r"(?:^|[\s;&|(])gh\s+pr\s+create(?=$|[\s;&|)])")
SKIP = "CLINS_FORK_REVIEW=skip"
SETTING = re.compile(
    r"clins:fork-review(?:\s+([\w.-]+/[\w.-]+))?\s*:\s*(.*)", re.IGNORECASE
)
REPO_FILES = ("CLAUDE.local.md", "AGENTS.md", "CLAUDE.md")
GH_TIMEOUT = 6


class CheckFailed(Exception):
    pass


def run(args, cwd=None):
    try:
        out = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=GH_TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise CheckFailed(f"`{' '.join(args[:3])}` failed: {e}")
    if out.returncode != 0:
        raise CheckFailed(f"`{' '.join(args[:3])}` failed: {out.stderr.strip()[:200]}")
    return out.stdout.strip()


def parse_command(command):
    """Return the flags of the first `gh pr create` in a shell command, or None."""
    m = PR_CREATE.search(command)
    if not m:
        return None
    rest = command[m.end():]
    rest = re.split(r"&&|\|\||;|\n|\|", rest, maxsplit=1)[0]
    try:
        words = shlex.split(rest)
    except ValueError:
        words = rest.split()
    flags = {}
    names = {"-R": "repo", "--repo": "repo", "-H": "head", "--head": "head",
             "-B": "base", "--base": "base"}
    i = 0
    while i < len(words):
        w = words[i]
        key, _, value = w.partition("=")
        if key in names:
            if not value and i + 1 < len(words):
                i += 1
                value = words[i]
            flags[names[key]] = value
        i += 1
    return flags


def parse_setting(text):
    """Return {"mode", "fork"} values found in one setting line's text."""
    out = {}
    for part in text.split(";"):
        words = part.strip().split()
        if len(words) >= 2 and words[0].lower() == "mode":
            mode = words[1].lower().strip(".,")
            if mode in ("ask", "fork", "origin"):
                out["mode"] = mode
        elif len(words) >= 2 and words[0].lower() == "fork" and "/" in words[1]:
            out["fork"] = words[1].strip(".,")
    return out


def setting_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    return [m.groups() for m in map(SETTING.search, text.splitlines()) if m]


def read_setting(repo, repo_root, global_file):
    """Merge the setting for `repo`: repo files first, then the user's global
    file. In each file a line scoped to the repo wins over a plain line."""
    sources = [os.path.join(repo_root, f) for f in REPO_FILES] if repo_root else []
    sources.append(global_file)
    merged = {}
    for path in sources:
        lines = setting_lines(path)
        scoped = [t for r, t in lines if r and r.lower() == repo.lower()]
        plain = [t for r, t in lines if not r]
        for text in scoped + plain:
            for k, v in parse_setting(text).items():
                merged.setdefault(k, v)
    return merged


def target_repo(flags, cwd):
    if flags.get("repo"):
        return flags["repo"].split("github.com/")[-1].strip("/")
    if os.environ.get("GH_REPO"):
        return os.environ["GH_REPO"]
    return run(["gh", "repo", "view", "--json", "nameWithOwner",
                "-q", ".nameWithOwner"], cwd=cwd)


def login_and_fork(repo):
    owner, name = repo.split("/", 1)
    query = ("query($o:String!,$n:String!){viewer{login} repository(owner:$o,name:$n)"
             "{forks(first:1,affiliations:[OWNER]){nodes{nameWithOwner}}}}")
    data = json.loads(run(["gh", "api", "graphql", "-f", f"query={query}",
                           "-f", f"o={owner}", "-f", f"n={name}"]))["data"]
    nodes = ((data.get("repository") or {}).get("forks") or {}).get("nodes") or []
    return data["viewer"]["login"], (nodes[0]["nameWithOwner"] if nodes else None)


def decision(kind, reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": kind,
                                   "permissionDecisionReason": reason}}


def check(command, cwd, global_file):
    """Return a decision dict, or None to let the command run."""
    flags = parse_command(command)
    if flags is None or SKIP in command:
        return None
    try:
        repo = target_repo(flags, cwd)
    except CheckFailed:
        return None
    try:
        root = run(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    except CheckFailed:
        root = None
    setting = read_setting(repo, root, global_file)
    mode = setting.get("mode")
    if mode not in ("ask", "fork"):
        return None

    try:
        login, fork = login_and_fork(repo)
        if repo.split("/")[0].lower() == login.lower():
            return None
        fork = setting.get("fork") or fork
        if not fork:
            return None
        head = flags.get("head", "")
        if ":" in head:
            head = head.split(":", 1)[1]
        head = head or run(["git", "branch", "--show-current"], cwd=cwd)
        if not head:
            raise CheckFailed("no head branch")
        found = run(["gh", "pr", "list", "-R", fork, "--head", head, "--state", "all",
                     "--json", "url", "-q", ".[0].url"])
    except (CheckFailed, KeyError, ValueError) as e:
        return decision("ask", f"clins:fork-review (mode {mode}): could not check for a "
                        f"review PR on your fork of {repo} ({e}). Allow only if this PR "
                        "should go straight to upstream.")
    if found:
        return None
    if mode == "ask":
        return decision("ask", f"clins:fork-review: this opens a PR straight on {repo}, "
                        f"with no PR for '{head}' on your fork {fork}. Your mode is ask: "
                        "allow to go straight to upstream, or deny and run clins:fork-review.")
    return decision("deny", f"clins:fork-review: mode is fork for {repo}, and your fork "
                    f"{fork} has no PR for branch '{head}'. Run clins:fork-review to open "
                    "and review the PR on the fork first. To go straight to upstream "
                    f"anyway, get the user's explicit OK, then rerun with {SKIP} "
                    "in front of the command.")


def main():
    try:
        data = json.load(sys.stdin)
        command = data["tool_input"]["command"]
    except (ValueError, KeyError, TypeError):
        return
    if not isinstance(command, str) or not PR_CREATE.search(command):
        return
    cwd = data.get("cwd") or os.getcwd()
    global_file = os.path.join(os.path.expanduser("~"), ".claude", "CLAUDE.md")
    result = check(command, cwd, global_file)
    if result:
        print(json.dumps(result))


def self_test():
    import tempfile

    assert parse_command("git push && gh pr list") is None
    assert parse_command("echo gh pr create-thing") is None
    assert parse_command("gh pr create -R a/b --head x:y --title 't t'") == \
        {"repo": "a/b", "head": "x:y"}
    assert parse_command("cd d && gh pr create --repo=a/b -B main | cat") == \
        {"repo": "a/b", "base": "main"}

    assert parse_setting("mode fork; review /greploop, then @alice") == {"mode": "fork"}
    assert parse_setting("mode bogus") == {}
    assert parse_setting("mode ask; fork me/other-name") == \
        {"mode": "ask", "fork": "me/other-name"}

    with tempfile.TemporaryDirectory() as d:
        root = os.path.realpath(os.path.join(d, "repo"))
        os.mkdir(root)
        subprocess.run(["git", "init", "-q", root], check=True)
        glob = os.path.join(d, "CLAUDE.md")
        with open(glob, "w") as f:
            f.write("clins:fork-review: mode ask; review /greploop\n"
                    "clins:fork-review up/line: mode fork; fork me/up-line\n")
        assert read_setting("up/line", root, glob) == {"mode": "fork", "fork": "me/up-line"}
        assert read_setting("other/repo", root, glob) == {"mode": "ask"}
        with open(os.path.join(root, "CLAUDE.local.md"), "w") as f:
            f.write("clins:fork-review: mode origin\n")
        assert read_setting("up/line", root, glob) == {"mode": "origin", "fork": "me/up-line"}
        assert check("gh pr create -R up/line", root, glob) is None
        assert check(f"{SKIP} gh pr create -R up/line", root, glob) is None
        assert read_setting("x/y", None, os.path.join(d, "missing")) == {}
    print("ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        self_test()
    else:
        main()
