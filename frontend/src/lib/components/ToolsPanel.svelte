<script lang="ts">
	let { toolsList, onClose }: { toolsList: any[]; onClose: () => void } = $props();
</script>

<div class="tools-panel">
	<div class="tools-header">
		<h3>Tools</h3>
		<span class="tools-count">{toolsList.length} available</span>
		<button class="close-btn" onclick={onClose}>✕</button>
	</div>

	{#if toolsList.length === 0}
	<p class="tools-empty">No tools available. Connect an MCP server in Settings or the built-in tools will appear automatically.</p>
	{:else}
	<div class="tools-list">
		{#each toolsList as tool}
		<div class="tool-item">
			<div class="tool-name">{tool.name}</div>
			<div class="tool-desc">{tool.description?.slice(0, 120)}{tool.description?.length > 120 ? '...' : ''}</div>
		</div>
		{/each}
	</div>
	{/if}

	<div class="setting-note" style="margin-top: 12px;">
		The AI automatically uses these tools when relevant. You can also ask it to use a specific tool by name.
	</div>
</div>

<style>
	.tools-panel { width: 300px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.tools-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
	.tools-header h3 { margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; flex: 1; }
	.tools-count { font-size: 10px; color: var(--text-muted); background: var(--bg-tertiary); padding: 2px 6px; border-radius: 8px; }
	.close-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; transition: all var(--transition); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); }
	.close-btn:hover { color: var(--error); background: rgba(255,68,68,0.1); }
	.tools-empty { font-size: 13px; color: var(--text-muted); padding: 20px; text-align: center; }
	.tools-list { display: flex; flex-direction: column; gap: 6px; }
	.tool-item { padding: 8px 10px; background: var(--bg-tertiary); border-radius: var(--radius); border: 1px solid var(--border); transition: all var(--transition); }
	.tool-item:hover { border-color: var(--accent); }
	.tool-name { font-size: 12px; font-weight: 600; color: var(--accent); font-family: monospace; margin-bottom: 3px; }
	.tool-desc { font-size: 11px; color: var(--text-muted); line-height: 1.4; }
	.setting-note { font-size: 12px; color: var(--text-muted); padding: 10px; line-height: 1.5; }
</style>
