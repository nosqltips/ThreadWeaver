<script lang="ts">
	import {
		createConversation,
		listConversations,
		getConversation,
		sendMessage,
		branchConversation,
		searchConversations,
		type Message,
		type ConversationSummary,
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
	}

	async function send() {
		if (!inputText.trim() || isStreaming) return;
		if (!currentConvId) await newChat();

		const userMessage = inputText.trim();
		inputText = '';
		messages = [...messages, { role: 'user', content: userMessage, timestamp: Date.now() / 1000 }];

		isStreaming = true;
		streamingText = '';

		try {
			const fullResponse = await sendMessage(currentConvId!, userMessage, (partial) => {
				streamingText = partial;
			});
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

	async function doSearch() {
		if (!searchQuery.trim()) return;
		searchResults = await searchConversations(searchQuery);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
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
		</div>

		<div class="messages">
			{#if messages.length === 0}
			<div class="welcome">
				<h1>ThreadWeaver</h1>
				<p>AI chat with branchable conversations.</p>
				<p>Every message is versioned. Branch from any point.</p>
				<button onclick={newChat}>Start chatting</button>
			</div>
			{/if}

			{#each messages as msg, i}
			<div class="msg {msg.role}">
				<div class="msg-header">
					<span class="role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
					<button class="branch-btn" onclick={() => branch(i)}>⑂ Branch</button>
				</div>
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

		<div class="input-area">
			<textarea placeholder="Type a message... (Enter to send)" bind:value={inputText}
				onkeydown={handleKeydown} disabled={isStreaming} rows="3"></textarea>
			<button class="send" onclick={send} disabled={isStreaming || !inputText.trim()}>
				{isStreaming ? '...' : 'Send'}
			</button>
		</div>
	</main>
</div>

<style>
	.layout { display: flex; height: 100vh; width: 100%; }

	.sidebar { width: 260px; background: #16162a; border-right: 1px solid #2a2a4a; display: flex; flex-direction: column; flex-shrink: 0; }
	.sidebar-header { padding: 14px; border-bottom: 1px solid #2a2a4a; }
	.sidebar-header h2 { margin: 0 0 10px; font-size: 15px; color: #7b68ee; }
	.new-chat { width: 100%; padding: 8px; background: #7b68ee; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
	.new-chat:hover { background: #6a5acd; }
	.search-box { padding: 6px 14px; }
	.search-box input { width: 100%; padding: 7px; background: #1a1a35; border: 1px solid #333; border-radius: 4px; color: #e0e0e0; font-size: 13px; }
	.search-results { padding: 0 6px; max-height: 180px; overflow-y: auto; }
	.search-result { display: block; width: 100%; text-align: left; padding: 6px 8px; background: none; border: none; color: #e0e0e0; cursor: pointer; border-radius: 4px; }
	.search-result:hover { background: #1a1a35; }
	.result-title { display: block; font-size: 12px; font-weight: 600; }
	.result-preview { display: block; font-size: 11px; color: #888; }
	.conv-list { flex: 1; overflow-y: auto; padding: 6px; }
	.conv-item { display: block; width: 100%; text-align: left; padding: 8px 10px; background: none; border: none; color: #e0e0e0; cursor: pointer; border-radius: 6px; margin-bottom: 1px; }
	.conv-item:hover { background: #1a1a35; }
	.conv-item.active { background: #2a2a4a; }
	.conv-title { display: block; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.conv-meta { display: block; font-size: 11px; color: #666; }
	.badge { background: #7b68ee33; color: #7b68ee; padding: 1px 5px; border-radius: 3px; font-size: 10px; margin-left: 4px; }

	.chat { flex: 1; display: flex; flex-direction: column; min-width: 0; }
	.chat-header { padding: 10px 14px; border-bottom: 1px solid #2a2a4a; display: flex; align-items: center; gap: 10px; }
	.chat-header h3 { margin: 0; font-size: 14px; color: #ccc; }
	.toggle { background: none; border: none; color: #888; cursor: pointer; padding: 4px 8px; }

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
	.branch-btn { background: none; border: 1px solid #333; color: #888; font-size: 11px; padding: 2px 6px; border-radius: 4px; cursor: pointer; opacity: 0; transition: opacity 0.2s; }
	.msg:hover .branch-btn { opacity: 1; }
	.branch-btn:hover { color: #7b68ee; border-color: #7b68ee; }
	.dot { color: #7b68ee; animation: pulse 1s infinite; }
	@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
	.msg-content { font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; }

	.input-area { padding: 14px; border-top: 1px solid #2a2a4a; display: flex; gap: 8px; }
	.input-area textarea { flex: 1; padding: 10px; background: #1a1a35; border: 1px solid #333; border-radius: 8px; color: #e0e0e0; font-size: 14px; font-family: inherit; resize: none; }
	.input-area textarea:focus { outline: none; border-color: #7b68ee; }
	.send { padding: 10px 18px; background: #7b68ee; color: #fff; border: none; border-radius: 8px; cursor: pointer; align-self: flex-end; }
	.send:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
