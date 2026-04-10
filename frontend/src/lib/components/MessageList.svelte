<script lang="ts">
	import type { Message as MessageType } from '$lib/api';
	import { renderMarkdown } from '$lib/markdown';
	import Message from './Message.svelte';

	let {
		messages, isStreaming, streamingText, onHighlight, onBranch,
	}: {
		messages: MessageType[];
		isStreaming: boolean;
		streamingText: string;
		onHighlight: (i: number) => void;
		onBranch: (i: number) => void;
	} = $props();

	const streamingHtml = $derived(renderMarkdown(streamingText));
</script>

<div class="messages">
	{#if messages.length === 0}
	<div class="welcome">
		<h1>ThreadWeaver</h1>
		<p class="welcome-tagline">AI chat where every conversation is versioned, branchable, and searchable.</p>

		<div class="welcome-features">
			<div class="welcome-feature">
				<div class="wf-icon">⑂</div>
				<div class="wf-text">
					<strong>Branch from any message</strong>
					<span>Explore "what if I'd asked differently?" without losing your original thread.</span>
				</div>
			</div>
			<div class="welcome-feature">
				<div class="wf-icon">🖼</div>
				<div class="wf-text">
					<strong>Multimodal</strong>
					<span>Paste images, drop files. Works with Claude, GPT, Gemini, Grok, and local models.</span>
				</div>
			</div>
			<div class="welcome-feature">
				<div class="wf-icon">🔧</div>
				<div class="wf-text">
					<strong>Tool calling + MCP</strong>
					<span>Read files, run commands, connect MCP servers. The AI acts, not just talks.</span>
				</div>
			</div>
			<div class="welcome-feature">
				<div class="wf-icon">📓</div>
				<div class="wf-text">
					<strong>Notebook</strong>
					<span>Save any message with a tag. Comment, copy, or start a new chat from highlights.</span>
				</div>
			</div>
			<div class="welcome-feature">
				<div class="wf-icon">📁</div>
				<div class="wf-text">
					<strong>Projects</strong>
					<span>Group related conversations. Shared context across chats in a project.</span>
				</div>
			</div>
			<div class="welcome-feature">
				<div class="wf-icon">🔍</div>
				<div class="wf-text">
					<strong>Full provenance</strong>
					<span>Powered by <a href="https://agentstategraph.dev" target="_blank">AgentStateGraph</a> — every message exchange is a versioned commit with intent, reasoning, and audit trail.</span>
				</div>
			</div>
		</div>

		<p class="welcome-hint">Select or create a chat to get started. Type a message or paste an image.</p>
	</div>
	{/if}

	{#each messages as msg, i}
		<Message {msg} index={i} {onHighlight} {onBranch} />
	{/each}

	{#if isStreaming && streamingText}
	<div class="msg assistant streaming">
		<div class="msg-header">
			<span class="role">Assistant</span>
			<span class="dot">●</span>
		</div>
		<div class="msg-content markdown">{@html streamingHtml}</div>
	</div>
	{/if}
</div>

<style>
	.messages { flex: 1; overflow-y: auto; padding: 16px; scroll-behavior: smooth; }

	.welcome { padding: 40px 20px; max-width: 640px; margin: 0 auto; animation: fadeIn 0.5s ease; }
	.welcome h1 { text-align: center; color: var(--accent); font-size: 32px; font-weight: 700; letter-spacing: -0.5px; background: linear-gradient(135deg, var(--accent), #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 4px; }
	.welcome-tagline { text-align: center; color: var(--text-muted); font-size: 15px; margin-bottom: 28px; }
	.welcome-features { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
	.welcome-feature { display: flex; gap: 12px; align-items: flex-start; padding: 12px 14px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: var(--radius); transition: all var(--transition); animation: fadeIn 0.4s ease backwards; }
	.welcome-feature:nth-child(1) { animation-delay: 0.05s; }
	.welcome-feature:nth-child(2) { animation-delay: 0.1s; }
	.welcome-feature:nth-child(3) { animation-delay: 0.15s; }
	.welcome-feature:nth-child(4) { animation-delay: 0.2s; }
	.welcome-feature:nth-child(5) { animation-delay: 0.25s; }
	.welcome-feature:nth-child(6) { animation-delay: 0.3s; }
	.welcome-feature:hover { border-color: var(--accent); background: var(--accent-subtle); }
	.wf-icon { font-size: 20px; flex-shrink: 0; width: 32px; text-align: center; }
	.wf-text { display: flex; flex-direction: column; gap: 2px; }
	.wf-text strong { font-size: 13px; color: var(--text-primary); }
	.wf-text span { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
	.wf-text a { color: var(--accent); }
	.welcome-hint { text-align: center; color: var(--text-muted); font-size: 13px; font-style: italic; }

	/* Streaming preview message */
	.msg { margin-bottom: 16px; padding: 14px 16px; border-radius: var(--radius-lg); max-width: 800px; animation: fadeIn 0.3s ease; }
	.msg.assistant { background: var(--bg-secondary); border: 1px solid var(--border); }
	.msg.streaming { border-color: var(--accent-glow); box-shadow: 0 0 16px var(--accent-glow); }
	.msg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
	.role { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
	.dot { color: var(--accent); animation: pulse 1s infinite; }
	.msg-content { font-size: 14px; line-height: 1.7; word-wrap: break-word; }

	.markdown :global(p) { margin: 0 0 10px; }
	.markdown :global(p:last-child) { margin-bottom: 0; }
	.markdown :global(code) { background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.88em; color: var(--accent); }
	.markdown :global(pre) { background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; overflow-x: auto; margin: 8px 0; }
	.markdown :global(pre code) { background: transparent; padding: 0; color: var(--text-primary); font-size: 12.5px; line-height: 1.55; }
</style>
