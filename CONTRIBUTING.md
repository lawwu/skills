# Contributing

## Philosophy

This repository favors **incremental change** over perfection. Skills are living documents that improve over time through small, iterative updates.

- **Bias toward action** - Ship small improvements rather than waiting for the perfect solution
- **Self-review is the default** - You know your changes best
- **Iterate freely** - Don't hesitate to refine existing skills

## Prerequisites

Install [prek](https://github.com/getsentry/prek) for pre-commit linting:

```bash
pip install prek
pre-commit install
```

## Local Development

```bash
git clone git@github.com:lawwu/skills.git ~/lawwu-skills
claude plugin marketplace add ~/lawwu-skills
claude plugin install lawwu-skills
```

## Testing Skills

Before merging, test your changes locally:

1. **Install the plugin from your local clone** (see above)
2. **Restart Claude Code** to pick up changes
3. **Invoke the skill** in a relevant context

   ```bash
   # Explicit invocation
   /skill-name

   # Or describe a task that should trigger the skill
   ```

4. **Verify behavior** - Check that the skill produces the expected guidance and handles edge cases appropriately

## Pull Request Workflow

All changes go through the PR flow, but formal review is optional.

- **Self-review and merge** when you're confident in your change
- **Request review** only when you want a second pair of eyes
- Keep PRs focused - one skill or one improvement per PR when practical

## Adding a New Skill

1. Create `plugins/lawwu-skills/skills/<skill-name>/SKILL.md`

2. Add required YAML frontmatter:

   ```yaml
   ---
   name: skill-name
   description: What this skill does. Include trigger keywords.
   ---
   ```

3. Update `README.md` to add the skill to the Available Skills table in alphabetical order

4. Add the skill to `.claude/settings.json`:

   ```json
   "Skill(lawwu-skills:skill-name)"
   ```

## Skill Template

Create a new directory under `plugins/lawwu-skills/skills/`:

```
plugins/lawwu-skills/skills/my-skill/
└── SKILL.md
```

**SKILL.md format:**

```yaml
---
name: my-skill
description: A clear description of what this skill does and when to use it. Include keywords that help agents identify when this skill is relevant.
---

# My Skill Name

## Instructions

Step-by-step guidance for the agent.

## Examples

Concrete examples showing expected input/output.

## Guidelines

- Specific rules to follow
- Edge cases to handle
```

### Naming Conventions

- **name**: 1-64 characters, lowercase alphanumeric with hyphens only
- **description**: Up to 1024 characters, include trigger keywords
- Keep SKILL.md under 500 lines; split longer content into reference files

### Optional Fields

| Field | Description |
|-------|-------------|
| `license` | License name or path to license file |
| `compatibility` | Environment requirements (max 500 chars) |
| `allowed-tools` | Comma-separated list of tools the skill can use |
| `metadata` | Arbitrary key-value pairs for additional properties |

```yaml
---
name: my-skill
description: What this skill does
license: MIT
allowed-tools: Read, Grep, Glob
---
```

## Vendoring Skills

When vendoring a skill or agent from an external source, retain proper attribution:

1. **Add a comment** at the top of the file referencing the original source:
   ```markdown
   <!--
   Based on [Original Name] by [Author/Org]:
   https://github.com/example/original-source
   -->
   ```

2. **Include a LICENSE file** in the skill directory if the original has specific licensing requirements.

### Example: code-simplifier

The `code-simplifier` agent is vendored from [Anthropic's official plugins](https://github.com/anthropics/claude-plugins-official). See the attribution comment at the top of the agent file.

## Repository Structure

```
lawwu-skills/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace manifest
├── plugins/
│   └── lawwu-skills/
│       ├── .claude-plugin/
│       │   └── plugin.json   # Plugin manifest
│       ├── agents/
│       │   └── code-simplifier.md
│       └── skills/
│           └── <skill-name>/
│               └── SKILL.md
├── AGENTS.md                 # Agent-facing documentation
├── CLAUDE.md                 # Symlink to AGENTS.md
└── README.md
```
