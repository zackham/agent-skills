# agent-skills

Reusable skills for Claude Code and other AI coding agents. Each skill is a self-contained protocol defined in a `SKILL.md` file that teaches the agent how to handle a specific class of task.

## What's a Skill?

A skill is a markdown file that gives an AI agent structured instructions for a specific capability. Drop it into your `.claude/skills/` directory (or equivalent) and the agent learns the protocol.

Skills are **prompts, not code**. They define the *what* and *why* — the agent figures out the *how* using its available tools. Some skills include optional Python utilities for heavy lifting (parsing, file I/O), but the core is always the SKILL.md.

## Available Skills

| Skill | Description |
|-------|-------------|
| [handoff](handoff/) | Session handoff and crash recovery. Bridges context across session boundaries. |

## Usage

### Claude Code

Copy the skill directory into your project:

```bash
cp -r handoff/ your-project/.claude/skills/handoff/
```

Reference it in your project's `CLAUDE.md`:

```markdown
## handoff & recovery

> skill: `.claude/skills/handoff/`

Session continuation across context limits and voluntary compaction.
```

### Other Agents

The SKILL.md files are agent-agnostic markdown. Adapt the protocol to your agent's tool interface. The core ideas (layered extraction, forward-looking briefings, unfilterable hazards) apply regardless of platform.

## Contributing

Open to contributions. Each skill should:
- Be self-contained in its own directory
- Have a `SKILL.md` with clear triggers, protocol, and examples
- Solve a real problem you've hit in practice
- Be agent-agnostic where possible (Claude Code specifics in adaptation guides)

## License

MIT
