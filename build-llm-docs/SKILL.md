---
name: build-llm-docs
description: Generate high-quality CLAUDE.md / AGENTS.md / LLM instruction files for codebases. Auto-applies when user says "build llm instructions", "generate CLAUDE.md", "write AGENTS.md", or "build docs for this codebase".
---

# Build LLM Docs

Generate excellent CLAUDE.md files that turn an LLM into a dangerous contributor within minutes. Not onboarding docs. Not READMEs. Mission briefings.

## Triggers

- "build llm instructions for this codebase"
- "generate CLAUDE.md"
- "write AGENTS.md for X"
- "build docs for the payments feature"
- "update CLAUDE.md"

## What Makes a CLAUDE.md Excellent vs Mediocre

**Mediocre:** Describes the codebase like a wiki. Generic advice ("follow best practices"). File tree dumps. Pasted dependency lists.

**Excellent:** Enables correct first PRs without human hand-holding. Every statement is specific to THIS repo. Every instruction is executable. An LLM reading only this file can safely modify the codebase.

The bar: if an agent reads this doc and implements a small feature, do they get it right on the first try?

---

## The Process (5 Phases)

### Phase 1: Scout (1 agent, always first)

Before spawning exploration agents, run a single scout to map the territory. This determines how to partition the real work.

```
Task tool (subagent_type: Explore)
Prompt: "Explore this codebase and produce a repo map. I need:
1. Tech stack with versions (check package.json, Gemfile, pyproject.toml, go.mod, etc.)
2. Top 10-15 most important files/directories and what they do
3. Application topology (monolith? microservices? workers? web + API?)
4. Entrypoints (where does execution start? main files, route definitions, CLI commands)
5. Build/test/lint commands (check Makefile, package.json scripts, CI configs)
6. Any existing CLAUDE.md, AGENTS.md, CONTRIBUTING.md, or similar docs

Output as structured sections. Be specific - file paths, not descriptions."
```

The scout output determines:
- Which deep-dive agents to spawn (skip frontend agent if no frontend)
- Which directories matter (don't waste agents on vendored code)
- What existing docs say (build on them, don't duplicate)

### Phase 2: Deep Dive (3-7 agents in parallel)

Spawn agents by **concern**, not by directory. Directory-based exploration produces file listings, not operational knowledge.

Launch all applicable agents simultaneously using parallel Task tool calls. Each agent gets a tightly scoped mission with required deliverables.

#### Agent Selection

Pick from this menu based on what the scout found. Skip agents that don't apply.

**Always include:**

1. **Runtime & Entrypoints Agent**
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "You are analyzing [CODEBASE] to document how it runs.

MISSION: Map how the application starts, handles requests, and processes work.

DELIVERABLES:
1. Application boot sequence (what happens on startup)
2. Request lifecycle: HTTP request → routing → controller/handler → response
3. Background jobs / async processing (if any): how they're defined, enqueued, processed
4. CLI commands or scripts meant to be run directly
5. Key middleware, interceptors, or hooks in the request pipeline

EVIDENCE RULES: Every claim must cite file:line_number. Trace at least 2 complete request paths end-to-end.

STOP WHEN: You've traced 2+ request flows and identified all entrypoints."
```

2. **Patterns & Conventions Agent**
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "You are analyzing [CODEBASE] to extract coding conventions.

MISSION: Document the patterns an LLM must follow to write code that belongs here.

DELIVERABLES:
1. File organization: where new files of each type go (models, services, tests, etc.)
2. Naming conventions (files, classes, functions, variables, DB columns)
3. Error handling pattern (how errors are raised, caught, reported)
4. Logging pattern (what logger, what format, what gets logged)
5. The 'how to add a new X' recipes:
   - New API endpoint
   - New DB migration / model
   - New background job
   - New test
6. Anti-patterns: things the codebase explicitly avoids (look at linter configs, code reviews, comments saying 'don't do X')
7. Import/dependency patterns (DI? service locator? direct imports?)

EVIDENCE RULES: For each convention, cite 2-3 examples showing the pattern in use. If you find linter/formatter configs, extract the non-default rules.

STOP WHEN: You can answer 'where does new code go?' and 'what patterns must it follow?' with specifics."
```

3. **Testing & Quality Agent**
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "You are analyzing [CODEBASE] to document testing practices.

DELIVERABLES:
1. Test framework and runner (exact commands to run all tests, one test file, one test case)
2. Test file organization (where tests live, naming conventions, how they map to source)
3. Fixture/factory patterns (how test data is created)
4. Mocking patterns (what gets mocked, what doesn't, preferred mocking library)
5. Integration vs unit test conventions
6. CI pipeline: what runs on PR, what blocks merge
7. Common test helpers or shared utilities
8. Known flaky tests or test gotchas

EVIDENCE RULES: Include exact runnable commands. Verify they exist in scripts/CI config."
```

**Include when applicable:**

4. **Data & Persistence Agent** (if DB/storage exists)
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "You are analyzing [CODEBASE] to document data storage.

DELIVERABLES:
1. Database type, ORM/query layer, connection config location
2. Schema location (migrations dir, schema file)
3. How to run migrations (commands for create, migrate, rollback, seed)
4. Core entities (top 5-10 models) and their relationships
5. Data access patterns: repository pattern? active record? raw queries?
6. Transaction boundaries and locking patterns
7. Caching layers (what's cached, where, invalidation strategy)
8. Two traced data flows:
   - A write path (user action → validation → persist → side effects)
   - A read path with joins/aggregations

EVIDENCE RULES: Cite schema files, model files, migration examples."
```

5. **Frontend/UI Agent** (if frontend exists)
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "You are analyzing [CODEBASE] to document the frontend.

DELIVERABLES:
1. Framework, build tool, state management approach
2. Component organization (where components live, naming, structure)
3. Styling approach (CSS modules? Tailwind? styled-components?)
4. API integration pattern (how frontend calls backend, client libraries)
5. Routing structure
6. Key shared components or design system
7. Build commands (dev server, production build, storybook if exists)

EVIDENCE RULES: Cite component files, config files, key patterns with examples."
```

6. **DevOps & Environment Agent** (for complex setups)
```
Task tool (subagent_type: Explore, thoroughness: medium)
Prompt: "You are analyzing [CODEBASE] to document local development setup.

DELIVERABLES:
1. How to set up the dev environment from scratch (dependencies, env vars, services)
2. Required external services (databases, caches, queues, third-party APIs)
3. Environment variable catalog (what's required, where .env.example lives)
4. Docker/containerization setup (if any)
5. Deployment process (how code gets to production)
6. Feature flags or environment-specific behavior

EVIDENCE RULES: Include exact commands. Reference docker-compose, .env files, setup scripts."
```

7. **Footgun & Edge Cases Agent** (for mature/complex codebases)
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "You are a security/reliability reviewer analyzing [CODEBASE].

MISSION: Find the top 10 ways an automated agent could break this system.

DELIVERABLES:
1. Auth/permissions gotchas (multitenancy, role checks, API key handling)
2. Data integrity risks (cascading deletes, orphaned records, race conditions)
3. Performance traps (N+1 queries, unbounded queries, missing indexes)
4. Deployment risks (migration order, breaking changes, rollback concerns)
5. Timezone, encoding, or locale gotchas
6. Things that look synchronous but aren't (eventual consistency, async processing)
7. 'Sacred' code that should not be touched without understanding (billing, auth, data export)

EVIDENCE RULES: For each risk, cite the specific code location and the safeguard pattern (or note it's missing)."
```

### Phase 3: Consolidation (2 rounds)

Do NOT single-pass synthesize. Agent outputs will overlap, contradict, and vary in quality.

#### Round 1: Fact Table (1 agent)

Feed ALL agent outputs to a consolidation agent that normalizes them into structured facts.

```
Task tool (subagent_type: general-purpose)
Prompt: "You have exploration reports from [N] agents analyzing a codebase.
Normalize ALL findings into a structured fact table.

For each fact:
- section: which CLAUDE.md section it belongs to (commands, architecture, patterns, data, testing, guardrails, recipes)
- claim: the specific statement
- evidence: file paths, commands, or code references that support it
- confidence: high (directly verified), medium (inferred from patterns), low (single data point)
- source_agents: which agent(s) reported this

CONFLICT HANDLING: If two agents contradict each other, list BOTH claims with evidence and mark as 'CONFLICT - needs resolution'.

DEDUP: Merge identical or near-identical findings. Keep the version with better evidence.

Output the full fact table. Do not summarize or editorialize."
```

Attach all Phase 2 agent outputs to this prompt.

#### Round 2: Draft CLAUDE.md (1 agent)

Feed the fact table to a writing agent with the target document structure.

```
Task tool (subagent_type: general-purpose)
Prompt: "Generate a CLAUDE.md from this fact table. Follow this structure EXACTLY:

## Structure Template

# [Project Name]

## Quick Start
- Install: `exact command`
- Run: `exact command`
- Test: `exact command` (also: run single test: `command`, run with coverage: `command`)
- Lint: `exact command`
- Build: `exact command`

## Architecture
[2-3 paragraphs max. Application topology, major layers, how they connect. NOT a directory listing.]

## Project Structure
[Key directories with their PURPOSE, not contents. 'If you need X, look in Y.' format.]
```
path/to/important/  - what goes here and why
path/to/other/      - what goes here and why
```

## Key Concepts
[Core domain entities, their relationships, critical abstractions. What an LLM needs to understand before touching the code.]

## Request Lifecycle
[1-2 traced paths showing how a request flows through the system. Include file:line references.]

## Data Layer
[DB, ORM, migrations, key models, access patterns. How to safely read/write data.]

## Patterns & Conventions
[Naming, file organization, error handling, logging. 'When adding new X, follow this pattern.' Include examples.]

## Testing
[Framework, commands, file organization, fixture patterns, mocking approach.]

## Common Recipes
### Add a new API endpoint
[Step-by-step with file paths]
### Add a new DB migration
[Step-by-step with file paths]
### Add a new background job
[Step-by-step with file paths]
[Add more recipes as discovered]

## Guardrails
[Things NOT to do. Footguns. 'Never X because Y.' Sacred code. Concurrency concerns. Auth gotchas.]

## Environment
[Required env vars, external services, setup notes.]

---

WRITING RULES:
1. Every command must be copy-pasteable and verified against the codebase
2. Every pattern must cite 2+ file examples
3. Delete any sentence that applies to generic software (not specific to THIS repo)
4. No adjectives ('clean', 'elegant', 'robust'). Only facts and instructions.
5. Prefer tables and bullet lists over prose paragraphs
6. File references use path:line_number format when useful
7. Keep total doc under 3000 lines. Aim for density, not length.
8. If a CONFLICT was flagged and not resolved, include both options with a [NEEDS VERIFICATION] tag

FACT TABLE:
[attach fact table here]"
```

If there were conflicts in the fact table, spawn a resolver agent to check the specific files before this step.

### Phase 4: Review (2-3 agents in parallel)

Review agents have DIFFERENT prompts than exploration agents. They are critics, not discoverers.

**Launch all reviewers in parallel:**

#### Reviewer 1: LLM Usability Test
```
Task tool (subagent_type: general-purpose)
Prompt: "You are Claude Code, dropped into this repo with ONLY the attached CLAUDE.md. No other context.

Simulate implementing this task: 'Add a new API endpoint that returns user statistics.'

Walk through each step you'd take. For EACH step, note:
- Can you do it with info from CLAUDE.md alone? (YES/NO)
- If NO, what's missing?

Then list:
1. Top 5 pieces of missing information that would block you
2. Any commands in the doc you suspect are wrong or incomplete
3. Sections that are too vague to act on (e.g., 'follow standard patterns' without saying what they are)

Be harsh. A usability test that passes everything is useless.

CLAUDE.md:
[attach draft]"
```

#### Reviewer 2: Accuracy Verifier
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "Verify the accuracy of this CLAUDE.md against the actual codebase.

For each section:
1. Pick 3-5 specific claims
2. Check them against the code
3. Flag anything that's wrong, outdated, or misleading

Also check:
- Are the commands actually runnable?
- Do the file paths exist?
- Are the described patterns actually used (not aspirational)?
- Are there important conventions the doc MISSED?

Output a list of corrections (what to fix) and additions (what to add).

CLAUDE.md:
[attach draft]"
```

#### Reviewer 3: Density & Anti-Fluff Check
```
Task tool (subagent_type: general-purpose)
Prompt: "Review this CLAUDE.md for quality and density.

Flag and rewrite:
1. Generic statements that apply to any codebase (delete these)
2. Sections that describe without instructing ('the app uses React' vs 'components go in src/components/, use hooks pattern, see UserProfile.tsx for canonical example')
3. Missing evidence anchors (claims without file references)
4. Redundant sections (same info in multiple places)
5. Sections that are too long for their information density (compress)
6. Missing 'don't do this' guardrails

Output: a revised version of each flagged section with your improvements applied.

CLAUDE.md:
[attach draft]"
```

### Phase 5: Final Assembly (1 agent)

Feed the draft + all reviewer outputs to a final agent.

```
Task tool (subagent_type: general-purpose)
Prompt: "Apply these review findings to the CLAUDE.md draft.

Rules:
1. Fix every accuracy issue the verifier found
2. Fill gaps the usability test identified (search codebase if needed)
3. Apply the density improvements
4. Do NOT add generic filler to fill gaps - if info isn't available, omit the section
5. Ensure all commands are present and formatted for copy-paste
6. Final doc should read like a mission briefing, not a wiki article

Output the complete, final CLAUDE.md.

DRAFT: [attach]
REVIEWER 1 (Usability): [attach]
REVIEWER 2 (Accuracy): [attach]
REVIEWER 3 (Density): [attach]"
```

Write the result to the target file.

---

## Multi-Repo / Multi-Feature Mode

When the target spans multiple repositories or is a feature within a larger codebase:

### Detection
- User specifies multiple paths: "build docs for rails/ and ui/"
- User names a feature: "build docs for the payments feature"
- Scout finds multiple package.json/Gemfile/etc. in subdirectories

### Strategy: Per-Repo Docs + Integration Overlay

1. **Run the full Phase 1-5 pipeline independently for each repo/feature area.** Each gets its own CLAUDE.md that is self-contained and useful on its own.

2. **Spawn an Integration Boundary Agent** after per-repo scouts complete:
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "You are analyzing how [REPO_A] and [REPO_B] integrate for the [FEATURE] feature.

DELIVERABLES:
1. API contracts between repos (endpoints, request/response shapes, auth headers)
2. Shared types, schemas, or generated clients
3. Data flow across the boundary (user action in UI → API call → backend processing → response → UI render)
4. Local dev choreography (what to run, in what order, ports, CORS, proxies)
5. Change protocol: 'if you change X in backend, you must also update Y in frontend'
6. Deploy coordination (migration order, feature flags, breaking change handling)
7. Source of truth for shared definitions (OpenAPI, GraphQL schema, protobufs, shared packages)

EVIDENCE RULES: Cite files in both repos. Trace at least 1 cross-repo flow end-to-end."
```

3. **Integration doc lives in the feature directory** (or primary repo). References per-repo docs, doesn't duplicate them.

### Output Structure for Multi-Repo

```
feature/
  PAYMENTS_LLM_README.md          # Integration overlay (cross-repo concerns)
  api/services/payments/
    PAYMENTS_LLM_README.md         # API-side self-contained doc
  ui/src/features/payments/
    PAYMENTS_LLM_README.md         # UI-side self-contained doc
```

The integration doc's structure:

```markdown
# [Feature Name] - Cross-Repo Context

## Repo Topology
- `api/services/payments/` (API service): Handles [X]. Local docs at [path].
- `ui/src/features/payments/` (React): Handles [Y]. Local docs at [path].

## The Contract
[API endpoints, shared types, versioning rules]

## Cross-Repo Data Flow
[End-to-end trace: user action → UI component → API call → engine controller → service → response → UI state update]

## Development Workflow
1. Start backend: [command]
2. Start frontend: [command]
3. Run integrated tests: [command]

## Change Protocol
- Backend schema change → also update [frontend types/client]
- New API endpoint → also add [frontend API call + hook]
- [Other coupling points]
```

---

## Updating Existing Docs

When CLAUDE.md already exists, do NOT regenerate from scratch.

1. Run Phase 1 (Scout) with additional instruction: "Also read the existing CLAUDE.md at [path] and note what it covers."

2. Run a **Diff Agent** instead of full exploration:
```
Task tool (subagent_type: Explore, thoroughness: very thorough)
Prompt: "Compare this existing CLAUDE.md against the current codebase.

For each section:
- ACCURATE: Still correct, no changes needed
- STALE: Was correct, now outdated (note what changed)
- MISSING: Important info not covered
- WRONG: Incorrect statements

Propose surgical edits - preserve human-written content, only fix/add what's needed.

Existing doc: [attach]"
```

3. Apply the diff. Skip Phases 2-4 unless >40% of the doc is stale/wrong (then do a full regen).

---

## Prompt Design Principles

These apply to ALL agent prompts in this pipeline:

1. **Scoped goal + open evidence gathering.** Tell agents WHAT to find, not WHERE to look. They discover the "where" by exploring.

2. **Required deliverables, not suggestions.** Use numbered lists of specific outputs. Agents work better with checklists than open-ended asks.

3. **Evidence rules.** Every claim must cite file paths. Unanchored advice drifts and lies. Enforce with: "EVIDENCE RULES: every claim must cite file:line_number."

4. **Stop conditions.** Tell agents when they're done. Without this, they either stop too early or spiral. "STOP WHEN: you've traced 2+ flows and identified all entrypoints."

5. **Structured output.** Agents consolidate better when their outputs share structure. Use consistent section headers across deep-dive agents.

6. **No chit-chat.** Add "Do not include introductions, summaries, or meta-commentary. Output findings directly." to any agent that tends to be chatty.

---

## Agent Count Guidelines

| Codebase Size | Scout | Deep Dive | Review | Total |
|--------------|-------|-----------|--------|-------|
| Small (<10k LOC) | 1 | 2-3 | 2 | 5-6 |
| Medium (10k-100k) | 1 | 4-5 | 3 | 8-9 |
| Large (100k+) | 1 | 5-7 | 3 | 9-11 |
| Multi-repo | 1 per repo + 1 integration | 4-5 per repo | 3 | 12-18 |

More agents = more token cost but better coverage. The sweet spot is usually 5 deep-dive agents. Beyond 7, consolidation quality drops unless you add an extra normalization round.

---

## Quality Checklist (verify before delivering)

The final CLAUDE.md must pass ALL of these:

- [ ] Every command is copy-pasteable (no placeholder values without explanation)
- [ ] "How to add a new X" recipes exist for the 2-3 most common modification types
- [ ] File paths reference actual existing files
- [ ] No sentence applies to generic software development
- [ ] Guardrails section exists with at least 3 specific "don't do this" items
- [ ] Architecture section is <500 words and includes a data flow
- [ ] Test commands include: run all, run one file, run one test case
- [ ] At least 1 request/data flow is traced end-to-end with file references
- [ ] No pasted dependency lists or file trees deeper than 2 levels
- [ ] Total doc is under 3000 lines (aim for 500-1500 for most repos)
