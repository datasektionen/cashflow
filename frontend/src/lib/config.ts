import { browser, dev } from '$app/environment';


const BACKEND_PORT = dev ? 8000 : 8001;
export const API_URL = browser ? '/api/' : `http://127.0.0.1:${BACKEND_PORT}/api/`;
