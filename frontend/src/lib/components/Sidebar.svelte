<script lang="ts">
	import type { ConversationSummary } from '$lib/api';

	let {
		conversations, currentConvId, convTree, projects, selectedProjectId,
		searchQuery = $bindable(), searchResults,
		onNewChat, onSelectConversation, onSearch, onDeleteChat, onArchiveChat,
		onMoveToProject, onNewProject, onSelectProject,
	}: {
		conversations: ConversationSummary[];
		currentConvId: string | null;
		convTree: any;
		projects: any[];
		selectedProjectId: string | null;
		searchQuery: string;
		searchResults: any[];
		onNewChat: () => void | Promise<void>;
		onSelectConversation: (id: string) => void | Promise<void>;
		onSearch: () => void | Promise<void>;
		onDeleteChat: (id: string) => void | Promise<void>;
		onArchiveChat: (id: string) => void | Promise<void>;
		onMoveToProject: (id: string) => void | Promise<void>;
		onNewProject: () => void | Promise<void>;
		onSelectProject: (id: string | null) => void;
	} = $props();

	function formatTime(ts: number): string {
		const d = new Date(ts * 1000);
		const now = new Date();
		const diff = now.getTime() - d.getTime();
		const mins = Math.floor(diff / 60000);
		const hours = Math.floor(diff / 3600000);
		const days = Math.floor(diff / 86400000);
		if (mins < 1) return 'just now';
		if (mins < 60) return `${mins}m ago`;
		if (hours < 24) return `${hours}h ago`;
		if (days < 7) return `${days}d ago`;
		return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
	}
</script>

<aside class="sidebar">
	<div class="sidebar-header">
		<h2>ThreadWeaver</h2>
		<button class="new-chat" onclick={onNewChat}>+ New Chat</button>
	</div>
	<div class="search-box">
		<input type="text" placeholder="Search..." bind:value={searchQuery}
			onkeydown={(e) => e.key === 'Enter' && onSearch()} />
	</div>
	{#if searchResults.length > 0}
	<div class="search-results">
		{#each searchResults as r}
		<button class="search-result" onclick={() => onSelectConversation(r.conversation_id)}>
			<span class="result-title">{r.conversation_title}</span>
			<span class="result-preview">{r.content_preview}</span>
		</button>
		{/each}
	</div>
	{/if}

	{#if convTree && convTree.children && convTree.children.length > 0}
	<div class="tree-section">
		<h3>Branches</h3>
		<div class="tree">
			{#snippet treeNode(node: any, depth: number)}
				<button class="tree-item" style="padding-left: {8 + depth * 16}px"
					class:active={node.id === currentConvId}
					onclick={() => onSelectConversation(node.id)}>
					<span class="tree-icon">{depth === 0 ? '●' : '⑂'}</span>
					<span class="tree-label">{node.title}</span>
					<span class="tree-count">{node.message_count} msgs</span>
				</button>
				{#if node.children}
					{#each node.children as child}
						{@render treeNode(child, depth + 1)}
					{/each}
				{/if}
			{/snippet}
			{@render treeNode(convTree, 0)}
		</div>
	</div>
	{/if}

	{#if projects.length > 0}
	<div class="projects-section">
		<div class="section-header">
			<span>Projects</span>
			<button class="section-add" onclick={onNewProject}>+</button>
		</div>
		{#each projects as proj}
		<button class="project-item" class:active={selectedProjectId === proj.id}
			onclick={() => onSelectProject(selectedProjectId === proj.id ? null : proj.id)}>
			<span class="project-name">📁 {proj.name}</span>
			<span class="project-count">{proj.chat_count}</span>
		</button>
		{/each}
	</div>
	{:else}
	<div class="section-header" style="padding: 4px 14px;">
		<span></span>
		<button class="section-add" title="New Project" onclick={onNewProject}>📁+</button>
	</div>
	{/if}

	<div class="conv-list">
		{#each conversations.filter(c => !selectedProjectId || (c as any).project_id === selectedProjectId) as conv}
		<div class="conv-item-wrapper">
			<button class="conv-item" class:active={conv.id === currentConvId}
				onclick={() => onSelectConversation(conv.id)}>
				<span class="conv-title">{conv.title}</span>
				<span class="conv-meta">
					<span>{conv.message_count} msgs</span>
					<span class="conv-time">{formatTime(conv.created_at)}</span>
					{#if (conv as any).parent_id}<span class="badge">branch</span>{/if}
					{#if (conv as any).project_id}<span class="badge project-badge">📁</span>{/if}
				</span>
			</button>
			<div class="conv-actions">
				<button class="conv-action" title="Move to project" onclick={() => onMoveToProject(conv.id)}>📁</button>
				<button class="conv-action" title="Archive" onclick={() => onArchiveChat(conv.id)}>📥</button>
				<button class="conv-action delete" title="Delete" onclick={() => onDeleteChat(conv.id)}>✕</button>
			</div>
		</div>
		{/each}

		{#if conversations.length === 0}
		<p style="text-align: center; color: var(--text-muted); font-size: 13px; padding: 20px;">No conversations yet</p>
		{/if}
	</div>
</aside>

<style>
	.sidebar { width: 260px; background: var(--bg-secondary); border-right: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; animation: slideInLeft 0.3s ease; }
	.sidebar-header { padding: 14px; border-bottom: 1px solid var(--border); }
	.sidebar-header h2 { margin: 0 0 10px; font-size: 15px; color: var(--accent); font-weight: 700; letter-spacing: -0.3px; }
	.new-chat { width: 100%; padding: 9px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius); cursor: pointer; font-size: 13px; font-weight: 500; transition: all var(--transition); }
	.new-chat:hover { filter: brightness(1.15); transform: translateY(-1px); box-shadow: 0 4px 12px var(--accent-glow); }
	.new-chat:active { transform: translateY(0); }
	.search-box { padding: 6px 14px; }
	.search-box input { width: 100%; padding: 8px 10px; background: var(--bg-tertiary); border: 1px solid transparent; border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px; transition: all var(--transition); }
	.search-box input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); outline: none; }
	.search-results { padding: 0 6px; max-height: 150px; overflow-y: auto; }
	.search-result { display: block; width: 100%; text-align: left; padding: 6px 8px; background: none; border: none; color: var(--text-primary); cursor: pointer; border-radius: var(--radius-sm); transition: background var(--transition); }
	.search-result:hover { background: var(--bg-hover); }
	.result-title { display: block; font-size: 12px; font-weight: 600; }
	.result-preview { display: block; font-size: 11px; color: var(--text-muted); }

	.tree-section { padding: 8px 6px; border-bottom: 1px solid var(--border); }
	.tree-section h3 { margin: 0 0 6px 8px; font-size: 10px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; font-weight: 600; }
	.tree-item { display: flex; align-items: center; gap: 6px; width: 100%; text-align: left; padding: 5px 8px; background: none; border: none; color: var(--text-secondary); cursor: pointer; border-radius: var(--radius-sm); font-size: 12px; transition: all var(--transition); }
	.tree-item:hover { background: var(--bg-hover); color: var(--text-primary); }
	.tree-item.active { background: var(--accent-subtle); color: var(--accent); }
	.tree-icon { font-size: 10px; color: var(--accent); }
	.tree-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.tree-count { font-size: 10px; color: var(--text-muted); }

	.projects-section { padding: 4px 6px; border-bottom: 1px solid var(--border); }
	.section-header { display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; font-size: 10px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; font-weight: 600; }
	.section-add { background: none; border: 1px solid var(--border); color: var(--text-muted); padding: 2px 6px; border-radius: var(--radius-sm); cursor: pointer; font-size: 11px; transition: all var(--transition); }
	.section-add:hover { color: var(--accent); border-color: var(--accent); }
	.project-item { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 6px 10px; background: none; border: none; color: var(--text-secondary); cursor: pointer; border-radius: var(--radius-sm); font-size: 12px; text-align: left; transition: all var(--transition); }
	.project-item:hover { background: var(--bg-hover); }
	.project-item.active { background: var(--accent-subtle); color: var(--accent); }
	.project-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.project-count { font-size: 10px; color: var(--text-muted); background: var(--bg-primary); padding: 1px 5px; border-radius: 8px; }
	.project-badge { font-size: 9px; }

	.conv-item-wrapper { position: relative; display: flex; align-items: center; }
	.conv-item-wrapper .conv-item { flex: 1; }
	.conv-actions { display: flex; gap: 2px; opacity: 0; transition: opacity var(--transition); padding-right: 4px; }
	.conv-item-wrapper:hover .conv-actions { opacity: 1; }
	.conv-action { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 11px; padding: 2px 4px; border-radius: 3px; transition: all var(--transition); }
	.conv-action:hover { color: var(--accent); background: var(--accent-subtle); }
	.conv-action.delete:hover { color: var(--error); background: rgba(255,68,68,0.1); }

	.conv-list { flex: 1; overflow-y: auto; padding: 6px; }
	.conv-item { display: block; width: 100%; text-align: left; padding: 9px 10px; background: none; border: none; color: var(--text-primary); cursor: pointer; border-radius: var(--radius); margin-bottom: 2px; transition: all var(--transition); }
	.conv-item:hover { background: var(--bg-hover); }
	.conv-item.active { background: var(--accent-subtle); border-left: 2px solid var(--accent); }
	.conv-title { display: block; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.conv-meta { display: flex; gap: 6px; align-items: center; font-size: 11px; color: var(--text-muted); margin-top: 2px; }
	.conv-time { color: var(--text-muted); opacity: 0.7; }
	.badge { background: var(--accent-subtle); color: var(--accent); padding: 1px 6px; border-radius: 3px; font-size: 10px; margin-left: 4px; font-weight: 500; }
</style>
