<script lang="ts">
	let {
		notebooks, noteComments, onClose, onAddComment, onBranchFromNote,
	}: {
		notebooks: any[];
		noteComments: Record<number, string[]>;
		onClose: () => void;
		onAddComment: (i: number) => void;
		onBranchFromNote: (i: number) => void | Promise<void>;
	} = $props();

	let expandedNote = $state<number | null>(null);

	function copyNote(note: any) {
		navigator.clipboard.writeText(
			note.messages.map((m: any) => `${m.role}: ${m.content}`).join('\n\n')
		);
	}
</script>

<div class="notebook">
	<div class="notebook-header">
		<h3>Notebook</h3>
		<button class="close-btn" onclick={() => { expandedNote = null; onClose(); }}>✕</button>
	</div>
	{#if notebooks.length === 0}
	<p class="notebook-empty">No highlights yet. Click the bookmark icon on any message to save it.</p>
	{:else}
	{#each notebooks as note, i}
	<div class="note" class:expanded={expandedNote === i}>
		<button class="note-header" onclick={() => expandedNote = expandedNote === i ? null : i}>
			<span class="note-tag">{note.tag}</span>
			<span class="note-preview">
				{#if expandedNote !== i}
					{note.messages[0]?.content.slice(0, 60)}{note.messages[0]?.content.length > 60 ? '...' : ''}
				{/if}
			</span>
			<span class="note-expand">{expandedNote === i ? '▾' : '▸'}</span>
		</button>

		{#if expandedNote === i}
		<div class="note-body">
			{#each note.messages as m}
			<div class="note-full-msg">
				<span class="note-role">{m.role}</span>
				<div class="note-content">{m.content}</div>
			</div>
			{/each}

			{#if noteComments[i]?.length}
			<div class="note-comments">
				<div class="note-comments-title">Comments</div>
				{#each noteComments[i] as comment}
				<div class="note-comment">{comment}</div>
				{/each}
			</div>
			{/if}

			<div class="note-actions">
				<button class="note-action-btn" onclick={() => onAddComment(i)}>💬 Comment</button>
				<button class="note-action-btn" onclick={() => onBranchFromNote(i)}>⑂ New Chat</button>
				<button class="note-action-btn" onclick={() => copyNote(note)}>📋 Copy</button>
			</div>
		</div>
		{/if}
	</div>
	{/each}
	{/if}
</div>

<style>
	.notebook { width: 300px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.notebook-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; gap: 8px; }
	.notebook-header h3 { margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; }
	.close-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; transition: all var(--transition); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); }
	.close-btn:hover { color: var(--error); background: rgba(255,68,68,0.1); }
	.notebook-empty { color: var(--text-muted); font-size: 13px; text-align: center; padding: 30px 20px; }
	.note { background: var(--bg-tertiary); border-radius: var(--radius); margin-bottom: 8px; border-left: 3px solid var(--accent); animation: scaleIn 0.2s ease; transition: all var(--transition); overflow: hidden; }
	.note:hover { border-left-width: 4px; }
	.note.expanded { border-left-color: var(--accent); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
	.note-header { padding: 10px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; width: 100%; background: none; border: none; text-align: left; color: inherit; }
	.note-header:hover { background: var(--bg-hover); }
	.note-tag { font-size: 10px; color: var(--accent); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; flex-shrink: 0; }
	.note-preview { font-size: 12px; color: var(--text-muted); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.note-expand { color: var(--text-muted); font-size: 10px; flex-shrink: 0; }
	.note-body { padding: 0 12px 12px; border-top: 1px solid var(--border); animation: fadeIn 0.2s ease; }
	.note-full-msg { padding: 8px 0; border-bottom: 1px solid var(--border); }
	.note-full-msg:last-of-type { border-bottom: none; }
	.note-role { font-size: 10px; font-weight: 700; color: var(--accent); text-transform: uppercase; display: block; margin-bottom: 4px; }
	.note-content { font-size: 13px; color: var(--text-primary); line-height: 1.6; white-space: pre-wrap; }
	.note-comments { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }
	.note-comments-title { font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }
	.note-comment { font-size: 12px; color: var(--text-secondary); padding: 4px 8px; background: var(--bg-primary); border-radius: var(--radius-sm); margin-bottom: 4px; }
	.note-actions { display: flex; gap: 6px; margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border); }
	.note-action-btn { background: none; border: 1px solid var(--border); color: var(--text-muted); padding: 4px 10px; border-radius: var(--radius-sm); cursor: pointer; font-size: 11px; transition: all var(--transition); }
	.note-action-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }
</style>
