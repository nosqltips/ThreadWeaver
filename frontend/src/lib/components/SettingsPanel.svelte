<script lang="ts">
	let {
		providers, localModels, defaultLocalModel, apiBase,
		onClose, onSetLocalModel, onSaveApiKey, onLoadSettings, onLoadLocalModels,
	}: {
		providers: any;
		localModels: any[];
		defaultLocalModel: string;
		apiBase: string;
		onClose: () => void;
		onSetLocalModel: (m: string) => void | Promise<void>;
		onSaveApiKey: (provider: string, key: string) => void | Promise<void>;
		onLoadSettings: () => void | Promise<void>;
		onLoadLocalModels: () => void | Promise<void>;
	} = $props();

	function setBackgroundColor(color: string) {
		document.documentElement.style.setProperty('--bg-primary', color);
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
</script>

<div class="settings-panel">
	<div class="settings-header">
		<h3>⚙ Settings</h3>
		<span class="version-badge">v0.3.0-beta</span>
		<button class="close-btn" onclick={onClose}>✕</button>
	</div>

	{#each Object.entries(providers) as [name, p]}
	<div class="setting-group">
		<div class="setting-label">{(p as any).label || name}</div>
		{#if name !== 'local'}
		<div class="setting-row">
			<input type="password" placeholder="API Key"
				value={(p as any).api_key_set ? '••••••••' : ''}
				onchange={(e) => onSaveApiKey(name, e.currentTarget.value)} />
			{#if (p as any).api_key_set}<span class="key-ok">✓</span>{/if}
		</div>
		{/if}
		<div class="setting-row">
			{#if name === 'local' && localModels.length > 0}
			<select onchange={(e) => onSetLocalModel(e.currentTarget.value)}>
				{#each localModels as m}
				<option value={m.name} selected={m.name === ((p as any).model || defaultLocalModel)}>{m.name}</option>
				{/each}
			</select>
			<button class="refresh-btn" onclick={() => onLoadLocalModels()}>↻</button>
			{:else}
			<input type="text" placeholder="Model" value={(p as any).model || ''}
				onchange={(e) => fetch(`${apiBase}/settings/provider/${name}`, {
					method: 'PUT', headers: {'Content-Type': 'application/json'},
					body: JSON.stringify({model: e.currentTarget.value})
				}).then(() => onLoadSettings())} />
			{/if}
		</div>
		{#if (p as any).base_url}
		<div class="setting-row">
			<input type="text" placeholder="Base URL" value={(p as any).base_url}
				onchange={(e) => fetch(`${apiBase}/settings/provider/${name}`, {
					method: 'PUT', headers: {'Content-Type': 'application/json'},
					body: JSON.stringify({base_url: e.currentTarget.value})
				}).then(() => onLoadSettings())} />
		</div>
		{/if}
	</div>
	{/each}

	{#if localModels.length === 0}
	<div class="setting-note">
		No local models found. Install <a href="https://ollama.com" target="_blank">Ollama</a> and run <code>ollama pull llama3</code>
	</div>
	{/if}

	<div class="setting-group">
		<div class="setting-label">Accent Color</div>
		<div class="color-picker-row">
			{#each ['#7b68ee', '#6366f1', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#8b5cf6', '#14b8a6'] as color}
			<button class="color-swatch"
				style="background: {color}"
				onclick={() => {
					document.documentElement.style.setProperty('--accent', color);
					document.documentElement.style.setProperty('--accent-glow', color + '33');
					document.documentElement.style.setProperty('--accent-subtle', color + '18');
					localStorage.setItem('tw-accent', color);
				}}
				aria-label="Set accent color"
			></button>
			{/each}
		</div>
	</div>

	<div class="setting-group">
		<div class="setting-label">Background</div>
		<div class="color-picker-row">
			{#each ['#0f0f1a', '#0d1117', '#1a1a2e', '#0f172a', '#18181b', '#1c1917', '#0c0a09', '#0a0a0a', '#111827', '#0e1629'] as color}
			<button class="color-swatch bg-swatch"
				style="background: {color}; border: 2px solid #333"
				onclick={() => setBackgroundColor(color)}
				aria-label="Set background color"
			></button>
			{/each}
		</div>
	</div>
</div>

<style>
	.settings-panel { width: 300px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.settings-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; gap: 8px; }
	.settings-header h3 { flex: 1; margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; }
	.version-badge { font-size: 9px; color: var(--accent); background: var(--accent-subtle); border: 1px solid var(--accent); padding: 2px 6px; border-radius: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
	.close-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; transition: all var(--transition); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); }
	.close-btn:hover { color: var(--error); background: rgba(255,68,68,0.1); }
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
	.color-picker-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
	.color-swatch { width: 28px; height: 28px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; transition: all var(--transition); }
	.color-swatch:hover { transform: scale(1.2); }
</style>
