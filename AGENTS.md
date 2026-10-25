Skills live one per folder under `skills/` (`skills/<name>/SKILL.md`). Claude Code loads them through the `clins` plugin (`.claude-plugin/plugin.json`, listed in `.claude-plugin/marketplace.json`), and `npx skills` finds the same folders.

Name a skill's folder and its `name:` without a prefix (`skills/create-pr/`, `name: create-pr`). The plugin adds the prefix: Claude Code shows the skill as `/clins:create-pr`. When one skill refers to another, write `clins:<name>`.

Every skill must be listed in the top-level `README.md`, with its name linked to its `SKILL.md`.

Keep skills general enough for anyone to use: no org names, private repos, channel IDs or internal metrics. Use placeholders such as `<owner>/<repo>` and `ENG-123`, and read team conventions from the target repo's `AGENTS.md`/`CLAUDE.md` at run time.

A skill can be installed alone, or with only some of the others (a team pack may pick a few). So:

- A skill never names the skills that call it. Describe what a caller can pass instead (an input, a setting). The calling skill names the skill it calls, not the other way round.
- When a skill hands off to another skill that is not one of its basic dependencies (`post`, and the host skill such as `github`), make the step conditional: "if `clins:<name>` is installed", with what to do without it.

Run `claude plugin validate .` after you add a skill or change a manifest.

Bump `version` in `.claude-plugin/plugin.json` in every PR that changes a skill or a manifest. Use semver: a minor bump for a new skill, a patch bump for fixes. `claude plugin update` compares this version, so without a bump installed copies do not update.
