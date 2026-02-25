# agent-skills

Reusable skills for Claude Code and other AI coding agents. Each skill is a self-contained protocol defined in a `SKILL.md` file that teaches the agent how to handle a specific class of task.

## What's a Skill?

A skill is a markdown file that gives an AI agent structured instructions for a specific capability. Skills are **prompts, not code**. They define the *what* and *why* — the agent figures out the *how* using its available tools.

## Available Skills

| Skill | Description |
|-------|-------------|
| [handoff](handoff/) | Session handoff and crash recovery. Bridges context across session boundaries. |

## Usage

Point your agent at this repo and ask it to evaluate the skills and adapt them for your codebase. Something like:

> Read https://github.com/zackham/agent-skills and evaluate which skills would be useful here. Adapt any relevant ones for our project.

The agent will read the SKILL.md files, understand the protocols, and integrate what makes sense for your setup. It'll handle the adaptation — file paths, project conventions, tooling specifics.

If you'd rather do it manually: copy a skill directory into `.claude/skills/` and reference it in your `CLAUDE.md`.

## License

MIT
