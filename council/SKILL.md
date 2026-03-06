---
name: council
description: Multi-model consensus for tough decisions. Fans out questions to frontier AI models via OpenRouter and synthesizes a single answer.
---

# Council

Ask hard questions to multiple frontier models, get back a synthesized answer. Different models have different blindspots and strengths — triangulating across 4 top-tier models and synthesizing beats relying on any single perspective.

## The Problem

Every AI model has systematic biases and blindspots. Claude is cautious and thorough but can over-qualify. GPT tends toward confident consensus answers. Gemini brings strong reasoning but different priors. Grok is direct and contrarian.

For genuinely tough decisions — architecture choices, complex tradeoffs, uncertain domains — you want diverse perspectives, not a single model's take.

## Triggers

- `/council "question"` — ask the council directly
- "ask the council about..." or "what would the council say about..."
- Any complex question where model diversity would help

## What Happens

1. **Context gathering** (optional): search your codebase/docs for relevant background
2. **Question framing**: reframe the raw question with that context so models have what they need
3. **Parallel query**: send to all models simultaneously via OpenRouter
4. **Synthesis**: read all responses and synthesize into a single answer

You only see the synthesis. Raw model outputs stay behind the scenes unless you ask.

## The Models

Top-tier only — these are supposed to be tough questions:

| Model | OpenRouter ID |
|-------|---------------|
| Claude Opus 4.6 | `anthropic/claude-opus-4.6` |
| GPT-5.4 | `openai/gpt-5.4` |
| Gemini 3.1 Pro | `google/gemini-3.1-pro-preview` |
| Grok 4.1 | `x-ai/grok-4.1-fast` |

To customize models, edit the `MODELS` dict in `council.py`.

## Setup

1. Get an [OpenRouter API key](https://openrouter.ai/keys)
2. Set it via environment variable or config file:

```bash
# Option A: environment variable
export OPENROUTER_API_KEY="sk-or-..."

# Option B: config file (path is configurable in council.py)
mkdir -p ~/.config/council
echo '{"api_key": "sk-or-..."}' > ~/.config/council/openrouter.json
```

3. Install the one dependency:

```bash
pip install httpx
# or: uv pip install httpx
```

## Usage

### In a Claude Code session

```
/council "should we use sqlite or postgres for the job queue?"
```

The agent will:
1. Optionally gather context from your codebase
2. Frame the question with that context
3. Query all 4 models in parallel
4. Synthesize: "The consensus is X. GPT and Gemini emphasized Y, while Grok raised Z."

### From the command line

```bash
python council.py "should we use sqlite or postgres for the job queue?"
```

### From Python

```python
from council import ask_council_sync, format_for_synthesis

result = ask_council_sync("your question here")
print(format_for_synthesis(result))
```

### Options

- Pass `include_context=False` to skip codebase context gathering (for general questions)
- Pass a custom `models` list to override the defaults

## When to Use

Good for:
- Technical architecture decisions
- Complex tradeoffs with multiple valid approaches
- Questions where model diversity surfaces different angles
- Triangulating on uncertain topics

Not for:
- Simple factual lookups
- Quick questions with obvious answers
- Anything a single model handles fine

## Cost

Roughly $0.05–0.15 per query depending on response lengths. Uses frontier models so not cheap — but if the question is worth asking multiple models, it's probably worth the cost.

## Adaptation

The script is self-contained (~200 lines, one dependency). To integrate into your project:

1. Copy `council.py` into your project
2. Optionally implement `gather_context()` to search your own data for relevant background
3. Reference this skill in your `CLAUDE.md` so your agent knows about `/council`

The default `gather_context()` is a no-op that passes questions through unchanged. Override it to add project-specific context enrichment.
