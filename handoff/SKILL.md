---
name: handoff
description: Session handoff and crash recovery for Claude Code. Auto-applies on /handoff, /recover, or when a session starts with a pending handoff file.
---

# Handoff

Session continuation for Claude Code. Builds forward-looking handoff docs so work survives context limits, session exits, and voluntary compaction.

## The Problem

Claude Code sessions die. Context windows overflow mid-task. Long sessions get sluggish. You want to pivot focus without losing what you've built up. When a new session starts, it has zero memory of the previous one.

The handoff skill bridges that gap: distill what matters into a handoff doc, clear context, reload clean.

## Triggers

- `/handoff` — voluntary compaction of current session
- `/handoff "focus on X"` — filtered handoff, keeping only what serves goal X
- `/recover` — recover from the most recent crashed/exited session
- `/recover <session-id>` — recover from a specific session
- `/recover "focus on X"` — recover with focus filter
- Session start: auto-detect pending handoff file

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/handoff` | Distill current session into handoff doc |
| `/handoff "focus on X"` | Handoff filtered to serve goal X |
| `/recover` | Recover from most recent dead session |
| `/recover <id> "focus"` | Recover specific session with filter |

## How It Works

### Voluntary Handoff (/handoff)

For live sessions — you already have full context. The agent:

1. **Captures environment state** — git status, branch, dirty files, HEAD SHA
2. **Synthesizes the handoff doc** from current conversation context
3. **Presents summary** for user review/correction
4. **Writes** the handoff doc to disk
5. **Outputs reload instructions** — user clears context and reloads

### Crash Recovery (/recover)

For dead sessions — must reconstruct context from the session transcript (JSONL). Uses a hybrid extraction pipeline:

#### Phase 1: Structural Pre-Index (deterministic, no LLM)

Parse the session JSONL and build a lightweight index:
- Message list with roles and approximate timestamps
- Tool calls with names, output sizes, first/last N characters
- Agent (subagent) dispatches and their completion results
- File paths and commands mentioned
- Where the session died and why (context overflow, rate limit, user exit, error)

This phase is fast and cheap — pure parsing, no inference.

#### Phase 2: Backbone Extraction

Extract all user messages and assistant text responses. Skip tool calls, tool results, and thinking blocks.

This is the conversation as the user experienced it. It captures intent, decisions, and direction. It is always relatively small regardless of session length because tool I/O dominates token usage.

#### Phase 3: Agent/Subagent Results

Extract all Task tool dispatches paired with their completion results. In Claude Code, subagent results often arrive as `<task-notification>` messages.

These represent completed work — often the highest-value content in a session. A research agent that returned 10K chars of analysis is worth preserving; the 50 tool calls it made internally are not.

#### Phase 4: Dynamic Deep Dives (LLM loop, budget-capped)

The LLM reads the backbone + agent results and identifies gaps:
- What decisions were made but aren't clear from the backbone alone?
- What tool outputs contain critical information not captured elsewhere?
- What was in-flight when the session died?

It then requests specific tool results by index from the pre-built index. After each retrieval, it reassesses: do I have enough to write a good handoff? Or do I need more?

**Budget caps:** Max 10 deep dive iterations. Max 50K tokens of tool output read. If budget is exhausted, produce handoff with explicit `known_gaps` section.

**Fallback:** If the JSONL is corrupted or unparseable, produce a minimal handoff from: the last 10% of the file + git state + explicit "NEEDS HUMAN TRIAGE" flag.

#### Phase 5: Synthesis

Combine all extracted context into the handoff doc. Apply focus filter if provided — but hazards are never filtered.

## The Handoff Doc

The handoff doc is a **briefing for the next session**, not a history of the last one. It answers: "What do you need to know to continue?"

### Format

```markdown
---
type: handoff
created: 2025-03-15T14:30:00
source_session: <session-id or "live">
lineage: [<previous handoff timestamps if chained>]
focus_filter: <null or "focus description">
confidence: <high|medium|low>
---

# Handoff: <Brief Goal Description>

## Goal
<One paragraph: what we're doing and why>

## Done
<Completed work with file references and evidence>
- Built auth middleware → `src/middleware/auth.ts` (lines 40-120)
- Generated migration → `db/migrations/003_add_sessions.sql`
- Tests passing for auth flow (12/12)

## Next
<Specific actionable items, ordered by priority>
1. Wire up the logout endpoint
2. Add rate limiting to login
3. Update API docs

## Hazards (never filtered)
<Landmines, constraints, things that apply regardless of focus>
- Don't touch `config/prod.yaml` — half-migrated state
- Auth tokens expire at 3pm PT — test before then
- User said "never auto-commit"
- Migration 003 applied locally but not pushed

## Key Context
<Decisions, preferences, constraints that only exist in session memory>
- Decided JWT over sessions (stateless, simpler for mobile)
- User prefers explicit error messages over codes
- Tried Passport.js first, switched to custom middleware (simpler)

## Environment
```
Branch: feature/auth
HEAD: abc1234 "add session table migration"
Dirty files:
  M src/middleware/auth.ts
  M src/routes/login.ts
  ?? src/routes/logout.ts
```

## Files to Read
**For context:** (understand the situation)
- `src/middleware/auth.ts` — the new auth middleware
- `docs/auth-design.md` — design doc from earlier discussion

**To modify next:** (where work continues)
- `src/routes/logout.ts` (just created, incomplete)
- `src/routes/login.ts` (needs rate limiting added)

## Verify Before Continuing
- [ ] `npm test` passes (was green at end of last session)
- [ ] Migration 003 is applied to local DB
- [ ] Login endpoint returns JWT (not session cookie)

## Known Gaps (if any)
<What the extraction couldn't determine — be honest>
- Couldn't read the test output from the last run (session died mid-output)
- Unclear whether user approved the error message format
```

### Sections Explained

| Section | Purpose | Filtered by focus? |
|---------|---------|-------------------|
| **Goal** | What we're trying to accomplish | No |
| **Done** | Completed work with evidence | Yes |
| **Next** | Ordered action items | Yes |
| **Hazards** | Landmines and constraints | **Never** |
| **Key Context** | Session-only knowledge | Partially |
| **Environment** | Git state snapshot | No |
| **Files to Read** | What to load for context vs. modify | Yes |
| **Verify** | Sanity checks before proceeding | No |
| **Known Gaps** | Honest about uncertainty | No |

## Key Principles

### Forward-looking, not backward-looking
The doc is a briefing, not a history. "What do you need to know to continue?" — not "What happened in the last session?"

### Minimum viable context
Only include what's needed. If information lives in a file on disk, reference the file path instead of reproducing content. The next session can read files; it can't read dead context.

### Hazards survive all filters
The "Hazards" section is NEVER removed by focus filtering. Safety constraints, "don't touch X", partial migrations, uncommitted state — these apply regardless of what you're working on next.

### Honest about uncertainty
If extraction couldn't determine something, say so in Known Gaps. A wrong handoff is worse than an incomplete one. The next session needs to know what it doesn't know.

### Lineage tracking
Every handoff includes its chain of previous handoffs (timestamps in the `lineage` field). This prevents multi-hop information decay. Previous handoff hazards are pulled forward verbatim, not re-summarized through another layer of LLM interpretation.

### Environment is ground truth
Git status, branch, HEAD SHA, dirty files — these are deterministic facts captured at handoff time. They anchor the handoff in reality and catch drift (e.g., "the handoff says we're on `feature/auth` but we're actually on `main`").

## The Reload Workflow

After the handoff doc is written:

1. The agent tells the user: "Handoff ready. Run `/clear` then paste:"
2. User clears context (or starts a new session)
3. User pastes: `Read handoff.md and confirm you have context`
4. New session reads the file, confirms key details, and continues from "Next"
5. The handoff file is archived after consumption

For crash recovery, the flow is the same — the skill just does extra work (JSONL parsing) before producing the handoff doc.

### Auto-detection (recommended)

Configure your agent to check for a pending handoff file on session start. If one exists, read it, present the summary, and ask: "Continuing from handoff — ready to proceed, or want to adjust focus?"

## Session JSONL Format

Claude Code stores session transcripts as JSONL files in `~/.claude/projects/<project-dir>/`. Each line is a JSON object with this structure:

```
{type: "user",      message: {role: "user",      content: "..."}, uuid: "...", timestamp: "..."}
{type: "assistant",  message: {role: "assistant",  content: [{type: "text", text: "..."}, {type: "tool_use", ...}]}, ...}
{type: "tool_result", message: {role: "tool",      content: "..."}, ...}
```

Subagent results arrive as user messages containing `<task-notification>` XML with `<task-id>`, `<summary>`, and `<result>` tags.

Session files can be 10-100MB+ for long sessions. The layered extraction approach avoids reading the entire file into context.

## Adaptation Guide

This skill is designed to be **copied into any Claude Code project** and adapted. Key integration points:

1. **Handoff file location** — default is `handoff.md` in your project root or scratch directory. Change to wherever makes sense for your project.

2. **Archive location** — old handoffs go to a subdirectory. Keeps last 5 by default.

3. **Session start hook** — add a check for the pending handoff file in your project's CLAUDE.md under session start instructions.

4. **Environment capture** — the default captures git state. Add project-specific state (running services, database status, test results) as needed.

5. **Focus filtering** — define what "hazards" means for your project. Database migrations, deployment state, and user-stated constraints are good defaults.

## Design Rationale

This skill was designed with input from a council of frontier models (Claude, GPT, Gemini, Grok). Key design decisions:

- **Hybrid extraction** (structural parse + LLM synthesis) rather than pure LLM reading of session files. The structural pass is fast, cheap, and reliable. The LLM adds judgment about what matters.

- **Budget-capped deep dives** rather than "read everything." Most session content is tool I/O that doesn't need to survive the handoff. The LLM decides what to dig into based on gaps in understanding.

- **Unfilterable hazards** inspired by the observation that focus filters can accidentally drop safety-critical context. "Don't touch prod" applies whether you're working on auth or UI.

- **Lineage tracking** because handoff chains (session → handoff → session → handoff → session) compound information loss at each hop. Pulling forward hazards verbatim prevents the game-of-telephone effect.

- **Verification checklist** because LLM-generated summaries can hallucinate completed work or invent decisions. The checklist gives the next session concrete things to spot-check before proceeding.
