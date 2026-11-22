const normalizePath = (path: string) => path.replace(/\/+$/, '') || '/';

/** Whether `to` is the current page or one of its ancestors ('/' only matches itself). */
export function isActivePath(to: string, pathname: string) {
	const target = normalizePath(to);
	const current = normalizePath(pathname);
	if (target === '/') return current === '/';
	return current === target || current.startsWith(target + '/');
}
