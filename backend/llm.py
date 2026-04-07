"""
LLM connectors — supports Anthropic, OpenAI, and local models.
Multimodal: text + images supported across all providers.

All connectors return an async generator of text chunks (streaming).
"""

import base64
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


def _build_anthropic_content(msg: dict) -> list | str:
    """Convert a message to Anthropic content format (supports images)."""
    if "images" not in msg or not msg["images"]:
        return msg["content"]

    # Multimodal: text + images
    content = []
    for img in msg["images"]:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img.get("media_type", "image/png"),
                "data": img["data"],
            },
        })
    content.append({"type": "text", "text": msg["content"]})
    return content


def _build_openai_content(msg: dict) -> list | str:
    """Convert a message to OpenAI content format (supports images)."""
    if "images" not in msg or not msg["images"]:
        return msg["content"]

    content = []
    for img in msg["images"]:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{img.get('media_type', 'image/png')};base64,{img['data']}",
            },
        })
    content.append({"type": "text", "text": msg["content"]})
    return content


async def _stream_anthropic(
    messages: list[dict],
    system_prompt: str = None,
) -> AsyncGenerator[str, None]:
    """Stream from Anthropic Claude API."""
    client = anthropic.AsyncAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # Build messages with multimodal support
    api_messages = []
    for msg in messages:
        api_messages.append({
            "role": msg["role"],
            "content": _build_anthropic_content(msg),
        })

    kwargs = {
        "model": model,
        "max_tokens": 4096,
        "messages": api_messages,
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
    for msg in messages:
        msgs.append({
            "role": msg["role"],
            "content": _build_openai_content(msg),
        })

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
    for msg in messages:
        msgs.append({
            "role": msg["role"],
            "content": _build_openai_content(msg),  # Ollama supports OpenAI image format
        })

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
