---
name: create-skills-marketplace
description: Scaffold a new Claude Code skills marketplace using the cookiecutter template at https://github.com/lawwu/skills-marketplace. Use this skill when the user asks to "create a skills marketplace", "set up a new skills repo", "scaffold a plugin marketplace", "create a new skills plugin", or wants to start a new agent skills repository from scratch.
---

# Create Skills Marketplace

Scaffold a new Claude Code skills marketplace from the cookiecutter template at `gh:lawwu/skills-marketplace`.

## Step 1: Gather inputs

Ask the user for the following before running anything:

| Variable | Description | Example |
|----------|-------------|---------|
| `repo_name` | Repository and marketplace name | `acme-skills` |
| `author_name` | Your full name | `Jane Smith` |
| `github_username` | Your GitHub handle | `janesmith` |
| `plugin_description` | One-line description of the plugin | `Agent skills for ACME engineers` |
| `license` | License choice | `MIT` (options: MIT, Apache-2.0, GPL-3.0, BSD-3-Clause, Unlicense) |

`plugin_name` and `skill_marketplace_name` are derived automatically from `repo_name`.

If the user is clearly in a hurry or already has values in mind, accept them inline rather than asking question by question.

## Step 2: Check prerequisites

```bash
# Check cookiecutter is available
if ! command -v cookiecutter &> /dev/null; then
  echo "cookiecutter not found — install with: pip install cookiecutter"
  exit 1
fi
```

If missing, tell the user to run `pip install cookiecutter` and then retry.

## Step 3: Run cookiecutter

Use `--no-input` with explicit variable overrides so nothing is left interactive:

```bash
cookiecutter gh:lawwu/skills-marketplace --no-input \
  repo_name="<repo_name>" \
  author_name="<author_name>" \
  github_username="<github_username>" \
  plugin_description="<plugin_description>" \
  license="<license>"
```

Run this in the directory where the user wants the new repo created (ask if unclear — default to current directory).

## Step 4: Confirm what was generated

After cookiecutter completes, show the user the top-level structure:

```bash
find <repo_name> -maxdepth 3 | sort
```

Call out the key pieces:
- `plugins/<plugin_name>/skills/` — where new skills go
- `.claude-plugin/marketplace.json` — marketplace manifest
- `.github/workflows/` — CI workflows (claude.yml, skill-review.yml, prek.yml)
- `AGENTS.md` / `CLAUDE.md` (symlink) — agent instructions
- `.agents/skills` (symlink) — skills.sh compatibility

## Step 5: Post-setup checklist

Walk the user through these steps:

1. **Initialize git and push to GitHub**
   ```bash
   cd <repo_name>
   git init && git add . && git commit -m "Initial scaffold from lawwu/skills-marketplace"
   gh repo create <github_username>/<repo_name> --public --source=. --push
   ```

2. **Add the API key secret** (required for `claude.yml` and `skill-review.yml` workflows)
   ```bash
   gh secret set ANTHROPIC_API_KEY --body "<your-key>" --repo <github_username>/<repo_name>
   ```

3. **Install locally for development**
   ```bash
   claude plugin marketplace add ~/<repo_name>
   claude plugin install <plugin_name>
   ```
   Restart Claude Code to activate.

4. **Install pre-commit hooks** (optional but recommended)
   ```bash
   cd <repo_name>
   pip install prek && pre-commit install
   ```

## Step 6: Next steps

Point the user to what they can do next:

- Add skills: create `plugins/<plugin_name>/skills/<skill-name>/SKILL.md`
- Use `/skill-creator` to build and iterate on new skills interactively
- Update `AGENTS.md` with any conventions specific to their team
- Add their GitHub username to `.github/CODEOWNERS` so Claude automation is gated to them

## Notes

- The post-generation hook automatically creates both symlinks (`CLAUDE.md → AGENTS.md` and `.agents/skills → ../plugins/<plugin_name>/skills`). No manual symlink step needed.
- On Windows the hook falls back to copying `AGENTS.md` as `CLAUDE.md` since symlinks require elevated permissions.
