"""
LLM connectors — supports Anthropic, OpenAI, and local models.
Multimodal: text + images. Tool calling: built-in + MCP.

Includes an agentic loop: if the LLM requests tool calls,
execute them and feed results back until the LLM responds with text.
"""

import json
import os
from typing import AsyncGenerator

import anthropic
import httpx
import openai

from tools import execute_tool, get_tool_definitions


async def stream_response(
    messages: list[dict],
    provider: str = None,
    system_prompt: str = None,
    use_tools: bool = True,
) -> AsyncGenerator[str, None]:
    """Stream a chat response, handling tool calls in an agentic loop."""
    provider = provider or os.getenv("LLM_PROVIDER", "anthropic")

    if provider == "anthropic":
        async for chunk in _agentic_loop_anthropic(messages, system_prompt, use_tools):
            yield chunk
    elif provider == "openai":
        async for chunk in _agentic_loop_openai(messages, system_prompt, use_tools):
            yield chunk
    elif provider == "gemini":
        async for chunk in _agentic_loop_openai(
            messages, system_prompt, use_tools,
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"),
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        ):
            yield chunk
    elif provider == "grok":
        async for chunk in _agentic_loop_openai(
            messages, system_prompt, use_tools,
            api_key=os.getenv("GROK_API_KEY"),
            base_url=os.getenv("GROK_BASE_URL", "https://api.x.ai/v1"),
            model=os.getenv("GROK_MODEL", "grok-3"),
        ):
            yield chunk
    elif provider == "local":
        async for chunk in _stream_local(messages, system_prompt):
            yield chunk
    else:
        yield f"Unknown provider: {provider}"


# ─── Anthropic with tool calling ────────────────────────────────

async def _agentic_loop_anthropic(
    messages: list[dict],
    system_prompt: str = None,
    use_tools: bool = True,
) -> AsyncGenerator[str, None]:
    """Anthropic agentic loop: stream text, handle tool calls, repeat."""
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    api_messages = [
        {"role": m["role"], "content": _build_anthropic_content(m)}
        for m in messages
    ]

    tools = get_tool_definitions() if use_tools else []
    max_iterations = 10

    for _ in range(max_iterations):
        kwargs = {
            "model": model,
            "max_tokens": 4096,
            "messages": api_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = tools

        response = await client.messages.create(**kwargs)

        # Process content blocks
        has_tool_use = False
        text_parts = []
        tool_results = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                yield block.text
            elif block.type == "tool_use":
                has_tool_use = True
                tool_name = block.name
                tool_input = block.input

                yield f"\n\n🔧 **Tool call: {tool_name}**\n"
                yield f"```json\n{json.dumps(tool_input, indent=2)}\n```\n"

                # Execute the tool
                result = await execute_tool(tool_name, tool_input)

                yield f"\n📋 **Result:**\n```\n{result[:500]}\n```\n\n"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if not has_tool_use:
            # No tool calls — we're done
            break

        # Feed tool results back to the LLM
        api_messages.append({"role": "assistant", "content": response.content})
        api_messages.append({"role": "user", "content": tool_results})


# ─── OpenAI with tool calling ───────────────────────────────────

async def _agentic_loop_openai(
    messages: list[dict],
    system_prompt: str = None,
    use_tools: bool = True,
    api_key: str = None,
    base_url: str = None,
    model: str = None,
) -> AsyncGenerator[str, None]:
    """OpenAI-compatible agentic loop. Works with OpenAI, Gemini, Grok, etc."""
    client = openai.AsyncOpenAI(
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
        base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    model = model or os.getenv("OPENAI_MODEL", "gpt-4")

    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    for m in messages:
        msgs.append({"role": m["role"], "content": _build_openai_content(m)})

    tools_def = get_tool_definitions() if use_tools else []
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools_def
    ] if tools_def else None

    max_iterations = 10

    for _ in range(max_iterations):
        kwargs = {"model": model, "messages": msgs}
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        if choice.message.content:
            yield choice.message.content

        if not choice.message.tool_calls:
            break

        # Handle tool calls
        msgs.append(choice.message)

        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            yield f"\n\n🔧 **Tool call: {tool_name}**\n"
            yield f"```json\n{json.dumps(tool_args, indent=2)}\n```\n"

            result = await execute_tool(tool_name, tool_args)

            yield f"\n📋 **Result:**\n```\n{result[:500]}\n```\n\n"

            msgs.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


# ─── Local (no tool calling, just streaming) ────────────────────

async def _stream_local(
    messages: list[dict],
    system_prompt: str = None,
) -> AsyncGenerator[str, None]:
    """Stream from a local model — no tool calling support."""
    base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("LOCAL_MODEL", "llama3")

    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    for m in messages:
        msgs.append({"role": m["role"], "content": _build_openai_content(m)})

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{base_url}/chat/completions",
            json={"model": model, "messages": msgs, "stream": True},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


# ─── Multimodal content builders ────────────────────────────────

def _build_anthropic_content(msg: dict) -> list | str:
    if "images" not in msg or not msg["images"]:
        return msg["content"]
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
