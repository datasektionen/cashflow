export type ExpenseFile = {
	id: number;
	file: string;
	expense: number | null;
	invoice: number | null;
};

export type Profile = {
	id: number;
	first_name: string;
	last_name: string;
};

export type Expense = {
	id: number;
	description: string;
	expense_date: string;
	created_date: string;
	confirmed_at: string | null;
	confirmed_by: number | null;
	owner: Profile;
	reimbursement: number | null;
	verification: string;
	is_flagged: boolean | null;
	parts: ExpensePart[];
	files: ExpenseFile[];
};

export interface ExpenseCreate {
	description: string;
	expense_date: string;
	parts: ExpensePart[];
	files: File[];
}

export type ExpensePart = {
	id?: number;
	cost_centre: string;
	secondary_cost_centre: string;
	budget_line: string;
	amount: string;
};

export type PaginatedResponse<T> = {
	data: T[];
	pagination: {
		total: number;
		page: number;
		perPage: number;
		totalPages: number;
	};
};

export type Permissions = {
	attest: string[];
	accounting: string[];
	pay: boolean;
	confirm: boolean;
	unconfirm: boolean;
	unattest: boolean;
	'edit-invoice': boolean;
	'view-all-payments': boolean;
};

export type User = {
	username: string;
	first_name: string;
	last_name: string;
	email: string;
	permissions: Permissions;
};
