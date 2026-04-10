<script lang="ts">
	let {
		title, showSidebar = $bindable(),
		selectedProvider = $bindable(), providers,
		localModels, defaultLocalModel,
		toolCount, mcpServerCount, notebookCount, hasMessages,
		showSettings, showProvenance, showNotebook, showTools, showMCP,
		onSetProvider, onSetLocalModel, onTogglePanel,
		onExportMarkdown, onExportJSON,
	}: {
		title: string;
		showSidebar: boolean;
		selectedProvider: string;
		providers: any;
		localModels: any[];
		defaultLocalModel: string;
		toolCount: number;
		mcpServerCount: number;
		notebookCount: number;
		hasMessages: boolean;
		showSettings: boolean;
		showProvenance: boolean;
		showNotebook: boolean;
		showTools: boolean;
		showMCP: boolean;
		onSetProvider: (p: string) => void | Promise<void>;
		onSetLocalModel: (m: string) => void | Promise<void>;
		onTogglePanel: (panel: 'settings' | 'provenance' | 'notebook' | 'mcp' | 'tools') => void;
		onExportMarkdown: () => void;
		onExportJSON: () => void;
	} = $props();

	let exportOpen = $state(false);

	function toggleExport(e: MouseEvent) {
		e.stopPropagation();
		exportOpen = !exportOpen;
	}

	$effect(() => {
		if (!exportOpen) return;
		const handler = () => exportOpen = false;
		window.addEventListener('click', handler);
		return () => window.removeEventListener('click', handler);
	});
</script>

<div class="chat-header">
	<button class="toggle" onclick={() => showSidebar = !showSidebar}>
		{showSidebar ? '◀' : '▶'}
	</button>
	<h3>{title}</h3>
	<div class="header-actions">
		<select class="provider-select" bind:value={selectedProvider} onchange={(e) => onSetProvider(e.currentTarget.value)}>
			{#each Object.entries(providers) as [name, p]}
				<option value={name}>{(p as any).label || name}{(p as any).api_key_set ? '' : ' ⚠'}</option>
			{/each}
		</select>

		{#if selectedProvider === 'local' && localModels.length > 1}
		<select class="model-select" onchange={(e) => onSetLocalModel(e.currentTarget.value)}>
			{#each localModels as m}
				<option value={m.name} selected={m.name === (providers?.local?.model || defaultLocalModel)}>{m.name}</option>
			{/each}
		</select>
		{:else if selectedProvider === 'local' && localModels.length === 1}
		<span class="model-label">{localModels[0].name}</span>
		{/if}

		{#if hasMessages}
		<div class="export-wrapper">
			<button class="header-icon-btn" title="Export conversation" onclick={toggleExport}>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
			</button>
			{#if exportOpen}
			<div class="export-menu" role="menu">
				<button class="export-item" onclick={() => { exportOpen = false; onExportMarkdown(); }}>📄 Markdown (.md)</button>
				<button class="export-item" onclick={() => { exportOpen = false; onExportJSON(); }}>{'{}'} JSON (.json)</button>
			</div>
			{/if}
		</div>
		{/if}

		<button class="header-icon-btn" title="Settings"
			class:active={showSettings}
			onclick={() => onTogglePanel('settings')}>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
		</button>
		<button class="header-icon-btn" title="Provenance"
			class:active={showProvenance}
			onclick={() => onTogglePanel('provenance')}>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20v-6M6 20V10M18 20V4"/></svg>
		</button>
		<button class="header-icon-btn" title="Notebook"
			class:active={showNotebook}
			onclick={() => onTogglePanel('notebook')}>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/><path d="M8 7h6"/><path d="M8 11h8"/></svg>
			{#if notebookCount > 0}<span class="icon-badge">{notebookCount}</span>{/if}
		</button>
		<span class="header-separator"></span>
		<button class="header-icon-btn" title="MCP Servers"
			class:active={showMCP}
			onclick={() => onTogglePanel('mcp')}>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/><line x1="1" y1="16" x2="23" y2="16"/><circle cx="5" cy="7" r="1" fill="currentColor"/><circle cx="5" cy="13" r="1" fill="currentColor"/><circle cx="5" cy="19" r="1" fill="currentColor"/></svg>
			{#if mcpServerCount > 0}<span class="icon-badge">{mcpServerCount}</span>{/if}
		</button>
		{#if toolCount > 0}
		<button class="header-icon-btn" title="{toolCount} tools available"
			class:active={showTools}
			onclick={() => onTogglePanel('tools')}>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
			<span class="icon-badge">{toolCount}</span>
		</button>
		{/if}
	</div>
</div>

<style>
	.chat-header { padding: 10px 14px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px; backdrop-filter: blur(8px); }
	.chat-header h3 { margin: 0; font-size: 14px; color: var(--text-secondary); flex: 1; font-weight: 500; }
	.toggle { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 4px 8px; transition: color var(--transition); }
	.toggle:hover { color: var(--accent); }
	.header-actions { display: flex; gap: 6px; align-items: center; }
	.header-separator { width: 1px; height: 20px; background: var(--border); margin: 0 2px; }
	.header-icon-btn { background: none; border: 1px solid var(--border); color: var(--text-muted); padding: 6px 8px; border-radius: var(--radius-sm); cursor: pointer; transition: all var(--transition); display: flex; align-items: center; justify-content: center; position: relative; min-width: 36px; min-height: 36px; }
	.header-icon-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }
	.header-icon-btn.active { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }
	.header-icon-btn svg { flex-shrink: 0; }
	.icon-badge { position: absolute; top: -4px; right: -4px; background: var(--accent); color: #fff; font-size: 9px; font-weight: 700; padding: 1px 4px; border-radius: 8px; min-width: 16px; text-align: center; }

	.model-label { font-size: 12px; color: var(--text-muted); padding: 5px 10px; background: var(--bg-tertiary); border-radius: var(--radius-sm); border: 1px solid var(--border); }
	.provider-select, .model-select { background: var(--bg-tertiary); color: var(--text-secondary); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 5px 10px; font-size: 12px; cursor: pointer; transition: all var(--transition); }
	.provider-select:hover, .model-select:hover { border-color: var(--accent); }
	.provider-select:focus, .model-select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }

	.export-wrapper { position: relative; }
	.export-menu { position: absolute; top: calc(100% + 4px); right: 0; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: 0 6px 20px rgba(0,0,0,0.4); padding: 4px; min-width: 180px; z-index: 100; animation: fadeIn 0.15s ease; }
	.export-item { display: block; width: 100%; padding: 8px 12px; background: none; border: none; color: var(--text-primary); font-size: 13px; text-align: left; cursor: pointer; border-radius: var(--radius-sm); transition: background var(--transition); }
	.export-item:hover { background: var(--accent-subtle); color: var(--accent); }
</style>
