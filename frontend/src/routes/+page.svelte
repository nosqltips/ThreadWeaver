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
		type Message,
		type ConversationSummary,
		type ImageData,
	} from '$lib/api';

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
	let notebooks = $state<any[]>([]);
	let convTree = $state<any>(null);

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
			}, undefined, images);
			messages = [...messages, { role: 'assistant', content: fullResponse, timestamp: Date.now() / 1000 }];
			streamingText = '';
		} catch (e) {
			messages = [...messages, { role: 'assistant', content: `Error: ${e}`, timestamp: Date.now() / 1000 }];
		}

		isStreaming = false;
		await loadConversations();
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

	$effect(() => { loadConversations(); });
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
						<span class="tree-count">{node.message_count}</span>
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

		<div class="conv-list">
			{#each conversations as conv}
			<button class="conv-item" class:active={conv.id === currentConvId}
				onclick={() => selectConversation(conv.id)}>
				<span class="conv-title">{conv.title}</span>
				<span class="conv-meta">{conv.message_count} msgs
					{#if conv.parent_id}<span class="badge">branch</span>{/if}
				</span>
			</button>
			{/each}
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
				<button class="header-btn" class:active={showNotebook} onclick={() => showNotebook = !showNotebook}>
					📓 {notebooks.length > 0 ? notebooks.length : ''}
				</button>
			</div>
		</div>

		<div class="main-content">
			<div class="messages">
				{#if messages.length === 0}
				<div class="welcome">
					<h1>ThreadWeaver</h1>
					<p>AI chat with branchable conversations.</p>
					<p>Every message is versioned. Branch from any point. Paste images.</p>
					<button onclick={newChat}>Start chatting</button>
				</div>
				{/if}

				{#each messages as msg, i}
				<div class="msg {msg.role}">
					<div class="msg-header">
						<span class="role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
						<div class="msg-actions">
							<button class="action-btn" title="Save to notebook" onclick={() => highlight(i, i)}>📓</button>
							<button class="action-btn" title="Branch from here" onclick={() => branch(i)}>⑂</button>
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

			<!-- Notebook panel -->
			{#if showNotebook}
			<div class="notebook">
				<div class="notebook-header">
					<h3>📓 Notebook</h3>
					<button class="close-btn" onclick={() => showNotebook = false}>✕</button>
				</div>
				{#if notebooks.length === 0}
				<p class="notebook-empty">No highlights yet. Click 📓 on any message to save it.</p>
				{:else}
				{#each notebooks as note, i}
				<div class="note">
					<div class="note-tag">{note.tag}</div>
					{#each note.messages as m}
					<div class="note-msg">
						<span class="note-role">{m.role}</span>: {m.content.slice(0, 100)}{m.content.length > 100 ? '...' : ''}
					</div>
					{/each}
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

	/* Sidebar */
	.sidebar { width: 260px; background: #16162a; border-right: 1px solid #2a2a4a; display: flex; flex-direction: column; flex-shrink: 0; }
	.sidebar-header { padding: 14px; border-bottom: 1px solid #2a2a4a; }
	.sidebar-header h2 { margin: 0 0 10px; font-size: 15px; color: #7b68ee; }
	.new-chat { width: 100%; padding: 8px; background: #7b68ee; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
	.new-chat:hover { background: #6a5acd; }
	.search-box { padding: 6px 14px; }
	.search-box input { width: 100%; padding: 7px; background: #1a1a35; border: 1px solid #333; border-radius: 4px; color: #e0e0e0; font-size: 13px; }
	.search-results { padding: 0 6px; max-height: 150px; overflow-y: auto; }
	.search-result { display: block; width: 100%; text-align: left; padding: 6px 8px; background: none; border: none; color: #e0e0e0; cursor: pointer; border-radius: 4px; }
	.search-result:hover { background: #1a1a35; }
	.result-title { display: block; font-size: 12px; font-weight: 600; }
	.result-preview { display: block; font-size: 11px; color: #888; }

	/* Branch tree */
	.tree-section { padding: 8px 6px; border-bottom: 1px solid #2a2a4a; }
	.tree-section h3 { margin: 0 0 6px 8px; font-size: 11px; text-transform: uppercase; color: #666; letter-spacing: 0.5px; }
	.tree-item { display: flex; align-items: center; gap: 6px; width: 100%; text-align: left; padding: 4px 8px; background: none; border: none; color: #ccc; cursor: pointer; border-radius: 4px; font-size: 12px; }
	.tree-item:hover { background: #1a1a35; }
	.tree-item.active { background: #2a2a4a; color: #7b68ee; }
	.tree-icon { font-size: 10px; color: #7b68ee; }
	.tree-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.tree-count { font-size: 10px; color: #666; }

	.conv-list { flex: 1; overflow-y: auto; padding: 6px; }
	.conv-item { display: block; width: 100%; text-align: left; padding: 8px 10px; background: none; border: none; color: #e0e0e0; cursor: pointer; border-radius: 6px; margin-bottom: 1px; }
	.conv-item:hover { background: #1a1a35; }
	.conv-item.active { background: #2a2a4a; }
	.conv-title { display: block; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.conv-meta { display: block; font-size: 11px; color: #666; }
	.badge { background: #7b68ee33; color: #7b68ee; padding: 1px 5px; border-radius: 3px; font-size: 10px; margin-left: 4px; }

	/* Chat area */
	.chat { flex: 1; display: flex; flex-direction: column; min-width: 0; }
	.chat-header { padding: 10px 14px; border-bottom: 1px solid #2a2a4a; display: flex; align-items: center; gap: 10px; }
	.chat-header h3 { margin: 0; font-size: 14px; color: #ccc; flex: 1; }
	.toggle { background: none; border: none; color: #888; cursor: pointer; padding: 4px 8px; }
	.header-actions { display: flex; gap: 4px; }
	.header-btn { background: none; border: 1px solid #333; color: #888; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px; }
	.header-btn.active { border-color: #7b68ee; color: #7b68ee; }

	.main-content { flex: 1; display: flex; overflow: hidden; }
	.messages { flex: 1; overflow-y: auto; padding: 16px; }
	.welcome { text-align: center; padding: 80px 20px; }
	.welcome h1 { color: #7b68ee; }
	.welcome p { color: #888; }
	.welcome button { margin-top: 16px; padding: 10px 24px; background: #7b68ee; color: #fff; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; }

	.msg { margin-bottom: 14px; padding: 10px 14px; border-radius: 8px; max-width: 800px; }
	.msg.user { background: #1a1a35; margin-left: auto; }
	.msg.assistant { background: #16162a; border: 1px solid #2a2a4a; }
	.msg.streaming { border-color: #7b68ee44; }
	.msg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
	.role { font-size: 11px; font-weight: 600; color: #7b68ee; text-transform: uppercase; }
	.msg-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
	.msg:hover .msg-actions { opacity: 1; }
	.action-btn { background: none; border: 1px solid #333; color: #888; font-size: 11px; padding: 2px 6px; border-radius: 4px; cursor: pointer; }
	.action-btn:hover { color: #7b68ee; border-color: #7b68ee; }
	.dot { color: #7b68ee; animation: pulse 1s infinite; }
	@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
	.msg-content { font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; }
	.msg-images { margin-bottom: 8px; }
	.attached-image { max-width: 300px; max-height: 200px; border-radius: 6px; border: 1px solid #333; }

	/* Notebook panel */
	.notebook { width: 300px; background: #16162a; border-left: 1px solid #2a2a4a; padding: 12px; overflow-y: auto; flex-shrink: 0; }
	.notebook-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
	.notebook-header h3 { margin: 0; font-size: 14px; color: #7b68ee; }
	.close-btn { background: none; border: none; color: #888; cursor: pointer; font-size: 16px; }
	.notebook-empty { color: #666; font-size: 13px; text-align: center; padding: 20px; }
	.note { background: #1a1a35; border-radius: 6px; padding: 10px; margin-bottom: 8px; border-left: 3px solid #7b68ee; }
	.note-tag { font-size: 10px; color: #7b68ee; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }
	.note-msg { font-size: 12px; color: #ccc; margin-bottom: 4px; }
	.note-role { font-weight: 600; color: #888; }

	/* Input area */
	.input-area { padding: 14px; border-top: 1px solid #2a2a4a; }
	.image-preview { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
	.preview-thumb { position: relative; }
	.preview-thumb img { width: 60px; height: 60px; object-fit: cover; border-radius: 6px; border: 1px solid #333; }
	.remove-img { position: absolute; top: -4px; right: -4px; background: #ff4444; color: #fff; border: none; border-radius: 50%; width: 16px; height: 16px; font-size: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
	.input-row { display: flex; gap: 8px; }
	.input-row textarea { flex: 1; padding: 10px; background: #1a1a35; border: 1px solid #333; border-radius: 8px; color: #e0e0e0; font-size: 14px; font-family: inherit; resize: none; }
	.input-row textarea:focus { outline: none; border-color: #7b68ee; }
	.send { padding: 10px 18px; background: #7b68ee; color: #fff; border: none; border-radius: 8px; cursor: pointer; align-self: flex-end; }
	.send:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
