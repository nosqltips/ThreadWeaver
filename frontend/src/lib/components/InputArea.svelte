<script lang="ts">
	import type { ImageData } from '$lib/api';

	let {
		inputText = $bindable(), pendingImages = $bindable(),
		isStreaming, onSend, onCancel,
	}: {
		inputText: string;
		pendingImages: ImageData[];
		isStreaming: boolean;
		onSend: () => void | Promise<void>;
		onCancel: () => void;
	} = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend(); }
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
</script>

<div class="input-area" role="region" aria-label="Message input"
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
		{#if isStreaming}
		<button class="send cancel" onclick={onCancel}>Stop</button>
		{:else}
		<button class="send" onclick={onSend} disabled={!inputText.trim() && pendingImages.length === 0}>Send</button>
		{/if}
	</div>
</div>

<style>
	.input-area { padding: 14px; border-top: 1px solid var(--border); background: var(--bg-secondary); }
	.image-preview { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; animation: fadeIn 0.2s ease; }
	.preview-thumb { position: relative; animation: scaleIn 0.2s ease; }
	.preview-thumb img { width: 60px; height: 60px; object-fit: cover; border-radius: var(--radius); border: 1px solid var(--border); transition: all var(--transition); }
	.preview-thumb img:hover { border-color: var(--accent); }
	.remove-img { position: absolute; top: -4px; right: -4px; background: var(--error); color: #fff; border: none; border-radius: 50%; width: 18px; height: 18px; font-size: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: transform var(--transition); }
	.remove-img:hover { transform: scale(1.2); }
	.input-row { display: flex; gap: 8px; }
	.input-row textarea { flex: 1; padding: 11px 14px; background: var(--bg-tertiary); border: 1px solid transparent; border-radius: var(--radius); color: var(--text-primary); font-size: 14px; font-family: inherit; resize: none; transition: all var(--transition); }
	.input-row textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
	.send { padding: 11px 20px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius); cursor: pointer; align-self: flex-end; font-weight: 500; transition: all var(--transition); }
	.send:hover:not(:disabled) { filter: brightness(1.15); transform: translateY(-1px); box-shadow: 0 4px 12px var(--accent-glow); }
	.send:active:not(:disabled) { transform: translateY(0); }
	.send:disabled { opacity: 0.4; cursor: not-allowed; }
	.send.cancel { background: var(--error); }
	.send.cancel:hover { background: #ff6666; }
</style>
