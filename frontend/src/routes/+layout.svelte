<script lang="ts">
	let { children } = $props();

	// Load saved colors
	if (typeof localStorage !== 'undefined' && typeof document !== 'undefined') {
		const savedAccent = localStorage.getItem('tw-accent');
		if (savedAccent) {
			document.documentElement.style.setProperty('--accent', savedAccent);
			document.documentElement.style.setProperty('--accent-glow', savedAccent + '33');
			document.documentElement.style.setProperty('--accent-subtle', savedAccent + '18');
		}
		const savedBg = localStorage.getItem('tw-bg');
		if (savedBg) {
			document.documentElement.style.setProperty('--bg-primary', savedBg);
			// Derive secondary/tertiary
			const num = parseInt(savedBg.replace('#', ''), 16);
			const lighten = (n: number, amt: number) => {
				const r = Math.min(255, (n >> 16) + amt);
				const g = Math.min(255, ((n >> 8) & 0xFF) + amt);
				const b = Math.min(255, (n & 0xFF) + amt);
				return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`;
			};
			document.documentElement.style.setProperty('--bg-secondary', lighten(num, 8));
			document.documentElement.style.setProperty('--bg-tertiary', lighten(num, 12));
			document.documentElement.style.setProperty('--bg-hover', lighten(num, 16));
		}
	}
</script>

<svelte:head>
	<title>ThreadWeaver</title>
	<meta name="description" content="AI chat with branchable conversations" />
</svelte:head>

<div class="app">
	{@render children()}
</div>

<style>
	:root {
		--accent: #7b68ee;
		--accent-glow: #7b68ee33;
		--accent-subtle: #7b68ee18;
		--bg-primary: #0f0f1a;
		--bg-secondary: #16162a;
		--bg-tertiary: #1a1a35;
		--bg-hover: #1e1e3a;
		--border: #2a2a4a;
		--text-primary: #e0e0e0;
		--text-secondary: #999;
		--text-muted: #666;
		--success: #00ff88;
		--error: #ff4444;
		--radius: 8px;
		--radius-sm: 4px;
		--radius-lg: 12px;
		--transition: 0.2s ease;
		--transition-slow: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	:global(body) {
		margin: 0;
		padding: 0;
		font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
		background: var(--bg-primary);
		color: var(--text-primary);
		-webkit-font-smoothing: antialiased;
	}

	:global(*) {
		box-sizing: border-box;
	}

	:global(::selection) {
		background: var(--accent);
		color: #fff;
	}

	:global(::-webkit-scrollbar) {
		width: 6px;
	}
	:global(::-webkit-scrollbar-track) {
		background: transparent;
	}
	:global(::-webkit-scrollbar-thumb) {
		background: var(--border);
		border-radius: 3px;
	}
	:global(::-webkit-scrollbar-thumb:hover) {
		background: var(--text-muted);
	}

	/* Global animations */
	@keyframes -global-fadeIn {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: translateY(0); }
	}

	@keyframes -global-slideInLeft {
		from { opacity: 0; transform: translateX(-12px); }
		to { opacity: 1; transform: translateX(0); }
	}

	@keyframes -global-slideInRight {
		from { opacity: 0; transform: translateX(12px); }
		to { opacity: 1; transform: translateX(0); }
	}

	@keyframes -global-pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}

	@keyframes -global-shimmer {
		0% { background-position: -200% center; }
		100% { background-position: 200% center; }
	}

	@keyframes -global-scaleIn {
		from { opacity: 0; transform: scale(0.95); }
		to { opacity: 1; transform: scale(1); }
	}

	.app {
		height: 100vh;
		display: flex;
	}
</style>
