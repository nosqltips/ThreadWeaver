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
		abortCurrentStream,
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
	import { exportMarkdown, exportJSON } from '$lib/export';

	import Sidebar from '$lib/components/Sidebar.svelte';
	import ChatHeader from '$lib/components/ChatHeader.svelte';
	import MessageList from '$lib/components/MessageList.svelte';
	import InputArea from '$lib/components/InputArea.svelte';
	import SettingsPanel from '$lib/components/SettingsPanel.svelte';
	import MCPPanel from '$lib/components/MCPPanel.svelte';
	import ToolsPanel from '$lib/components/ToolsPanel.svelte';
	import ProvenancePanel from '$lib/components/ProvenancePanel.svelte';
	import NotebookPanel from '$lib/components/NotebookPanel.svelte';

	const API_BASE = '/api';

	// Conversation state
	let conversations = $state<ConversationSummary[]>([]);
	let currentConvId = $state<string | null>(null);
	let messages = $state<Message[]>([]);
	let convTree = $state<any>(null);
	let projects = $state<any[]>([]);
	let selectedProjectId = $state<string | null>(null);

	// Input/streaming
	let inputText = $state('');
	let pendingImages = $state<ImageData[]>([]);
	let isStreaming = $state(false);
	let streamingText = $state('');

	// Search
	let searchQuery = $state('');
	let searchResults = $state<any[]>([]);

	// UI state
	let showSidebar = $state(true);
	let showNotebook = $state(false);
	let showSettings = $state(false);
	let showProvenance = $state(false);
	let showTools = $state(false);
	let showMCP = $state(false);

	// Notebook
	let notebooks = $state<any[]>([]);
	let noteComments = $state<Record<number, string[]>>({});

	// Provenance / tools / MCP
	let provenanceData = $state<any[]>([]);
	let mcpServers = $state<any>({});
	let toolsList = $state<any[]>([]);
	let toolCount = $state(0);

	// Provider/model
	let selectedProvider = $state('anthropic');
	let providers = $state<any>({});
	let localModels = $state<any[]>([]);
	let defaultLocalModel = $state('');

	const currentTitle = $derived(
		conversations.find(c => c.id === currentConvId)?.title || 'ThreadWeaver'
	);

	function closeAllPanels() {
		showSettings = false;
		showProvenance = false;
		showNotebook = false;
		showTools = false;
		showMCP = false;
	}

	function togglePanel(panel: 'settings' | 'provenance' | 'notebook' | 'mcp' | 'tools') {
		const flag = {
			settings: showSettings,
			provenance: showProvenance,
			notebook: showNotebook,
			mcp: showMCP,
			tools: showTools,
		}[panel];
		const next = !flag;
		closeAllPanels();
		if (panel === 'settings') { showSettings = next; if (next) loadLocalModels(); }
		if (panel === 'provenance') { showProvenance = next; if (next) loadProvenance(); }
		if (panel === 'notebook') showNotebook = next;
		if (panel === 'mcp') { showMCP = next; if (next) loadMCPServers(); }
		if (panel === 'tools') { showTools = next; if (next) loadTools(); }
	}

	// ─── data loaders ─────────────────────────────────────
	async function loadConversations() { try { conversations = await listConversations(); } catch {} }
	async function loadProjects() { try { projects = await listProjects(); } catch {} }
	async function loadMCPServers() { try { mcpServers = await listMCPServers(); } catch {} }
	async function loadTools() { try { toolsList = await listTools(); } catch {} }
	async function loadToolCount() { try { toolCount = (await listTools()).length; } catch {} }

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
			defaultLocalModel = data.default || '';
		} catch {}
	}

	async function loadProvenance() {
		if (!currentConvId) { provenanceData = []; return; }
		try { provenanceData = await getProvenance(currentConvId); } catch { provenanceData = []; }
	}

	// ─── conversation actions ─────────────────────────────
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

	async function deleteChat(convId: string) {
		if (!confirm('Delete this conversation?')) return;
		await deleteConversation(convId);
		if (currentConvId === convId) { currentConvId = null; messages = []; }
		await loadConversations();
	}

	async function archiveChat(convId: string) {
		await archiveConversation(convId);
		if (currentConvId === convId) { currentConvId = null; messages = []; }
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
		if (projects.length === 0) { alert('Create a project first.'); return; }
		const projectId = prompt('Project ID (' + projects.map(p => p.id + ': ' + p.name).join(', ') + '):');
		if (!projectId) return;
		await addConversationToProject(convId, projectId);
		await loadConversations();
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

	async function highlight(messageIndex: number) {
		if (!currentConvId) return;
		const tag = prompt('Tag this highlight (optional):') || 'highlight';
		const result = await createHighlight(currentConvId, messageIndex, messageIndex, tag);
		notebooks = [...notebooks, result];
		showNotebook = true;
	}

	async function branchFromNote(noteIndex: number) {
		const note = notebooks[noteIndex];
		if (!note || !currentConvId) return;
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

	async function doSearch() {
		if (!searchQuery.trim()) return;
		searchResults = await searchConversations(searchQuery);
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

	async function onMCPChange() {
		await loadMCPServers();
		await loadToolCount();
	}

	function doExportMarkdown() {
		if (messages.length === 0) return;
		exportMarkdown(currentTitle, messages);
	}

	function doExportJSON() {
		if (messages.length === 0) return;
		exportJSON(currentTitle, messages, {
			conversation_id: currentConvId,
			provider: selectedProvider,
		});
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
	<Sidebar
		{conversations} {currentConvId} {convTree} {projects} {selectedProjectId}
		bind:searchQuery {searchResults}
		onNewChat={newChat}
		onSelectConversation={selectConversation}
		onSearch={doSearch}
		onDeleteChat={deleteChat}
		onArchiveChat={archiveChat}
		onMoveToProject={moveToProject}
		onNewProject={newProject}
		onSelectProject={(id) => selectedProjectId = id}
	/>
	{/if}

	<main class="chat">
		<ChatHeader
			title={currentTitle}
			bind:showSidebar
			bind:selectedProvider
			{providers} {localModels} {defaultLocalModel}
			{toolCount}
			mcpServerCount={Object.keys(mcpServers).length}
			notebookCount={notebooks.length}
			hasMessages={messages.length > 0}
			{showSettings} {showProvenance} {showNotebook} {showTools} {showMCP}
			onSetProvider={setProvider}
			onSetLocalModel={setLocalModel}
			onTogglePanel={togglePanel}
			onExportMarkdown={doExportMarkdown}
			onExportJSON={doExportJSON}
		/>

		<div class="main-content">
			<MessageList
				{messages} {isStreaming} {streamingText}
				onHighlight={highlight}
				onBranch={branch}
			/>

			{#if showSettings}
			<SettingsPanel
				{providers} {localModels} {defaultLocalModel} apiBase={API_BASE}
				onClose={() => showSettings = false}
				onSetLocalModel={setLocalModel}
				onSaveApiKey={saveApiKey}
				onLoadSettings={loadSettings}
				onLoadLocalModels={loadLocalModels}
			/>
			{/if}

			{#if showMCP}
			<MCPPanel {mcpServers} apiBase={API_BASE}
				onClose={() => showMCP = false}
				onChange={onMCPChange} />
			{/if}

			{#if showTools}
			<ToolsPanel {toolsList} onClose={() => showTools = false} />
			{/if}

			{#if showProvenance}
			<ProvenancePanel {provenanceData} onClose={() => showProvenance = false} />
			{/if}

			{#if showNotebook}
			<NotebookPanel
				{notebooks} {noteComments}
				onClose={() => showNotebook = false}
				onAddComment={addNoteComment}
				onBranchFromNote={branchFromNote}
			/>
			{/if}
		</div>

		<InputArea
			bind:inputText bind:pendingImages
			{isStreaming}
			onSend={send}
			onCancel={() => abortCurrentStream()}
		/>
	</main>
</div>

<style>
	.layout { display: flex; height: 100vh; width: 100%; }
	.chat { flex: 1; display: flex; flex-direction: column; min-width: 0; }
	.main-content { flex: 1; display: flex; overflow: hidden; }
</style>
