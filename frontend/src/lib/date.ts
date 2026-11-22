export function formatDate(value: string | Date): string {
	return (typeof value === 'string' ? new Date(value) : value).toLocaleDateString('sv-SE');
}
