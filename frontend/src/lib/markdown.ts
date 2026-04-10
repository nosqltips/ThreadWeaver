/**
 * Markdown rendering with sanitization.
 * Uses `marked` for parsing and DOMPurify for XSS protection.
 */
import { marked } from 'marked';
import DOMPurify from 'dompurify';

marked.setOptions({
	gfm: true,
	breaks: true,
});

export function renderMarkdown(text: string): string {
	if (!text) return '';
	const raw = marked.parse(text, { async: false }) as string;
	// SSR fallback: DOMPurify needs window. Return raw on the server, sanitize in browser.
	if (typeof window === 'undefined') return raw;
	return DOMPurify.sanitize(raw, {
		ADD_ATTR: ['target', 'rel'],
	});
}
