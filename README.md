# lawwu-skills

Agent skills for Claude Code, Codex and other coding agents following the [Agent Skills](https://agentskills.io) open format.

## Installation

### Claude Code

```bash
claude plugin marketplace add lawwu/skills
claude plugin install lawwu-skills@lawwu-skills
```

Restart Claude Code after installation. Skills activate automatically when relevant.

**Update:**

```bash
claude plugin marketplace update
claude plugin update lawwu-skills@lawwu-skills
```

Or run `/plugin` to open the plugin manager.

### Skills Package (skills.sh)

For agents supporting the [skills.sh](https://skills.sh) ecosystem:

```bash
npx skills add lawwu/skills
```

## Available Skills

| Skill | Description |
|-------|-------------|
| [skill-creator](plugins/lawwu-skills/skills/code-simplifier/SKILL.md) | Create new skills, modify and improve existing skills, and measure skill performance |

## Available Subagents

| Subagent | Description |
|----------|-------------|
| [code-simplifier](plugins/lawwu-skills/agents/code-simplifier.md) | Simplifies and refines code for clarity, consistency, and maintainability while preserving all functionality |

## Contributing

### Local Development

```bash
git clone git@github.com:lawwu/skills.git ~/lawwu-skills
claude plugin marketplace add ~/lawwu-skills
claude plugin install lawwu-skills
```

### Repository Structure

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
│           └── code-simplifier/
│               └── SKILL.md
├── AGENTS.md                 # Agent-facing documentation
├── CLAUDE.md                 # Symlink to AGENTS.md
└── README.md                 # This file
```

### Creating New Skills

Skills follow the [Agent Skills specification](https://agentskills.io/specification). Each skill requires a `SKILL.md` file with YAML frontmatter.

#### Skill Template

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

#### Naming Conventions

- **name**: 1-64 characters, lowercase alphanumeric with hyphens only
- **description**: Up to 1024 characters, include trigger keywords
- Keep SKILL.md under 500 lines; split longer content into reference files

#### Optional Fields

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

### Vendoring Skills

When vendoring a skill or agent from an external source, retain proper attribution:

1. **Add a comment** at the top of the file referencing the original source:
   ```markdown
   <!--
   Based on [Original Name] by [Author/Org]:
   https://github.com/example/original-source
   -->
   ```

2. **Include a LICENSE file** in the skill directory if the original has specific licensing requirements.

#### Example: code-simplifier

The `code-simplifier` agent is vendored from [Anthropic's official plugins](https://github.com/anthropics/claude-plugins-official). See the attribution comment at the top of the agent file.

## Inspiration

- [Sentry's skills marketplace](https://github.com/getsentry/skills)
- [claude.yml](https://github.com/anthropics/claude-code-action/blob/f956510b1afc643e768961656c10f7039534d553/examples/claude.yml)
- [validate-frontmatter.yml](https://github.com/anthropics/claude-plugins-official/blob/b36fd4b753018b0b340803579399992a32e43502/.github/workflows/validate-frontmatter.yml)

## References

- [Claude Skills](https://code.claude.com/docs/en/skills)
- [Claude Plugins](https://code.claude.com/docs/en/plugins)
- [Agent Skills Specification](https://agentskills.io/specification)

## License

MIT
