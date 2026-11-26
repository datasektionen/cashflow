import type { Attachment } from 'svelte/attachments';

const MAX_SCALE = 8;

/** Ctrl/⌘ + wheel, pinch or double-click zooms around the cursor; drag or wheel pans while zoomed. */
export const zoomable: Attachment<HTMLElement> = (node) => {
	let scale = 1;
	let x = 0;
	let y = 0;

	function apply() {
		node.style.translate = `${x}px ${y}px`;
		node.style.scale = String(scale);
		node.style.cursor = scale > 1 ? 'grab' : 'zoom-in';
		node.style.touchAction = scale > 1 ? 'none' : '';
	}

	function zoomTo(next: number, clientX: number, clientY: number) {
		next = Math.min(MAX_SCALE, Math.max(1, next));
		const rect = node.getBoundingClientRect();
		// Untransformed centre of the element
		const cx = rect.left + rect.width / 2 - x;
		const cy = rect.top + rect.height / 2 - y;
		x = next === 1 ? 0 : clientX - cx - (next * (clientX - cx - x)) / scale;
		y = next === 1 ? 0 : clientY - cy - (next * (clientY - cy - y)) / scale;
		scale = next;
		apply();
	}

	// Ctrl/⌘ + wheel (and trackpad pinch) zooms; plain wheel pans while zoomed, otherwise scrolls the page
	function onwheel(e: WheelEvent) {
		if (e.ctrlKey || e.metaKey) {
			e.preventDefault();
			zoomTo(scale * Math.exp(-Math.max(-50, Math.min(50, e.deltaY)) * 0.01), e.clientX, e.clientY);
		} else if (scale > 1) {
			e.preventDefault();
			x -= e.deltaX;
			y -= e.deltaY;
			apply();
		}
	}

	function ondblclick(e: MouseEvent) {
		getSelection()?.removeAllRanges();
		zoomTo(scale > 1 ? 1 : 3, e.clientX, e.clientY);
	}

	function onpointerdown(e: PointerEvent) {
		if (scale === 1) return;
		e.preventDefault();
		node.setPointerCapture(e.pointerId);
		const move = (m: PointerEvent) => {
			x += m.movementX;
			y += m.movementY;
			apply();
		};
		node.addEventListener('pointermove', move);
		node.addEventListener('pointerup', () => node.removeEventListener('pointermove', move), {
			once: true
		});
	}

	node.style.userSelect = 'none';
	apply();
	node.addEventListener('wheel', onwheel, { passive: false });
	node.addEventListener('dblclick', ondblclick);
	node.addEventListener('pointerdown', onpointerdown);
	return () => {
		node.removeEventListener('wheel', onwheel);
		node.removeEventListener('dblclick', ondblclick);
		node.removeEventListener('pointerdown', onpointerdown);
	};
};
