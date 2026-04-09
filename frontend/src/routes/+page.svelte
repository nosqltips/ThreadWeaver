<script lang="ts">
	import {
		createConversation,
		listConversations,
		getConversation,
		sendMessage,
		branchConversation,
		searchConversations,
		createHighlight,
		getConversationTree,
		getSettings,
		listTools,
		connectMCP,
		listMCPServers,
		deleteConversation,
		archiveConversation,
		createProject,
		listProjects,
		addConversationToProject,
		getProvenance,
		type Message,
		type ConversationSummary,
		type ImageData,
	} from '$lib/api';

	const API_BASE = '/api';

	let conversations = $state<ConversationSummary[]>([]);
	let currentConvId = $state<string | null>(null);
	let messages = $state<Message[]>([]);
	let inputText = $state('');
	let streamingText = $state('');
	let isStreaming = $state(false);
	let searchQuery = $state('');
	let searchResults = $state<any[]>([]);
	let showSidebar = $state(true);
	let pendingImages = $state<ImageData[]>([]);
	let showNotebook = $state(false);
	let showSettings = $state(false);
	let notebooks = $state<any[]>([]);
	let convTree = $state<any>(null);
	let expandedNote = $state<number | null>(null);
	let noteComments = $state<Record<number, string[]>>({});
	let projects = $state<any[]>([]);
	let selectedProjectId = $state<string | null>(null);
	let showArchived = $state(false);
	let showProvenance = $state(false);
	let provenanceData = $state<any[]>([]);
	let mcpServers = $state<any>({});
	let showTools = $state(false);
	let toolsList = $state<any[]>([]);
	let mcpName = $state('');
	let mcpCommand = $state('');
	let mcpArgs = $state('');

	async function loadMCPServers() {
		try { mcpServers = await listMCPServers(); } catch {}
	}

	async function connectMCPServer() {
		if (!mcpName.trim() || !mcpCommand.trim()) return;
		try {
			const result = await connectMCP(mcpName.trim(), mcpCommand.trim(),
				mcpArgs.trim() ? mcpArgs.trim().split(' ') : []);
			mcpName = '';
			mcpCommand = '';
			mcpArgs = '';
			await loadMCPServers();
			await loadToolCount();
			alert(`Connected! ${result.tools} tools discovered: ${result.tool_names?.join(', ')}`);
		} catch (e) {
			alert(`Failed to connect: ${e}`);
		}
	}

	async function loadTools() {
		try { toolsList = await listTools(); } catch {}
	}

	async function disconnectMCPServer(name: string) {
		await fetch(`${API_BASE}/mcp/${name}`, { method: 'DELETE' });
		await loadMCPServers();
		await loadToolCount();
	}

	async function loadProvenance() {
		if (!currentConvId) { provenanceData = []; return; }
		try {
			provenanceData = await getProvenance(currentConvId);
		} catch { provenanceData = []; }
	}

	async function loadProjects() {
		try { projects = await listProjects(); } catch {}
	}

	async function deleteChat(convId: string) {
		if (!confirm('Delete this conversation?')) return;
		await deleteConversation(convId);
		if (currentConvId === convId) {
			currentConvId = null;
			messages = [];
		}
		await loadConversations();
	}

	async function archiveChat(convId: string) {
		await archiveConversation(convId);
		if (currentConvId === convId) {
			currentConvId = null;
			messages = [];
		}
		await loadConversations();
	}

	async function newProject() {
		const name = prompt('Project name:');
		if (!name) return;
		const desc = prompt('Description (optional):') || '';
		await createProject(name, desc);
		await loadProjects();
	}

	async function moveToProject(convId: string) {
		if (projects.length === 0) {
			alert('Create a project first.');
			return;
		}
		const projectId = prompt('Project ID (' + projects.map(p => p.id + ': ' + p.name).join(', ') + '):');
		if (!projectId) return;
		await addConversationToProject(convId, projectId);
		await loadConversations();
	}

	// Provider/model selection
	let selectedProvider = $state('anthropic');
	let providers = $state<any>({});
	let localModels = $state<any[]>([]);
	let toolCount = $state(0);

	async function loadSettings() {
		try {
			const settings = await getSettings();
			selectedProvider = settings.default_provider;
			providers = settings.providers || {};
		} catch {}
	}

	async function loadLocalModels() {
		try {
			const res = await fetch(`${API_BASE}/models/local`);
			const data = await res.json();
			localModels = data.models || [];
		} catch {}
	}

	async function loadToolCount() {
		try {
			const tools = await listTools();
			toolCount = tools.length;
		} catch {}
	}

	async function setProvider(provider: string) {
		selectedProvider = provider;
		await fetch(`${API_BASE}/settings/default`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ provider }),
		});
	}

	async function setLocalModel(model: string) {
		await fetch(`${API_BASE}/settings/provider/local`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ model }),
		});
		await loadSettings();
	}

	async function saveApiKey(provider: string, key: string) {
		await fetch(`${API_BASE}/settings/provider/${provider}`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ api_key: key }),
		});
		await loadSettings();
	}

	async function loadConversations() {
		try { conversations = await listConversations(); } catch {}
	}

	async function newChat() {
		const { id } = await createConversation();
		await loadConversations();
		await selectConversation(id);
	}

	async function selectConversation(id: string) {
		currentConvId = id;
		const conv = await getConversation(id);
		messages = conv.messages;
		try { convTree = await getConversationTree(id); } catch { convTree = null; }
	}

	async function send() {
		if (!inputText.trim() || isStreaming) return;
		if (!currentConvId) await newChat();

		const userMessage = inputText.trim();
		const images = pendingImages.length > 0 ? [...pendingImages] : undefined;
		inputText = '';
		pendingImages = [];

		messages = [...messages, {
			role: 'user', content: userMessage,
			timestamp: Date.now() / 1000, images
		}];

		isStreaming = true;
		streamingText = '';

		try {
			const fullResponse = await sendMessage(currentConvId!, userMessage, (partial) => {
				streamingText = partial;
			}, selectedProvider, images);
			messages = [...messages, { role: 'assistant', content: fullResponse, timestamp: Date.now() / 1000 }];
			streamingText = '';
		} catch (e) {
			messages = [...messages, { role: 'assistant', content: `Error: ${e}`, timestamp: Date.now() / 1000 }];
		}

		isStreaming = false;
		await loadConversations();
		if (showProvenance) loadProvenance();
	}

	async function branch(messageIndex: number) {
		if (!currentConvId) return;
		const { id } = await branchConversation(currentConvId, messageIndex);
		await loadConversations();
		await selectConversation(id);
	}

	async function highlight(startIdx: number, endIdx: number) {
		if (!currentConvId) return;
		const tag = prompt('Tag this highlight (optional):') || 'highlight';
		const result = await createHighlight(currentConvId, startIdx, endIdx, tag);
		notebooks = [...notebooks, result];
		showNotebook = true;
	}

	async function branchFromNote(noteIndex: number) {
		const note = notebooks[noteIndex];
		if (!note || !currentConvId) return;
		// Branch from the end of the highlighted messages
		const { id } = await branchConversation(currentConvId, note.end_index);
		await loadConversations();
		await selectConversation(id);
	}

	function addNoteComment(noteIndex: number) {
		const comment = prompt('Add a comment:');
		if (!comment) return;
		if (!noteComments[noteIndex]) noteComments[noteIndex] = [];
		noteComments[noteIndex] = [...noteComments[noteIndex], comment];
	}

	function setBackgroundColor(color: string) {
		document.documentElement.style.setProperty('--bg-primary', color);
		// Derive secondary/tertiary from primary
		document.documentElement.style.setProperty('--bg-secondary', lighten(color, 8));
		document.documentElement.style.setProperty('--bg-tertiary', lighten(color, 12));
		document.documentElement.style.setProperty('--bg-hover', lighten(color, 16));
		localStorage.setItem('tw-bg', color);
	}

	function lighten(hex: string, amount: number): string {
		const num = parseInt(hex.replace('#', ''), 16);
		const r = Math.min(255, (num >> 16) + amount);
		const g = Math.min(255, ((num >> 8) & 0xFF) + amount);
		const b = Math.min(255, (num & 0xFF) + amount);
		return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`;
	}

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

	async function doSearch() {
		if (!searchQuery.trim()) return;
		searchResults = await searchConversations(searchQuery);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
	}

	function handlePaste(e: ClipboardEvent) {
		const items = e.clipboardData?.items;
		if (!items) return;
		for (const item of items) {
			if (item.type.startsWith('image/')) {
				e.preventDefault();
				const blob = item.getAsFile();
				if (!blob) continue;
				const reader = new FileReader();
				reader.onload = () => {
					const base64 = (reader.result as string).split(',')[1];
					pendingImages = [...pendingImages, { data: base64, media_type: item.type }];
				};
				reader.readAsDataURL(blob);
			}
		}
	}

	function handleFileDrop(e: DragEvent) {
		e.preventDefault();
		const files = e.dataTransfer?.files;
		if (!files) return;
		for (const file of files) {
			if (file.type.startsWith('image/')) {
				const reader = new FileReader();
				reader.onload = () => {
					const base64 = (reader.result as string).split(',')[1];
					pendingImages = [...pendingImages, { data: base64, media_type: file.type }];
				};
				reader.readAsDataURL(file);
			}
		}
	}

	function removeImage(idx: number) {
		pendingImages = pendingImages.filter((_, i) => i !== idx);
	}

	$effect(() => {
		loadConversations();
		loadSettings();
		loadLocalModels();
		loadToolCount();
		loadProjects();
		loadMCPServers();
	});
</script>

<div class="layout">
	{#if showSidebar}
	<aside class="sidebar">
		<div class="sidebar-header">
			<h2>ThreadWeaver</h2>
			<button class="new-chat" onclick={newChat}>+ New Chat</button>
		</div>
		<div class="search-box">
			<input type="text" placeholder="Search..." bind:value={searchQuery}
				onkeydown={(e) => e.key === 'Enter' && doSearch()} />
		</div>
		{#if searchResults.length > 0}
		<div class="search-results">
			{#each searchResults as r}
			<button class="search-result" onclick={() => selectConversation(r.conversation_id)}>
				<span class="result-title">{r.conversation_title}</span>
				<span class="result-preview">{r.content_preview}</span>
			</button>
			{/each}
		</div>
		{/if}

		<!-- Branch tree -->
		{#if convTree && convTree.children && convTree.children.length > 0}
		<div class="tree-section">
			<h3>Branches</h3>
			<div class="tree">
				{#snippet treeNode(node: any, depth: number)}
					<button class="tree-item" style="padding-left: {8 + depth * 16}px"
						class:active={node.id === currentConvId}
						onclick={() => selectConversation(node.id)}>
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

		<!-- Projects -->
		{#if projects.length > 0}
		<div class="projects-section">
			<div class="section-header">
				<span>Projects</span>
				<button class="section-add" onclick={newProject}>+</button>
			</div>
			{#each projects as proj}
			<button class="project-item" class:active={selectedProjectId === proj.id}
				onclick={() => selectedProjectId = selectedProjectId === proj.id ? null : proj.id}>
				<span class="project-name">📁 {proj.name}</span>
				<span class="project-count">{proj.chat_count}</span>
			</button>
			{/each}
		</div>
		{:else}
		<div class="section-header" style="padding: 4px 14px;">
			<span></span>
			<button class="section-add" title="New Project" onclick={newProject}>📁+</button>
		</div>
		{/if}

		<div class="conv-list">
			{#each conversations.filter(c => !selectedProjectId || c.project_id === selectedProjectId) as conv}
			<div class="conv-item-wrapper">
				<button class="conv-item" class:active={conv.id === currentConvId}
					onclick={() => selectConversation(conv.id)}>
					<span class="conv-title">{conv.title}</span>
					<span class="conv-meta">
						<span>{conv.message_count} msgs</span>
						<span class="conv-time">{formatTime(conv.created_at)}</span>
						{#if conv.parent_id}<span class="badge">branch</span>{/if}
						{#if conv.project_id}<span class="badge project-badge">📁</span>{/if}
					</span>
				</button>
				<div class="conv-actions">
					<button class="conv-action" title="Move to project" onclick={() => moveToProject(conv.id)}>📁</button>
					<button class="conv-action" title="Archive" onclick={() => archiveChat(conv.id)}>📥</button>
					<button class="conv-action delete" title="Delete" onclick={() => deleteChat(conv.id)}>✕</button>
				</div>
			</div>
			{/each}

			{#if conversations.length === 0}
			<p style="text-align: center; color: var(--text-muted); font-size: 13px; padding: 20px;">No conversations yet</p>
			{/if}
		</div>
	</aside>
	{/if}

	<main class="chat">
		<div class="chat-header">
			<button class="toggle" onclick={() => showSidebar = !showSidebar}>
				{showSidebar ? '◀' : '▶'}
			</button>
			<h3>{conversations.find(c => c.id === currentConvId)?.title || 'ThreadWeaver'}</h3>
			<div class="header-actions">
				<!-- Provider/model selector -->
				<select class="provider-select" bind:value={selectedProvider} onchange={(e) => setProvider(e.currentTarget.value)}>
					{#each Object.entries(providers) as [name, p]}
						<option value={name}>{p.label || name}{p.api_key_set ? '' : ' ⚠'}</option>
					{/each}
				</select>

				{#if selectedProvider === 'local' && localModels.length > 1}
				<select class="model-select" onchange={(e) => setLocalModel(e.currentTarget.value)}>
					{#each localModels as m}
						<option value={m.name} selected={m.name === providers?.local?.model}>{m.name}</option>
					{/each}
				</select>
				{:else if selectedProvider === 'local' && localModels.length === 1}
				<span class="model-label">{localModels[0].name}</span>
				{/if}

				<button class="header-icon-btn" title="Settings" onclick={() => { showSettings = !showSettings; showNotebook = false; showProvenance = false; showTools = false; if (showSettings) loadLocalModels(); }}
					class:active={showSettings}>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
				</button>
				<button class="header-icon-btn" title="Provenance" onclick={() => { showProvenance = !showProvenance; showSettings = false; showNotebook = false; showTools = false; if (showProvenance) loadProvenance(); }}
					class:active={showProvenance}>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20v-6M6 20V10M18 20V4"/></svg>
				</button>
				<button class="header-icon-btn" title="Notebook" onclick={() => { showNotebook = !showNotebook; showSettings = false; showProvenance = false; showTools = false; }}
					class:active={showNotebook}>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/><path d="M8 7h6"/><path d="M8 11h8"/></svg>
					{#if notebooks.length > 0}<span class="icon-badge">{notebooks.length}</span>{/if}
				</button>
				{#if toolCount > 0}
				<button class="header-icon-btn" title="{toolCount} tools available"
					class:active={showTools}
					onclick={() => { showTools = !showTools; showSettings = false; showNotebook = false; showProvenance = false; if (showTools) loadTools(); }}>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
					<span class="icon-badge">{toolCount}</span>
				</button>
				{/if}
			</div>
		</div>

		<div class="main-content">
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
				<div class="msg {msg.role}">
					<div class="msg-header">
						<div class="msg-meta">
							<span class="role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
							<span class="msg-time">{new Date(msg.timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>
						</div>
						<div class="msg-actions">
							<button class="action-btn" title="Save to notebook" onclick={() => highlight(i, i)}>
								<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
							</button>
							<button class="action-btn" title="Branch from here" onclick={() => branch(i)}>
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
					<div class="msg-content">{msg.content}</div>
				</div>
				{/each}

				{#if isStreaming && streamingText}
				<div class="msg assistant streaming">
					<div class="msg-header">
						<span class="role">Assistant</span>
						<span class="dot">●</span>
					</div>
					<div class="msg-content">{streamingText}</div>
				</div>
				{/if}
			</div>

			<!-- Settings panel -->
			{#if showSettings}
			<div class="settings-panel">
				<div class="settings-header">
					<h3>⚙ Settings</h3>
					<button class="close-btn" onclick={() => showSettings = false}>✕</button>
				</div>

				{#each Object.entries(providers) as [name, p]}
				<div class="setting-group">
					<div class="setting-label">{p.label || name}</div>
					{#if name !== 'local'}
					<div class="setting-row">
						<input type="password" placeholder="API Key"
							value={p.api_key_set ? '••••••••' : ''}
							onchange={(e) => saveApiKey(name, e.currentTarget.value)} />
						{#if p.api_key_set}<span class="key-ok">✓</span>{/if}
					</div>
					{/if}
					<div class="setting-row">
						{#if name === 'local' && localModels.length > 0}
						<select onchange={(e) => setLocalModel(e.currentTarget.value)}>
							{#each localModels as m}
							<option value={m.name} selected={m.name === p.model}>{m.name}</option>
							{/each}
						</select>
						<button class="refresh-btn" onclick={loadLocalModels}>↻</button>
						{:else}
						<input type="text" placeholder="Model" value={p.model || ''}
							onchange={(e) => fetch(`${API_BASE}/settings/provider/${name}`, {
								method: 'PUT', headers: {'Content-Type': 'application/json'},
								body: JSON.stringify({model: e.currentTarget.value})
							}).then(loadSettings)} />
						{/if}
					</div>
					{#if p.base_url}
					<div class="setting-row">
						<input type="text" placeholder="Base URL" value={p.base_url}
							onchange={(e) => fetch(`${API_BASE}/settings/provider/${name}`, {
								method: 'PUT', headers: {'Content-Type': 'application/json'},
								body: JSON.stringify({base_url: e.currentTarget.value})
							}).then(loadSettings)} />
					</div>
					{/if}
				</div>
				{/each}

				{#if localModels.length === 0}
				<div class="setting-note">
					No local models found. Install <a href="https://ollama.com" target="_blank">Ollama</a> and run <code>ollama pull llama3</code>
				</div>
				{/if}

				<!-- Accent color picker -->
				<div class="setting-group">
					<div class="setting-label">Accent Color</div>
					<div class="color-picker-row">
						{#each [
							'#7b68ee', '#6366f1', '#3b82f6', '#06b6d4', '#10b981',
							'#f59e0b', '#ef4444', '#ec4899', '#8b5cf6', '#14b8a6',
						] as color}
						<button class="color-swatch"
							style="background: {color}"
							onclick={() => {
								document.documentElement.style.setProperty('--accent', color);
								document.documentElement.style.setProperty('--accent-glow', color + '33');
								document.documentElement.style.setProperty('--accent-subtle', color + '18');
								localStorage.setItem('tw-accent', color);
							}}
						></button>
						{/each}
					</div>
				</div>

				<!-- Background color picker -->
				<div class="setting-group">
					<div class="setting-label">Background</div>
					<div class="color-picker-row">
						{#each [
							'#0f0f1a', '#0d1117', '#1a1a2e', '#0f172a', '#18181b',
							'#1c1917', '#0c0a09', '#0a0a0a', '#111827', '#0e1629',
						] as color}
						<button class="color-swatch bg-swatch"
							style="background: {color}; border: 2px solid #333"
							onclick={() => setBackgroundColor(color)}
						></button>
						{/each}
					</div>
				</div>
			</div>
			{/if}

						<!-- MCP Servers -->
				<div class="setting-group">
					<div class="setting-label">MCP Servers</div>
					{#if Object.keys(mcpServers).length > 0}
					<div class="mcp-list">
						{#each Object.entries(mcpServers) as [name, server]}
						<div class="mcp-server">
							<div class="mcp-server-info">
								<span class="mcp-name">{name}</span>
								<span class="mcp-tools">{server.tools} tools</span>
							</div>
							<button class="mcp-disconnect" onclick={() => disconnectMCPServer(name)}>x</button>
						</div>
						{/each}
					</div>
					{/if}
					<div class="mcp-presets">
						<div class="mcp-presets-title">Quick Connect</div>
						{#each [
							{name: 'filesystem', cmd: 'npx', args: '@modelcontextprotocol/server-filesystem /home', desc: 'File access'},
							{name: 'github', cmd: 'npx', args: '@modelcontextprotocol/server-github', desc: 'GitHub repos & issues'},
							{name: 'sqlite', cmd: 'npx', args: '@modelcontextprotocol/server-sqlite --db-path ./data.db', desc: 'SQLite queries'},
							{name: 'memory', cmd: 'npx', args: '@modelcontextprotocol/server-memory', desc: 'Knowledge graph'},
							{name: 'brave-search', cmd: 'npx', args: '@modelcontextprotocol/server-brave-search', desc: 'Web search'},
						] as preset}
						<button class="mcp-preset" onclick={() => { mcpName = preset.name; mcpCommand = preset.cmd; mcpArgs = preset.args; }}>
							<span class="mcp-preset-name">{preset.name}</span>
							<span class="mcp-preset-desc">{preset.desc}</span>
						</button>
						{/each}
					</div>

					<div class="mcp-connect-form">
						<input type="text" placeholder="Server name" bind:value={mcpName} />
						<input type="text" placeholder="Command (e.g., npx or /path/to/binary)" bind:value={mcpCommand} />
						<input type="text" placeholder="Args (e.g., @modelcontextprotocol/server-github)" bind:value={mcpArgs} />
						<button class="mcp-connect-btn" onclick={connectMCPServer}
							disabled={!mcpName.trim() || !mcpCommand.trim()}>Connect</button>
					</div>
					<div class="setting-note">
						Click a preset to fill the form, then Connect. Or enter any MCP server command.
						<br/><a href="https://modelcontextprotocol.io/servers" target="_blank">Browse 100+ MCP servers</a>
						 · <a href="https://mcp.so" target="_blank">mcp.so directory</a>
					</div>
				</div>

			<!-- Tools panel -->
			{#if showTools}
			<div class="tools-panel">
				<div class="tools-header">
					<h3>Tools</h3>
					<span class="tools-count">{toolsList.length} available</span>
					<button class="close-btn" onclick={() => showTools = false}>✕</button>
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
			{/if}

			<!-- Provenance panel (AgentStateGraph) -->
			{#if showProvenance}
			<div class="provenance-panel">
				<div class="provenance-header">
					<h3>Provenance</h3>
					<div class="provenance-badge">AgentStateGraph</div>
					<button class="close-btn" onclick={() => showProvenance = false}>✕</button>
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
			{/if}

			<!-- Notebook panel -->
			{#if showNotebook}
			<div class="notebook">
				<div class="notebook-header">
					<h3>Notebook</h3>
					<button class="close-btn" onclick={() => { showNotebook = false; expandedNote = null; }}>✕</button>
				</div>
				{#if notebooks.length === 0}
				<p class="notebook-empty">No highlights yet. Click the bookmark icon on any message to save it.</p>
				{:else}
				{#each notebooks as note, i}
				<div class="note" class:expanded={expandedNote === i}>
					<div class="note-header" onclick={() => expandedNote = expandedNote === i ? null : i}>
						<span class="note-tag">{note.tag}</span>
						<span class="note-preview">
							{#if expandedNote !== i}
								{note.messages[0]?.content.slice(0, 60)}{note.messages[0]?.content.length > 60 ? '...' : ''}
							{/if}
						</span>
						<span class="note-expand">{expandedNote === i ? '▾' : '▸'}</span>
					</div>

					{#if expandedNote === i}
					<div class="note-body">
						{#each note.messages as m}
						<div class="note-full-msg">
							<span class="note-role">{m.role}</span>
							<div class="note-content">{m.content}</div>
						</div>
						{/each}

						<!-- Comments -->
						{#if noteComments[i]?.length}
						<div class="note-comments">
							<div class="note-comments-title">Comments</div>
							{#each noteComments[i] as comment}
							<div class="note-comment">{comment}</div>
							{/each}
						</div>
						{/if}

						<!-- Actions -->
						<div class="note-actions">
							<button class="note-action-btn" onclick={() => addNoteComment(i)}>
								💬 Comment
							</button>
							<button class="note-action-btn" onclick={() => branchFromNote(i)}>
								⑂ New Chat
							</button>
							<button class="note-action-btn" onclick={() => {
								navigator.clipboard.writeText(note.messages.map(m => `${m.role}: ${m.content}`).join('\n\n'));
							}}>
								📋 Copy
							</button>
						</div>
					</div>
					{/if}
				</div>
				{/each}
				{/if}
			</div>
			{/if}
		</div>

		<div class="input-area"
			ondragover={(e) => e.preventDefault()}
			ondrop={handleFileDrop}>
			{#if pendingImages.length > 0}
			<div class="image-preview">
				{#each pendingImages as img, i}
				<div class="preview-thumb">
					<img src="data:{img.media_type};base64,{img.data}" alt="preview" />
					<button class="remove-img" onclick={() => removeImage(i)}>✕</button>
				</div>
				{/each}
			</div>
			{/if}
			<div class="input-row">
				<textarea placeholder="Type a message... (Paste images, Enter to send)"
					bind:value={inputText}
					onkeydown={handleKeydown}
					onpaste={handlePaste}
					disabled={isStreaming} rows="3"></textarea>
				<button class="send" onclick={send} disabled={isStreaming || (!inputText.trim() && pendingImages.length === 0)}>
					{isStreaming ? '...' : 'Send'}
				</button>
			</div>
		</div>
	</main>
</div>

<style>
	.layout { display: flex; height: 100vh; width: 100%; }

	/* Sidebar with slide transition */
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

	/* Branch tree */
	.tree-section { padding: 8px 6px; border-bottom: 1px solid var(--border); }
	.tree-section h3 { margin: 0 0 6px 8px; font-size: 10px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; font-weight: 600; }
	.tree-item { display: flex; align-items: center; gap: 6px; width: 100%; text-align: left; padding: 5px 8px; background: none; border: none; color: var(--text-secondary); cursor: pointer; border-radius: var(--radius-sm); font-size: 12px; transition: all var(--transition); }
	.tree-item:hover { background: var(--bg-hover); color: var(--text-primary); }
	.tree-item.active { background: var(--accent-subtle); color: var(--accent); }
	.tree-icon { font-size: 10px; color: var(--accent); }
	.tree-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.tree-count { font-size: 10px; color: var(--text-muted); }

	/* Projects section */
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

	/* Conversation item with actions */
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

	/* Chat area */
	.chat { flex: 1; display: flex; flex-direction: column; min-width: 0; }
	.chat-header { padding: 10px 14px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px; backdrop-filter: blur(8px); }
	.chat-header h3 { margin: 0; font-size: 14px; color: var(--text-secondary); flex: 1; font-weight: 500; }
	.toggle { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 4px 8px; transition: color var(--transition); }
	.toggle:hover { color: var(--accent); }
	.header-actions { display: flex; gap: 6px; align-items: center; }
	.header-icon-btn { background: none; border: 1px solid var(--border); color: var(--text-muted); padding: 6px 8px; border-radius: var(--radius-sm); cursor: pointer; transition: all var(--transition); display: flex; align-items: center; justify-content: center; position: relative; min-width: 36px; min-height: 36px; }
	.header-icon-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }
	.header-icon-btn.active { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }
	.header-icon-btn svg { flex-shrink: 0; }
	.icon-badge { position: absolute; top: -4px; right: -4px; background: var(--accent); color: #fff; font-size: 9px; font-weight: 700; padding: 1px 4px; border-radius: 8px; min-width: 16px; text-align: center; }

	.main-content { flex: 1; display: flex; overflow: hidden; }
	.messages { flex: 1; overflow-y: auto; padding: 16px; scroll-behavior: smooth; }

	/* Welcome screen */
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

	/* Messages with animations */
	.msg { margin-bottom: 14px; padding: 12px 16px; border-radius: var(--radius-lg); max-width: 800px; animation: fadeIn 0.3s ease; transition: box-shadow var(--transition); }
	.msg:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.2); }
	.msg.user { background: var(--bg-tertiary); margin-left: auto; animation: slideInRight 0.3s ease; border: 1px solid transparent; }
	.msg.user:hover { border-color: var(--border); }
	.msg.assistant { background: var(--bg-secondary); border: 1px solid var(--border); animation: slideInLeft 0.3s ease; }
	.msg.streaming { border-color: var(--accent-glow); box-shadow: 0 0 16px var(--accent-glow); }
	.msg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
	.msg-meta { display: flex; align-items: center; gap: 8px; }
	.role { font-size: 10px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
	.msg-time { font-size: 10px; color: var(--text-muted); font-weight: 400; }
	.msg-actions { display: flex; gap: 4px; opacity: 0; transition: opacity var(--transition); }
	.msg:hover .msg-actions { opacity: 1; }
	.action-btn { background: none; border: 1px solid var(--border); color: var(--text-muted); font-size: 11px; padding: 3px 8px; border-radius: var(--radius-sm); cursor: pointer; transition: all var(--transition); }
	.action-btn:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-subtle); transform: scale(1.05); }
	.dot { color: var(--accent); animation: pulse 1s infinite; }
	.msg-content { font-size: 14px; line-height: 1.7; white-space: pre-wrap; word-wrap: break-word; }
	.msg-images { margin-bottom: 8px; }
	.attached-image { max-width: 300px; max-height: 200px; border-radius: var(--radius); border: 1px solid var(--border); transition: transform var(--transition); }
	.attached-image:hover { transform: scale(1.02); }

	/* Tools panel */
	.tools-panel { width: 300px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.tools-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
	.tools-header h3 { margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; flex: 1; }
	.tools-count { font-size: 10px; color: var(--text-muted); background: var(--bg-tertiary); padding: 2px 6px; border-radius: 8px; }
	.tools-empty { font-size: 13px; color: var(--text-muted); padding: 20px; text-align: center; }
	.tools-list { display: flex; flex-direction: column; gap: 6px; }
	.tool-item { padding: 8px 10px; background: var(--bg-tertiary); border-radius: var(--radius); border: 1px solid var(--border); transition: all var(--transition); }
	.tool-item:hover { border-color: var(--accent); }
	.tool-name { font-size: 12px; font-weight: 600; color: var(--accent); font-family: monospace; margin-bottom: 3px; }
	.tool-desc { font-size: 11px; color: var(--text-muted); line-height: 1.4; }

	/* Provenance panel */
	.provenance-panel { width: 320px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.provenance-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
	.provenance-header h3 { margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; flex: 1; }
	.provenance-badge { font-size: 9px; color: var(--accent); background: var(--accent-subtle); border: 1px solid var(--accent); padding: 2px 6px; border-radius: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
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

	/* MCP servers in settings */
	.mcp-list { margin-bottom: 8px; }
	.mcp-server { display: flex; align-items: center; justify-content: space-between; padding: 6px 8px; background: var(--bg-primary); border-radius: var(--radius-sm); margin-bottom: 4px; }
	.mcp-server-info { display: flex; gap: 8px; align-items: center; }
	.mcp-name { font-size: 12px; color: var(--text-primary); font-weight: 500; }
	.mcp-tools { font-size: 10px; color: var(--accent); background: var(--accent-subtle); padding: 1px 5px; border-radius: 3px; }
	.mcp-disconnect { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 12px; padding: 2px 6px; border-radius: 3px; transition: all var(--transition); }
	.mcp-disconnect:hover { color: var(--error); background: rgba(255,68,68,0.1); }
	.mcp-presets { margin-bottom: 8px; }
	.mcp-presets-title { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 4px; }
	.mcp-preset { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 5px 8px; background: var(--bg-primary); border: 1px solid transparent; border-radius: var(--radius-sm); cursor: pointer; text-align: left; margin-bottom: 3px; transition: all var(--transition); }
	.mcp-preset:hover { border-color: var(--accent); background: var(--accent-subtle); }
	.mcp-preset-name { font-size: 12px; color: var(--text-primary); font-weight: 500; }
	.mcp-preset-desc { font-size: 10px; color: var(--text-muted); }
	.mcp-connect-form { display: flex; flex-direction: column; gap: 4px; }
	.mcp-connect-form input { padding: 6px 9px; background: var(--bg-primary); border: 1px solid transparent; border-radius: var(--radius-sm); color: var(--text-primary); font-size: 12px; transition: all var(--transition); }
	.mcp-connect-form input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }
	.mcp-connect-btn { padding: 6px 12px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 12px; font-weight: 500; transition: all var(--transition); margin-top: 4px; }
	.mcp-connect-btn:hover:not(:disabled) { filter: brightness(1.15); }
	.mcp-connect-btn:disabled { opacity: 0.4; cursor: not-allowed; }

	/* Side panels with animation */
	.notebook, .settings-panel { width: 300px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.notebook-header, .settings-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
	.notebook-header h3, .settings-header h3 { margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; }
	.close-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; transition: all var(--transition); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); }
	.close-btn:hover { color: var(--error); background: rgba(255,68,68,0.1); }
	.notebook-empty { color: var(--text-muted); font-size: 13px; text-align: center; padding: 30px 20px; }
	.note { background: var(--bg-tertiary); border-radius: var(--radius); margin-bottom: 8px; border-left: 3px solid var(--accent); animation: scaleIn 0.2s ease; transition: all var(--transition); overflow: hidden; }
	.note:hover { border-left-width: 4px; }
	.note.expanded { border-left-color: var(--accent); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
	.note-header { padding: 10px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; }
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

	/* Settings panel */
	.setting-group { background: var(--bg-tertiary); border-radius: var(--radius); padding: 12px; margin-bottom: 10px; transition: border var(--transition); border: 1px solid transparent; }
	.setting-group:hover { border-color: var(--border); }
	.setting-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }
	.setting-row { display: flex; gap: 4px; margin-bottom: 4px; }
	.setting-row input, .setting-row select { flex: 1; padding: 6px 9px; background: var(--bg-primary); border: 1px solid transparent; border-radius: var(--radius-sm); color: var(--text-primary); font-size: 12px; transition: all var(--transition); }
	.setting-row input:focus, .setting-row select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }
	.key-ok { color: var(--success); font-size: 14px; padding: 4px; animation: scaleIn 0.2s ease; }
	.refresh-btn { background: none; border: 1px solid var(--border); color: var(--text-muted); padding: 5px 9px; border-radius: var(--radius-sm); cursor: pointer; font-size: 12px; transition: all var(--transition); }
	.refresh-btn:hover { color: var(--accent); border-color: var(--accent); transform: rotate(180deg); }
	.setting-note { font-size: 12px; color: var(--text-muted); padding: 10px; line-height: 1.5; }
	.setting-note a { color: var(--accent); }
	.setting-note code { background: var(--bg-tertiary); padding: 2px 5px; border-radius: 3px; font-size: 11px; }

	/* Color picker */
	.color-picker-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
	.color-swatch { width: 28px; height: 28px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; transition: all var(--transition); }
	.color-swatch:hover { transform: scale(1.2); }
	.color-swatch.active { border-color: #fff; box-shadow: 0 0 8px var(--accent-glow); }

	/* Input area */
	.input-area { padding: 14px; border-top: 1px solid var(--border); background: var(--bg-secondary); }
	.image-preview { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; animation: fadeIn 0.2s ease; }
	.preview-thumb { position: relative; animation: scaleIn 0.2s ease; }
	.preview-thumb img { width: 60px; height: 60px; object-fit: cover; border-radius: var(--radius); border: 1px solid var(--border); transition: all var(--transition); }
	.preview-thumb img:hover { border-color: var(--accent); }
	.remove-img { position: absolute; top: -4px; right: -4px; background: var(--error); color: #fff; border: none; border-radius: 50%; width: 18px; height: 18px; font-size: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: transform var(--transition); }
	.remove-img:hover { transform: scale(1.2); }
	.input-row { display: flex; gap: 8px; }
	.input-row textarea { flex: 1; padding: 11px 14px; background: var(--bg-tertiary); border: 1px solid transparent; border-radius: var(--radius); color: var(--text-primary); font-size: 14px; font-family: inherit; resize: none; transition: all var(--transition); }
	.input-row textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
	.send { padding: 11px 20px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius); cursor: pointer; align-self: flex-end; font-weight: 500; transition: all var(--transition); }
	.send:hover:not(:disabled) { filter: brightness(1.15); transform: translateY(-1px); box-shadow: 0 4px 12px var(--accent-glow); }
	.send:active:not(:disabled) { transform: translateY(0); }
	.send:disabled { opacity: 0.4; cursor: not-allowed; }

	/* Provider/model selector */
	.model-label { font-size: 12px; color: var(--text-muted); padding: 5px 10px; background: var(--bg-tertiary); border-radius: var(--radius-sm); border: 1px solid var(--border); }
	.provider-select, .model-select { background: var(--bg-tertiary); color: var(--text-secondary); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 5px 10px; font-size: 12px; cursor: pointer; transition: all var(--transition); }
	.provider-select:hover, .model-select:hover { border-color: var(--accent); }
	.provider-select:focus, .model-select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }
	.tool-badge { font-size: 11px; color: var(--text-muted); padding: 4px 8px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
</style>
