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
	email: string;
	username: string;
};

export type Payment = {
	id: number;
	date: string;
	payer: Profile;
};

export type Comment = {
	date: string;
	author: Profile;
	content: string;
};

export type Expense = {
	id: number;
	description: string;
	expense_date: string;
	created_date: string;
	confirmed_at: string | null;
	confirmed_by: Profile | null;
	owner: Profile;
	reimbursement: number | null;
	payment: Payment | null;
	verification: string;
	is_flagged: boolean | null;
	parts: ExpensePart[];
	files: ExpenseFile[];
	comments: Comment[];
};

export type InvoicePart = {
	invoice?: number;
	cost_centre: string;
	secondary_cost_centre: string;
	budget_line: string;
	amount: string;
	attested_by?: number;
	attest_date?: string;
};

export type Invoice = {
	id: number;
	created_date: string;
	invoice_date: string;
	due_date: string;
	confirmed_by: number | null;
	confirmed_at: string | null;
	owner: Profile;
	description: string;
	verification: string | null;
	paid_at: string | null;
	paid_by: number | null;
	parts: InvoicePart[];
};

export interface InvoiceCreate {
	description: string;
	invoice_date: string;
	due_date: string;
	files: File[];
	parts: InvoicePart[];
	accounted?: boolean;
	verification?: string;
}

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
	attested_by: Profile | null;
	attest_date: string | null;
};

export type ClaimStatus = 'submitted' | 'paid';

export type Claim = {
	id: number;
	type: 'expense' | 'invoice';
	description: string;
	amount: string;
	status: ClaimStatus;
	date: string;
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
