"""
LLM connectors — supports Anthropic, OpenAI, and local models.
Multimodal: text + images. Tool calling: built-in + MCP.

Includes an agentic loop: if the LLM requests tool calls,
execute them and feed results back until the LLM responds with text.
"""

import asyncio
import json
import os
from typing import AsyncGenerator

import anthropic
import httpx
import openai

from config import config
from tools import execute_tool, get_tool_definitions

# Default timeouts (seconds)
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
LOCAL_LLM_TIMEOUT = float(os.getenv("LOCAL_LLM_TIMEOUT", "120"))


# Local models known to support tool calling (Ollama / OpenAI-compatible)
# Models NOT in this list will be sent without tools to avoid 400 errors.
TOOL_CAPABLE_LOCAL_MODELS = {
    # Llama 3.x families
    "llama3", "llama3.1", "llama3.2", "llama3.3",
    # Mistral with tool support
    "mistral", "mistral-nemo", "mistral-small", "mixtral",
    # Qwen
    "qwen2", "qwen2.5", "qwen3",
    # Command-R
    "command-r", "command-r-plus",
    # Hermes
    "hermes3", "nous-hermes2",
    # Firefunction
    "firefunction-v2",
    # Granite
    "granite3", "granite3.1",
}


def supports_tools(provider: str, model: str) -> bool:
    """Check if a given provider/model combination supports tool calling.

    Cloud providers (Anthropic, OpenAI, Gemini, Grok) all support tools.
    For local models, we check against a known list of tool-capable families.
    """
    if provider in ("anthropic", "openai", "gemini", "grok"):
        return True
    if provider == "local":
        if not model:
            return False
        # Strip tag (e.g., "llama3.2:3b" → "llama3.2")
        base = model.split(":")[0].lower()
        # Strip provider prefix (e.g., "registry.ollama.ai/library/llama3" → "llama3")
        if "/" in base:
            base = base.rsplit("/", 1)[1]
        # Match against known families
        for family in TOOL_CAPABLE_LOCAL_MODELS:
            if base == family or base.startswith(family + "."):
                return True
        return False
    return False


async def stream_response(
    messages: list[dict],
    provider: str = None,
    system_prompt: str = None,
    use_tools: bool = True,
) -> AsyncGenerator[str, None]:
    """Stream a chat response, handling tool calls in an agentic loop."""
    provider = provider or config.default_provider

    if provider == "anthropic":
        async for chunk in _agentic_loop_anthropic(messages, system_prompt, use_tools):
            yield chunk
    elif provider in ("openai", "gemini", "grok"):
        async for chunk in _agentic_loop_openai(
            messages, system_prompt, use_tools,
            api_key=config.get_api_key(provider),
            base_url=config.get_base_url(provider),
            model=config.get_model(provider),
        ):
            yield chunk
    elif provider == "local":
        local_model = config.get_model("local") or "llama3"
        # Only use tools if the model is known to support them
        model_supports_tools = use_tools and supports_tools("local", local_model)
        if model_supports_tools:
            async for chunk in _agentic_loop_openai(
                messages, system_prompt, True,
                api_key="ollama",
                base_url=config.get_base_url("local") or "http://localhost:11434/v1",
                model=local_model,
            ):
                yield chunk
        else:
            # Model doesn't support tools (or tools disabled) — simple streaming
            if use_tools:
                # User wanted tools but model doesn't support them — let them know
                yield f"ℹ️ *Model `{local_model}` doesn't support tool calling. Responding without tools.*\n\n"
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
    client = anthropic.AsyncAnthropic(
        api_key=config.get_api_key("anthropic"),
        timeout=LLM_TIMEOUT,
    )
    model = config.get_model("anthropic")

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

        try:
            response = await client.messages.create(**kwargs)
        except (anthropic.APITimeoutError, asyncio.TimeoutError):
            yield f"\n\n⏱ **Request timed out** after {LLM_TIMEOUT}s. The LLM may be slow or unresponsive.\n"
            return
        except Exception as e:
            yield f"\n\n❌ **Error**: {type(e).__name__}: {e}\n"
            return

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
    # Local models get a longer timeout (slow inference on small hardware)
    is_local = (base_url and "localhost" in base_url) or (base_url and "127.0.0.1" in base_url) or "11434" in (base_url or "")
    timeout = LOCAL_LLM_TIMEOUT if is_local else LLM_TIMEOUT

    client = openai.AsyncOpenAI(
        api_key=api_key or config.get_api_key("openai"),
        base_url=base_url or config.get_base_url("openai") or "https://api.openai.com/v1",
        timeout=timeout,
    )
    model = model or config.get_model("openai") or "gpt-4"

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

        try:
            response = await client.chat.completions.create(**kwargs)
        except (openai.APITimeoutError, asyncio.TimeoutError):
            yield f"\n\n⏱ **Request timed out** after {timeout}s. The model may be slow or unresponsive.\n"
            return
        except openai.BadRequestError as e:
            err_msg = str(e).lower()
            # Some models report tool incompatibility only at request time.
            # Retry once without tools as a defense-in-depth fallback.
            if "tool" in err_msg and openai_tools:
                yield f"\nℹ️ *Model `{model}` doesn't support tool calling. Retrying without tools...*\n\n"
                kwargs.pop("tools", None)
                openai_tools = None  # disable for remaining iterations
                try:
                    response = await client.chat.completions.create(**kwargs)
                except Exception as e2:
                    yield f"\n\n❌ **Error after retry**: {type(e2).__name__}: {e2}\n"
                    return
            else:
                yield f"\n\n❌ **Bad request**: {e}\n"
                return
        except Exception as e:
            yield f"\n\n❌ **Error**: {type(e).__name__}: {e}\n"
            return
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
    base_url = config.get_base_url("local") or "http://localhost:11434/v1"
    model = config.get_model("local") or "llama3"

    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    for m in messages:
        msgs.append({"role": m["role"], "content": _build_openai_content(m)})

    try:
        async with httpx.AsyncClient(timeout=LOCAL_LLM_TIMEOUT) as client:
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
    except (httpx.TimeoutException, asyncio.TimeoutError):
        yield f"\n\n⏱ **Request timed out** after {LOCAL_LLM_TIMEOUT}s. The local model may be overloaded or unresponsive.\n"
    except Exception as e:
        yield f"\n\n❌ **Error**: {type(e).__name__}: {e}\n"


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
