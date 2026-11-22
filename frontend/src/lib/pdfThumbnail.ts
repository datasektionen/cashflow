import type { PdfDocumentObject, PdfEngine } from '@embedpdf/models';
// Served from the installed package so it always matches the engine version
import WASM_URL from '@embedpdf/pdfium/pdfium.wasm?url';

let engine: Promise<PdfEngine> | undefined;
const byUrl = new Map<string, Promise<string | null>>();
const byFile = new WeakMap<File, Promise<string | null>>();

// One PDF engine for the whole page, started the first time a preview is needed
function getEngine() {
	engine ??= import('@embedpdf/engines/pdfium-worker-engine').then(({ createPdfiumEngine }) =>
		createPdfiumEngine(WASM_URL)
	);
	return engine;
}

async function render(open: (engine: PdfEngine) => Promise<PdfDocumentObject>) {
	try {
		const pdf = await getEngine();
		const doc = await open(pdf);
		try {
			const blob = await pdf.renderThumbnail(doc, doc.pages[0], { scaleFactor: 0.4 }).toPromise();
			return URL.createObjectURL(blob);
		} finally {
			pdf.closeDocument(doc);
		}
	} catch {
		return null;
	}
}

/** Object URL of a small image of the PDF's first page, or null if it can't be read. Cached per source. */
export function pdfThumbnail(source: string | File): Promise<string | null> {
	const id = crypto.randomUUID();
	if (typeof source === 'string') {
		let thumb = byUrl.get(source);
		if (!thumb) {
			thumb = render((pdf) => pdf.openDocumentUrl({ id, url: source }).toPromise());
			byUrl.set(source, thumb);
		}
		return thumb;
	}
	let thumb = byFile.get(source);
	if (!thumb) {
		thumb = render(async (pdf) =>
			pdf.openDocumentBuffer({ id, content: await source.arrayBuffer() }).toPromise()
		);
		byFile.set(source, thumb);
	}
	return thumb;
}

/** Frees an uploaded file's preview once it is no longer shown. */
export function releasePdfThumbnail(file: File) {
	byFile.get(file)?.then((url) => url && URL.revokeObjectURL(url));
	byFile.delete(file);
}
