// Served from the installed package so it always matches the engine version
import WASM_URL from '@embedpdf/pdfium/pdfium.wasm?url';

// Engines run in workers started from a blob, so the URL must be absolute
export const pdfiumWasmUrl = () => new URL(WASM_URL, location.href).href;
