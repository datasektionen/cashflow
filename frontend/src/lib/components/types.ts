export type TableColumn<T> = {
	key: keyof T;
	header: string;
	render: (row: T) => string;
	width: string;
};

export type TableRowProps<T> = {
	onClick?: (row: T) => void;
	class?: string | ((row: T) => string);
};
