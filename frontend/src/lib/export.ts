/**
 * Conversation export — markdown and JSON.
 */
import type { Message } from './api';

function safeFilename(s: string): string {
	return (s || 'conversation')
		.replace(/[^a-z0-9-_]+/gi, '-')
		.replace(/-+/g, '-')
		.replace(/^-|-$/g, '')
		.slice(0, 60) || 'conversation';
}

function downloadBlob(content: string, filename: string, mime: string) {
	const blob = new Blob([content], { type: mime });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
}

export function exportMarkdown(title: string, messages: Message[]) {
	const lines: string[] = [];
	lines.push(`# ${title || 'Conversation'}`);
	lines.push('');
	lines.push(`*Exported from ThreadWeaver on ${new Date().toLocaleString()}*`);
	lines.push('');
	for (const msg of messages) {
		const role = msg.role === 'user' ? '👤 You' : '🤖 Assistant';
		const ts = msg.timestamp
			? new Date(msg.timestamp * 1000).toLocaleString()
			: '';
		lines.push(`## ${role}${ts ? ` — *${ts}*` : ''}`);
		lines.push('');
		if (msg.images && msg.images.length > 0) {
			for (const img of msg.images) {
				lines.push(`![attached image](data:${img.media_type || 'image/png'};base64,${img.data})`);
			}
			lines.push('');
		}
		lines.push(msg.content || '');
		lines.push('');
	}
	downloadBlob(lines.join('\n'), `${safeFilename(title)}.md`, 'text/markdown');
}

export function exportJSON(title: string, messages: Message[], extra: Record<string, unknown> = {}) {
	const payload = {
		title,
		exported_at: new Date().toISOString(),
		message_count: messages.length,
		messages,
		...extra,
	};
	downloadBlob(JSON.stringify(payload, null, 2), `${safeFilename(title)}.json`, 'application/json');
}
