<script lang="ts">
	import { connectMCP } from '$lib/api';

	let {
		mcpServers, apiBase, onClose, onChange,
	}: {
		mcpServers: any;
		apiBase: string;
		onClose: () => void;
		onChange: () => void | Promise<void>;
	} = $props();

	let mcpName = $state('');
	let mcpCommand = $state('');
	let mcpArgs = $state('');

	async function connectMCPServer() {
		if (!mcpName.trim() || !mcpCommand.trim()) return;
		try {
			const result = await connectMCP(mcpName.trim(), mcpCommand.trim(),
				mcpArgs.trim() ? mcpArgs.trim().split(' ') : []);
			mcpName = '';
			mcpCommand = '';
			mcpArgs = '';
			await onChange();
			alert(`Connected! ${result.tools} tools discovered: ${result.tool_names?.join(', ')}`);
		} catch (e) {
			alert(`Failed to connect: ${e}`);
		}
	}

	async function disconnectMCPServer(name: string) {
		await fetch(`${apiBase}/mcp/${name}`, { method: 'DELETE' });
		await onChange();
	}

	const presets = [
		{name: 'filesystem', cmd: 'npx', args: '@modelcontextprotocol/server-filesystem /home', desc: 'File access'},
		{name: 'github', cmd: 'npx', args: '@modelcontextprotocol/server-github', desc: 'GitHub repos & issues'},
		{name: 'sqlite', cmd: 'npx', args: '@modelcontextprotocol/server-sqlite --db-path ./data.db', desc: 'SQLite queries'},
		{name: 'memory', cmd: 'npx', args: '@modelcontextprotocol/server-memory', desc: 'Knowledge graph'},
		{name: 'brave-search', cmd: 'npx', args: '@modelcontextprotocol/server-brave-search', desc: 'Web search'},
	];
</script>

<div class="mcp-panel">
	<div class="mcp-panel-header">
		<h3>MCP Servers</h3>
		<button class="close-btn" onclick={onClose}>✕</button>
	</div>

	{#if Object.keys(mcpServers).length > 0}
	<div class="mcp-list">
		{#each Object.entries(mcpServers) as [name, server]}
		<div class="mcp-server">
			<div class="mcp-server-info">
				<span class="mcp-name">{name}</span>
				<span class="mcp-tools">{(server as any).tools} tools</span>
			</div>
			<button class="mcp-disconnect" onclick={() => disconnectMCPServer(name)}>✕</button>
		</div>
		{/each}
	</div>
	{/if}

	<div class="mcp-presets">
		<div class="mcp-presets-title">Quick Connect</div>
		{#each presets as preset}
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

<style>
	.mcp-panel { width: 300px; background: var(--bg-secondary); border-left: 1px solid var(--border); padding: 14px; overflow-y: auto; flex-shrink: 0; animation: slideInRight 0.3s ease; }
	.mcp-panel-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
	.mcp-panel-header h3 { margin: 0; font-size: 14px; color: var(--accent); font-weight: 600; flex: 1; }
	.close-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; transition: all var(--transition); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); }
	.close-btn:hover { color: var(--error); background: rgba(255,68,68,0.1); }
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
	.setting-note { font-size: 12px; color: var(--text-muted); padding: 10px; line-height: 1.5; }
	.setting-note a { color: var(--accent); }
</style>
