const fold = (value: string) =>
	value.normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase().trim();

/** Matches every query word; ranks exact, then word-prefix, then substring matches. */
export function rankOptions<T>(items: readonly T[], query: string, text: (item: T) => string): T[] {
	const needle = fold(query);
	if (!needle) return [...items];
	const tokens = needle.split(/\s+/);
	return items
		.map((item, index) => {
			const haystack = fold(text(item));
			const words = haystack.split(/[^\p{L}\p{N}]+/u);
			const rank =
				haystack === needle ? 0 : tokens.every((t) => words.some((w) => w.startsWith(t))) ? 1 : 2;
			return { item, index, haystack, rank };
		})
		.filter(({ haystack }) => tokens.every((t) => haystack.includes(t)))
		.sort((a, b) => a.rank - b.rank || a.index - b.index)
		.map(({ item }) => item);
}
