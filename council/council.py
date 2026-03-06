"""
Council - Multi-model consensus for tough decisions.

Fans out questions to frontier AI models via OpenRouter and synthesizes responses.
Single file, single dependency (httpx). Designed to be dropped into any project.

Usage:
    python council.py "should we use sqlite or postgres for the job queue?"

    from council import ask_council_sync, format_for_synthesis
    result = ask_council_sync("your question")
    print(format_for_synthesis(result))
"""

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Models — edit this to change the council composition
# ---------------------------------------------------------------------------

MODELS: dict[str, str] = {
    "claude-opus-4.6": "anthropic/claude-opus-4.6",
    "gpt-5.4": "openai/gpt-5.4",
    "gemini-3.1-pro": "google/gemini-3.1-pro-preview",
    "grok-4.1": "x-ai/grok-4.1-fast",
}

# Where to look for the API key file. Override via OPENROUTER_API_KEY env var.
CONFIG_PATH = Path.home() / ".config" / "council" / "openrouter.json"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ModelResponse:
    """Response from a single model."""

    name: str
    content: str
    tokens_in: int
    tokens_out: int
    error: str | None = None


@dataclass
class CouncilResult:
    """Full council result."""

    question: str
    framed_question: str
    context_used: list[str]
    responses: list[ModelResponse]
    total_cost_usd: float


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------


def _get_api_key() -> str:
    """Get OpenRouter API key from env or config file."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f).get("api_key", "")

    raise RuntimeError(
        "OpenRouter API key not found. Set OPENROUTER_API_KEY env var "
        f"or create {CONFIG_PATH} with {{\"api_key\": \"sk-or-...\"}}"
    )


# ---------------------------------------------------------------------------
# Context gathering — override this for project-specific enrichment
# ---------------------------------------------------------------------------


def gather_context(question: str) -> tuple[list[str], str]:
    """
    Search for relevant context and frame the question.

    Override this function to add project-specific context enrichment.
    For example, search your codebase, docs, or knowledge base and prepend
    relevant snippets to the question.

    Returns:
        (context_snippets, framed_question)
    """
    return [], question


# ---------------------------------------------------------------------------
# Model calls
# ---------------------------------------------------------------------------


async def _call_model(
    client: httpx.AsyncClient,
    name: str,
    model_id: str,
    messages: list[dict],
    api_key: str,
) -> ModelResponse:
    """Call a single model via OpenRouter."""
    try:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 65000,
            },
            timeout=httpx.Timeout(connect=30.0, read=900.0, write=30.0, pool=30.0),
        )

        if response.status_code != 200:
            return ModelResponse(
                name=name,
                content="",
                tokens_in=0,
                tokens_out=0,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return ModelResponse(
            name=name,
            content=content,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )

    except Exception as e:
        return ModelResponse(
            name=name,
            content="",
            tokens_in=0,
            tokens_out=0,
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------


async def ask_council(
    question: str,
    include_context: bool = True,
    models: dict[str, str] | None = None,
) -> CouncilResult:
    """
    Ask the council a question.

    Args:
        question: The raw question.
        include_context: Whether to call gather_context() for enrichment.
        models: Override model dict. Keys are display names, values are
                OpenRouter model IDs.

    Returns:
        CouncilResult with all model responses.
    """
    if models is None:
        models = MODELS

    api_key = _get_api_key()

    if include_context:
        context_snippets, framed_question = gather_context(question)
    else:
        context_snippets = []
        framed_question = question

    messages = [{"role": "user", "content": framed_question}]

    async with httpx.AsyncClient() as client:
        tasks = [
            _call_model(client, name, model_id, messages, api_key)
            for name, model_id in models.items()
        ]
        responses = await asyncio.gather(*tasks)

    # Rough cost estimate (average across frontier models)
    total_cost = sum(
        (r.tokens_in * 10 + r.tokens_out * 40) / 1_000_000 for r in responses
    )

    return CouncilResult(
        question=question,
        framed_question=framed_question,
        context_used=context_snippets,
        responses=list(responses),
        total_cost_usd=total_cost,
    )


def ask_council_sync(
    question: str,
    include_context: bool = True,
    models: dict[str, str] | None = None,
) -> CouncilResult:
    """Synchronous wrapper for ask_council."""
    return asyncio.run(ask_council(question, include_context, models))


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_for_synthesis(result: CouncilResult) -> str:
    """Format council responses for synthesis (by a human or AI)."""
    parts = [f"Question: {result.question}\n"]

    if result.context_used:
        parts.append("Context gathered:")
        for ctx in result.context_used:
            parts.append(f"  - {ctx[:200]}")
        parts.append("")

    parts.append("Model responses:\n")

    for r in result.responses:
        if r.error:
            parts.append(f"**{r.name}**: [Error: {r.error}]\n")
        else:
            parts.append(f"**{r.name}**:\n{r.content}\n")

    parts.append(f"\nEstimated cost: ${result.total_cost_usd:.4f}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python council.py 'your question here'")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"Asking council: {question}\n")

    result = ask_council_sync(question, include_context=False)
    print(format_for_synthesis(result))
