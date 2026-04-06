<script lang="ts">
	let { children } = $props();
</script>

<svelte:head>
	<title>ThreadWeaver</title>
	<meta name="description" content="AI chat with branchable conversations" />
</svelte:head>

<div class="app">
	{@render children()}
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: system-ui, -apple-system, sans-serif;
		background: #0f0f1a;
		color: #e0e0e0;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.app {
		height: 100vh;
		display: flex;
	}
</style>
