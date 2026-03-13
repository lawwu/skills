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
| [review-code](plugins/lawwu-skills/skills/review-code/SKILL.md) | Review code using an external AI model (Codex by default, Claude Code as fallback). Asks for scope before starting. |
| [skill-creator](plugins/lawwu-skills/skills/code-simplifier/SKILL.md) | Create new skills, modify and improve existing skills, and measure skill performance |

## Available Subagents

| Subagent | Description |
|----------|-------------|
| [code-simplifier](plugins/lawwu-skills/agents/code-simplifier.md) | Simplifies and refines code for clarity, consistency, and maintainability while preserving all functionality |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, skill templates, vendoring policy, and the PR workflow.

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
