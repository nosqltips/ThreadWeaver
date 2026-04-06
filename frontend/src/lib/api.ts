/**
 * API client for the StateGraph Chat backend.
 */

const API_BASE = 'http://localhost:8000/api';

export interface Message {
	role: 'user' | 'assistant';
	content: string;
	timestamp: number;
}

export interface Conversation {
	id: string;
	title: string;
	branch: string;
	messages: Message[];
	parent_id: string | null;
	parent_message_index: number | null;
	tags: string[];
}

export interface ConversationSummary {
	id: string;
	title: string;
	message_count: number;
	parent_id: string | null;
	created_at: number;
}

export async function createConversation(title = 'New Chat'): Promise<{ id: string }> {
	const res = await fetch(`${API_BASE}/conversations`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ title }),
	});
	return res.json();
}

export async function listConversations(): Promise<ConversationSummary[]> {
	const res = await fetch(`${API_BASE}/conversations`);
	return res.json();
}

export async function getConversation(id: string): Promise<Conversation> {
	const res = await fetch(`${API_BASE}/conversations/${id}`);
	return res.json();
}

export async function getConversationTree(id: string): Promise<any> {
	const res = await fetch(`${API_BASE}/conversations/${id}/tree`);
	return res.json();
}

export async function sendMessage(
	convId: string,
	content: string,
	onChunk: (text: string) => void,
	provider?: string
): Promise<string> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/messages`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ content, provider }),
	});

	const reader = res.body!.getReader();
	const decoder = new TextDecoder();
	let fullResponse = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		const text = decoder.decode(value);
		const lines = text.split('\n');

		for (const line of lines) {
			if (line.startsWith('data: ')) {
				try {
					const data = JSON.parse(line.slice(6));
					if (data.type === 'chunk') {
						fullResponse += data.content;
						onChunk(fullResponse);
					} else if (data.type === 'done') {
						fullResponse = data.content;
					}
				} catch {}
			}
		}
	}

	return fullResponse;
}

export async function branchConversation(
	convId: string,
	atMessage: number,
	title?: string
): Promise<{ id: string }> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/branch`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ at_message: atMessage, title }),
	});
	return res.json();
}

export async function searchConversations(query: string): Promise<any[]> {
	const res = await fetch(`${API_BASE}/search`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ query }),
	});
	return res.json();
}

export async function createHighlight(
	convId: string,
	startIndex: number,
	endIndex: number,
	tag?: string
): Promise<any> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/highlights`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ start_index: startIndex, end_index: endIndex, tag }),
	});
	return res.json();
}

export async function getSettings(): Promise<any> {
	const res = await fetch(`${API_BASE}/settings`);
	return res.json();
}
