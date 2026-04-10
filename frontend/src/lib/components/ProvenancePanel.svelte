<script lang="ts">
	let { provenanceData, onClose }: { provenanceData: any[]; onClose: () => void } = $props();
</script>

<div class="provenance-panel">
	<div class="provenance-header">
		<h3>Provenance</h3>
		<div class="provenance-badge">AgentStateGraph</div>
		<button class="close-btn" onclick={onClose}>✕</button>
	</div>

	{#if provenanceData.length === 0}
	<div class="provenance-empty">
		<div class="prov-icon">📊</div>
		<p>No provenance data yet.</p>
		<p class="prov-hint">Start a conversation to see the provenance trail. Every message is tracked with intent, agent, and timestamps.</p>
		<a href="https://agentstategraph.dev" target="_blank" class="prov-link">Learn about AgentStateGraph</a>
	</div>
	{:else}
	<div class="provenance-timeline">
		{#each provenanceData as entry, i}
		<div class="prov-entry" style="animation-delay: {i * 0.05}s">
			<div class="prov-dot"></div>
			<div class="prov-content">
				<div class="prov-entry-header">
					<span class="prov-category">{entry.intent?.category || 'Unknown'}</span>
					<span class="prov-time">{entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : ''}</span>
				</div>
				<div class="prov-description">{entry.intent?.description || ''}</div>
				{#if entry.reasoning}
				<div class="prov-reasoning">{entry.reasoning}</div>
				{/if}
				<div class="prov-meta">
					<span class="prov-agent">{entry.agent || 'unknown'}</span>
					{#if entry.confidence != null}
					<span class="prov-confidence">{Math.round(entry.confidence * 100)}%</span>
					{/if}
					{#if entry.intent?.tags?.length}
					<span class="prov-tags">{entry.intent.tags.join(', ')}</span>
					{/if}
				</div>
				<div class="prov-id">{entry.id || ''}</div>
			</div>
		</div>
		{/each}
	</div>
	{/if}
</div>

<style>
	.provenance-panel { width: 320px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.provenance-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
	.provenance-header h3 { margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; flex: 1; }
	.provenance-badge { font-size: 9px; color: var(--accent); background: var(--accent-subtle); border: 1px solid var(--accent); padding: 2px 6px; border-radius: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
	.close-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; transition: all var(--transition); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); }
	.close-btn:hover { color: var(--error); background: rgba(255,68,68,0.1); }
	.provenance-empty { text-align: center; padding: 24px 12px; }
	.prov-icon { font-size: 32px; margin-bottom: 8px; }
	.provenance-empty p { font-size: 13px; color: var(--text-muted); line-height: 1.5; margin: 4px 0; }
	.prov-hint { font-size: 12px !important; }
	.prov-link { display: inline-block; margin-top: 12px; font-size: 12px; color: var(--accent); }

	.provenance-timeline { position: relative; padding-left: 16px; }
	.provenance-timeline::before { content: ''; position: absolute; left: 5px; top: 8px; bottom: 8px; width: 2px; background: var(--border); border-radius: 1px; }

	.prov-entry { position: relative; margin-bottom: 12px; animation: fadeIn 0.3s ease backwards; }
	.prov-dot { position: absolute; left: -14px; top: 6px; width: 10px; height: 10px; background: var(--accent); border-radius: 50%; border: 2px solid var(--bg-secondary); z-index: 1; }
	.prov-content { background: var(--bg-tertiary); border-radius: var(--radius); padding: 10px 12px; border: 1px solid var(--border); transition: all var(--transition); }
	.prov-content:hover { border-color: var(--accent); }

	.prov-entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
	.prov-category { font-size: 10px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; background: var(--accent-subtle); padding: 1px 6px; border-radius: 3px; }
	.prov-time { font-size: 10px; color: var(--text-muted); }

	.prov-description { font-size: 12px; color: var(--text-primary); margin-bottom: 4px; line-height: 1.4; }
	.prov-reasoning { font-size: 11px; color: var(--text-muted); font-style: italic; margin-bottom: 6px; line-height: 1.4; padding: 4px 8px; background: var(--bg-primary); border-radius: var(--radius-sm); border-left: 2px solid var(--accent); }

	.prov-meta { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
	.prov-agent { font-size: 10px; color: var(--text-muted); background: var(--bg-primary); padding: 1px 5px; border-radius: 3px; }
	.prov-confidence { font-size: 10px; color: var(--success); font-weight: 600; }
	.prov-tags { font-size: 10px; color: var(--text-muted); }
	.prov-id { font-size: 9px; color: var(--text-muted); opacity: 0.5; margin-top: 4px; font-family: monospace; }
</style>
