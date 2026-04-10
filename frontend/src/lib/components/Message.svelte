<script lang="ts">
	import type { Message } from '$lib/api';
	import { renderMarkdown } from '$lib/markdown';

	let { msg, index, onHighlight, onBranch }: {
		msg: Message;
		index: number;
		onHighlight: (i: number) => void;
		onBranch: (i: number) => void;
	} = $props();

	const html = $derived(renderMarkdown(msg.content));
</script>

<div class="msg {msg.role}">
	<div class="msg-avatar">
		{#if msg.role === 'user'}
		<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
		{:else}
		<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/><path d="M6 12h12l2 10H4l2-10z"/></svg>
		{/if}
	</div>
	<div class="msg-body">
		<div class="msg-header">
			<div class="msg-meta">
				<span class="role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
				<span class="msg-time">{new Date(msg.timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>
			</div>
			<div class="msg-actions">
				<button class="action-btn" title="Save to notebook" onclick={() => onHighlight(index)}>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
				</button>
				<button class="action-btn" title="Branch from here" onclick={() => onBranch(index)}>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M6 9v3a6 6 0 0 0 6 6h3"/><line x1="18" y1="9" x2="18" y2="15"/></svg>
				</button>
			</div>
		</div>
		{#if msg.images && msg.images.length > 0}
		<div class="msg-images">
			{#each msg.images as img}
			<img src="data:{img.media_type};base64,{img.data}" alt="attached" class="attached-image" />
			{/each}
		</div>
		{/if}
		<div class="msg-content markdown">{@html html}</div>
	</div>
</div>

<style>
	.msg { margin-bottom: 16px; padding: 14px 16px; border-radius: var(--radius-lg); max-width: 800px; animation: fadeIn 0.3s ease; transition: box-shadow var(--transition); display: flex; gap: 12px; }
	.msg:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.2); }
	.msg-avatar { flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-top: 2px; }
	.msg.user .msg-avatar { background: var(--accent); color: #fff; }
	.msg.assistant .msg-avatar { background: var(--bg-primary); color: var(--accent); border: 1px solid var(--border); }
	.msg-body { flex: 1; min-width: 0; }
	.msg.user { background: var(--accent-subtle); margin-left: auto; animation: slideInRight 0.3s ease; border: 1px solid var(--accent-glow); border-left: 3px solid var(--accent); }
	.msg.user:hover { border-color: var(--accent); }
	.msg.user .role { color: var(--accent); }
	.msg.assistant { background: var(--bg-secondary); border: 1px solid var(--border); animation: slideInLeft 0.3s ease; }
	.msg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
	.msg-meta { display: flex; align-items: center; gap: 8px; }
	.role { font-size: 10px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
	.msg.assistant .role { color: var(--text-muted); }
	.msg-time { font-size: 10px; color: var(--text-muted); font-weight: 400; }
	.msg-actions { display: flex; gap: 4px; opacity: 0; transition: opacity var(--transition); }
	.msg:hover .msg-actions { opacity: 1; }
	.action-btn { background: none; border: 1px solid var(--border); color: var(--text-muted); font-size: 11px; padding: 3px 8px; border-radius: var(--radius-sm); cursor: pointer; transition: all var(--transition); }
	.action-btn:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-subtle); transform: scale(1.05); }
	.msg-content { font-size: 14px; line-height: 1.7; word-wrap: break-word; }
	.msg-images { margin-bottom: 8px; }
	.attached-image { max-width: 300px; max-height: 200px; border-radius: var(--radius); border: 1px solid var(--border); transition: transform var(--transition); }
	.attached-image:hover { transform: scale(1.02); }

	/* Markdown styles (using :global because content is rendered via @html) */
	.markdown :global(p) { margin: 0 0 10px; }
	.markdown :global(p:last-child) { margin-bottom: 0; }
	.markdown :global(h1), .markdown :global(h2), .markdown :global(h3), .markdown :global(h4) { margin: 14px 0 6px; font-weight: 700; line-height: 1.3; }
	.markdown :global(h1) { font-size: 20px; }
	.markdown :global(h2) { font-size: 17px; }
	.markdown :global(h3) { font-size: 15px; }
	.markdown :global(h4) { font-size: 14px; }
	.markdown :global(ul), .markdown :global(ol) { margin: 6px 0 10px; padding-left: 22px; }
	.markdown :global(li) { margin: 3px 0; }
	.markdown :global(li > p) { margin: 0; }
	.markdown :global(a) { color: var(--accent); text-decoration: underline; }
	.markdown :global(a:hover) { filter: brightness(1.2); }
	.markdown :global(blockquote) { margin: 8px 0; padding: 6px 12px; border-left: 3px solid var(--accent); background: var(--bg-tertiary); border-radius: 0 var(--radius-sm) var(--radius-sm) 0; color: var(--text-secondary); }
	.markdown :global(code) { background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.88em; color: var(--accent); }
	.markdown :global(pre) { background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; overflow-x: auto; margin: 8px 0; }
	.markdown :global(pre code) { background: transparent; padding: 0; color: var(--text-primary); font-size: 12.5px; line-height: 1.55; }
	.markdown :global(table) { border-collapse: collapse; margin: 8px 0; font-size: 13px; }
	.markdown :global(th), .markdown :global(td) { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
	.markdown :global(th) { background: var(--bg-tertiary); font-weight: 600; }
	.markdown :global(hr) { border: none; border-top: 1px solid var(--border); margin: 12px 0; }
	.markdown :global(img) { max-width: 100%; border-radius: var(--radius-sm); }
	.markdown :global(strong) { font-weight: 700; }
	.markdown :global(em) { font-style: italic; }
</style>
