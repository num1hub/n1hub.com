"""LLM client wrapper for grounded answer generation."""

from __future__ import annotations

from typing import List

from .config import settings
from .models import CapsuleModel


async def generate_grounded_answer(query: str, context_capsules: List[CapsuleModel]) -> str:
    """
    Generate a grounded answer using LLM with context capsules.
    
    Uses the RAG-QUERY prompt pattern from CapsuleOS Prompt Library:
    - Use ONLY provided CONTEXT_CAPSULES
    - NO external facts from training data
    - Every factual claim must cite ≥1 capsule_id
    - Use inline citation format: 【<capsule_id>】
    - If insufficient evidence: Return fallback message
    """
    if not context_capsules or len(context_capsules) < 2:
        return settings.citation_fallback
    
    # Build context from capsules
    context_parts = []
    for capsule in context_capsules:
        context_parts.append(
            f"【{capsule.metadata.capsule_id}】\n"
            f"Summary: {capsule.neuro_concentrate.summary}\n"
            f"Keywords: {', '.join(capsule.neuro_concentrate.keywords)}\n"
            f"Content: {capsule.core_payload.content[:500]}..."  # Truncate for token limits
        )
    
    context_text = "\n\n".join(context_parts)
    
    # RAG-QUERY prompt pattern (from Prompt Library, capsule 18)
    system_prompt = """You are a grounded answerer. Use ONLY the provided CONTEXT_CAPSULES.
- NO external facts from training data
- Every factual claim must cite ≥1 capsule_id using inline format: 【<capsule_id>】
- If insufficient evidence: Return "Insufficient capsule evidence to answer."
- Be concise and precise
- Use bullet points for lists
- Mark interpretations clearly"""
    
    user_prompt = f"""QUERY: {query}

CONTEXT_CAPSULES:
{context_text}

Generate a grounded answer using ONLY the context above. Cite capsule_ids inline using 【<capsule_id>】 format."""
    
    # Call LLM provider
    try:
        if settings.llm_provider == "anthropic":
            return await _call_anthropic(system_prompt, user_prompt)
        elif settings.llm_provider == "openai":
            return await _call_openai(system_prompt, user_prompt)
        else:
            # Fallback to simple composition if LLM not configured
            return _simple_compose_answer(context_capsules, query)
    except Exception as e:
        # Fallback on error
        return _simple_compose_answer(context_capsules, query)


async def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    """Call Anthropic Claude API."""
    try:
        import anthropic
        
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY not set")
        
        client = anthropic.Anthropic(api_key=settings.llm_api_key)
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.answer_max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        
        # Extract text from response
        if response.content and len(response.content) > 0:
            if hasattr(response.content[0], 'text'):
                return response.content[0].text
            elif isinstance(response.content[0], str):
                return response.content[0]
        
        return settings.citation_fallback
    except ImportError:
        # anthropic package not installed, fallback
        return _simple_compose_answer_from_prompt(system_prompt, user_prompt)
    except Exception:
        # API error, fallback
        return _simple_compose_answer_from_prompt(system_prompt, user_prompt)


async def _call_openai(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI API."""
    try:
        from openai import AsyncOpenAI
        
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY not set")
        
        client = AsyncOpenAI(api_key=settings.llm_api_key)
        response = await client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=settings.answer_max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content or settings.citation_fallback
        
        return settings.citation_fallback
    except ImportError:
        # openai package not installed, fallback
        return _simple_compose_answer_from_prompt(system_prompt, user_prompt)
    except Exception:
        # API error, fallback
        return _simple_compose_answer_from_prompt(system_prompt, user_prompt)


def _simple_compose_answer(capsules: List[CapsuleModel], query: str) -> str:
    """Fallback simple answer composition (original implementation)."""
    sentences = [
        "N1Hub evaluated the active scope and assembled the following grounded perspective.",
    ]
    for capsule in capsules:
        sentences.append(
            f"【{capsule.metadata.capsule_id}】 {capsule.neuro_concentrate.summary.split('.', 1)[0].strip()}"
        )
    sentences.append("Responses stay within cited capsules; request a richer scope to go deeper.")
    return " ".join(sentences)


def _simple_compose_answer_from_prompt(system_prompt: str, user_prompt: str) -> str:
    """Fallback when LLM is not available - extract query and use simple composition."""
    # Extract query from user_prompt
    query = user_prompt.split("QUERY:")[1].split("\n")[0].strip() if "QUERY:" in user_prompt else ""
    # This is a minimal fallback - in practice, we'd parse capsules from context
    return settings.citation_fallback
