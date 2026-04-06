"""
LLM connectors — supports Anthropic, OpenAI, and local models.

All connectors return an async generator of text chunks (streaming).
"""

import os
from typing import AsyncGenerator

import anthropic
import httpx
import openai


async def stream_response(
    messages: list[dict],
    provider: str = None,
    system_prompt: str = None,
) -> AsyncGenerator[str, None]:
    """Stream a chat response from the configured LLM provider."""
    provider = provider or os.getenv("LLM_PROVIDER", "anthropic")

    if provider == "anthropic":
        async for chunk in _stream_anthropic(messages, system_prompt):
            yield chunk
    elif provider == "openai":
        async for chunk in _stream_openai(messages, system_prompt):
            yield chunk
    elif provider == "local":
        async for chunk in _stream_local(messages, system_prompt):
            yield chunk
    else:
        yield f"Unknown provider: {provider}"


async def _stream_anthropic(
    messages: list[dict],
    system_prompt: str = None,
) -> AsyncGenerator[str, None]:
    """Stream from Anthropic Claude API."""
    client = anthropic.AsyncAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    kwargs = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    async with client.messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            yield text


async def _stream_openai(
    messages: list[dict],
    system_prompt: str = None,
) -> AsyncGenerator[str, None]:
    """Stream from OpenAI or any OpenAI-compatible endpoint."""
    client = openai.AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4")

    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.extend(messages)

    stream = await client.chat.completions.create(
        model=model,
        messages=msgs,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_local(
    messages: list[dict],
    system_prompt: str = None,
) -> AsyncGenerator[str, None]:
    """Stream from a local model via OpenAI-compatible API (Ollama, LM Studio)."""
    base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("LOCAL_MODEL", "llama3")

    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.extend(messages)

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": msgs,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
