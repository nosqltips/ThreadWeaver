/**
 * API client for the StateGraph Chat backend.
 */

const API_BASE = '/api';

export interface ImageData {
	data: string;  // base64
	media_type: string;
}

export interface Message {
	role: 'user' | 'assistant';
	content: string;
	timestamp: number;
	images?: ImageData[];
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

// Abort the current in-flight stream (set by sendMessage, used for cancel)
let currentAbortController: AbortController | null = null;

export function abortCurrentStream() {
	if (currentAbortController) {
		currentAbortController.abort();
		currentAbortController = null;
	}
}

export async function sendMessage(
	convId: string,
	content: string,
	onChunk: (text: string) => void,
	provider?: string,
	images?: ImageData[],
	timeoutMs = 180000  // 3 minutes — backend has its own LLM timeout
): Promise<string> {
	const body: any = { content, provider };
	if (images && images.length > 0) {
		body.images = images;
	}

	const controller = new AbortController();
	currentAbortController = controller;

	// Idle timeout — abort if no chunk received within timeoutMs
	let idleTimer: any = null;
	const resetIdleTimer = () => {
		if (idleTimer) clearTimeout(idleTimer);
		idleTimer = setTimeout(() => controller.abort('idle-timeout'), timeoutMs);
	};
	resetIdleTimer();

	let fullResponse = '';

	try {
		const res = await fetch(`${API_BASE}/conversations/${convId}/messages`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body),
			signal: controller.signal,
		});

		const reader = res.body!.getReader();
		const decoder = new TextDecoder();

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			resetIdleTimer();

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
	} catch (e: any) {
		if (e.name === 'AbortError') {
			fullResponse += `\n\n⏱ Request cancelled or timed out (no response for ${Math.round(timeoutMs/1000)}s).`;
			onChunk(fullResponse);
		} else {
			fullResponse += `\n\n❌ Error: ${e.message || e}`;
			onChunk(fullResponse);
		}
	} finally {
		if (idleTimer) clearTimeout(idleTimer);
		currentAbortController = null;
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

export async function listTools(): Promise<any[]> {
	const res = await fetch(`${API_BASE}/tools`);
	return res.json();
}

export async function connectMCP(name: string, command: string, args: string[] = []): Promise<any> {
	const res = await fetch(`${API_BASE}/mcp/connect`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, command, args }),
	});
	return res.json();
}

export async function listMCPServers(): Promise<any> {
	const res = await fetch(`${API_BASE}/mcp/servers`);
	return res.json();
}

export async function attachFile(convId: string, path: string): Promise<any> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/file`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ path }),
	});
	return res.json();
}

// Delete / Archive
export async function deleteConversation(convId: string): Promise<any> {
	const res = await fetch(`${API_BASE}/conversations/${convId}`, { method: 'DELETE' });
	return res.json();
}

export async function archiveConversation(convId: string): Promise<any> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/archive`, { method: 'POST' });
	return res.json();
}

export async function unarchiveConversation(convId: string): Promise<any> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/unarchive`, { method: 'POST' });
	return res.json();
}

// Projects
export async function createProject(name: string, description = '', systemPrompt = ''): Promise<any> {
	const res = await fetch(`${API_BASE}/projects`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, description, system_prompt: systemPrompt }),
	});
	return res.json();
}

export async function listProjects(): Promise<any[]> {
	const res = await fetch(`${API_BASE}/projects`);
	return res.json();
}

export async function getProject(projectId: string): Promise<any> {
	const res = await fetch(`${API_BASE}/projects/${projectId}`);
	return res.json();
}

export async function addConversationToProject(convId: string, projectId: string): Promise<any> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/project`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ project_id: projectId }),
	});
	return res.json();
}

export async function getProvenance(convId: string): Promise<any[]> {
	const res = await fetch(`${API_BASE}/conversations/${convId}/provenance`);
	return res.json();
}
