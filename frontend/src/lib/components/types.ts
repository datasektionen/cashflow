export type TableColumn<T> = {
	key: keyof T;
	header: string;
	render: (row: T) => string;
	width: string;
};
