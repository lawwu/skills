# Contributing

## Philosophy

This repository favors **incremental change** over perfection. Skills are living documents that improve over time through small, iterative updates.

- **Bias toward action** - Ship small improvements rather than waiting for the perfect solution
- **Self-review is the default** - You know your changes best
- **Iterate freely** - Don't hesitate to refine existing skills

## Testing Skills

Before merging, test your changes locally:

1. **Install the plugin from your local clone**

   ```bash
   claude plugin marketplace add ~/path/to/lawwu-skills
   claude plugin install lawwu-skills
   ```

2. **Restart Claude Code** to pick up changes

3. **Invoke the skill** in a relevant context

   ```bash
   # For explicit invocation
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

3. Update `README.md` to add the skill to the Available Skills table in alphabetical order by skill name

4. Add the skill to `.claude/settings.json`:

   ```json
   "Skill(lawwu-skills:skill-name)"
   ```

See [README.md](README.md) for the full skill template and optional frontmatter fields.
