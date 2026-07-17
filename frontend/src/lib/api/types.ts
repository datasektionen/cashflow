export type ExpenseFile = {
	id: number;
	file: string;
	expense: number | null;
	invoice: number | null;
};

export type Profile = {
	id?: number;
	first_name: string;
	last_name: string;
	email: string;
	username: string;
	// Whether the user has registered bank account and clearing number.
	// Optional because User objects are passed as Profile in a few places.
	has_bank_info?: boolean;
};

export type Payment = {
	id: number;
	date: string;
	payer: Profile;
	receiver: Profile;
	tag: string;
};

export type PaymentInitiationFile = {
	id: number;
	msg_id: string;
	file: string;
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
	// Fortnox voucher (verification) number; null if not yet accounted.
	voucher: string | null;
	is_flagged: boolean | null;
	parts: ExpensePart[];
	files: ExpenseFile[];
	comments: Comment[];
	// Fortnox account to credit on the balancing voucher row.
	// null in list responses; populated on single-claim reads.
	recommended_credit_account: number | null;
};

export type InvoicePart = {
	id: number;
	invoice?: number;
	cost_centre: string;
	secondary_cost_centre: string;
	budget_line: string;
	amount: string;
	attested_by: Profile | null;
	attest_date: string | null;
	// Voucher suggestions derived from GOrdian + Fortnox.
	// null in list responses; populated on single-claim reads.
	recommended_accounts: number[] | null;
	recommended_cost_centre: string | null;
};

export type Invoice = {
	id: number;
	created_date: string;
	invoice_date: string;
	due_date: string;
	confirmed_by: Profile | null;
	confirmed_at: string | null;
	owner: Profile;
	description: string;
	voucher: string | null;
	paid_by: Profile | null;
	paid_at: string | null;
	parts: InvoicePart[];
	comments: Comment[];
	files: ExpenseFile[];
	// Fortnox account to credit on the balancing voucher row.
	// null in list responses; populated on single-claim reads.
	recommended_credit_account: number | null;
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

export type PartUpdate = {
	cost_centre: string;
	secondary_cost_centre: string;
	budget_line: string;
	amount: string;
};

export interface ExpenseUpdate {
	description?: string;
	expense_date?: string;
	files?: File[];
	parts?: PartUpdate[];
}

export interface InvoiceUpdate {
	description?: string;
	invoice_date?: string;
	due_date?: string;
	files?: File[];
	parts?: PartUpdate[];
}

export type ExpensePart = {
	id: number;
	cost_centre: string;
	secondary_cost_centre: string;
	budget_line: string;
	amount: string;
	attested_by: Profile | null;
	attest_date: string | null;
	// Voucher suggestions derived from GOrdian + Fortnox.
	// null in list responses; populated on single-claim reads.
	recommended_accounts: number[] | null;
	recommended_cost_centre: string | null;
};

type ClaimBase = {
	id: number;
	description: string;
	amount: string;
	created_date: string;
	is_attested: boolean;
	is_confirmed: boolean;
	is_paid: boolean;
	owner: Profile;
	// Fortnox voucher (verification) number; null if not yet accounted.
	voucher: string | null;
};

export type Claim =
	| (ClaimBase & { type: 'expense'; parts: ExpensePart[] })
	| (ClaimBase & { type: 'invoice'; parts: InvoicePart[] });

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
	'manage-fortnox': boolean;
	delete: boolean;
};

export type FortnoxStatus = {
	is_connected: boolean;
	authenticated_by: string | null;
	expires_at: string | null;
};

export type FortnoxAccount = {
	number: number;
	description: string;
};

export type FortnoxCostCentre = {
	code: string;
	description: string;
};

export type CostCentre = {
	id: number | null;
	name: string;
	type: 'committee' | 'partition' | 'project' | 'other' | null;
	active: boolean;
};

export type SecondaryCostCentre = {
	id: number | null;
	name: string;
	cost_centre_id: number | null;
	active: boolean;
};

export type BudgetLine = {
	id: number | null;
	name: string;
	secondary_cost_centre_id: number | null;
	accounts: number[] | null;
	income: number | null;
	expense: number | null;
	comment: string | null;
	active: boolean;
};

export type BankInfo = {
	bank_account: string;
	sorting_number: string;
	bank_name: string;
};

export type User = {
	username: string;
	first_name: string;
	last_name: string;
	email: string;
	permissions: Permissions;
	bank_info: BankInfo;
};

export type ActionSummary = {
	expenses: {
		attestable: number;
		confirmable: number;
		accountable: number;
		payable: number;
	};
	invoices: {
		attestable: number;
		accountable: number;
		payable: number;
	};
};

export type TristateFilter = 'true' | 'false' | 'none';

export type ClaimFilter = {
	type?: 'expense' | 'invoice';
	user?: string;
	cost_centre?: string;
	secondary_cost_centre?: string;
	budget_line?: string;
	attested?: TristateFilter;
	confirmed?: TristateFilter;
	paid?: TristateFilter;
	accounted?: TristateFilter;
	flagged?: TristateFilter;
	attestable?: boolean;
	confirmable?: boolean;
	accountable?: boolean;
	payable?: boolean;
	voucher_series?: string;
	q?: string;
};

export type DescriptionSearch = {
	description?: string;
	description_fuzzy?: string;
};

export type PendingPayment = {
	owner: Profile;
	// Full details are only exposed on the pay-gated pending endpoint.
	bank_info: BankInfo;
	total: string;
	count: number;
};

export type VoucherRow = {
	account: number;
	cost_centre?: string;
	credit?: number;
	debit?: number;
	description?: string;
	project?: string;
	quantity?: number;
	removed?: boolean;
	transaction_information?: string;
};

// Pass either voucher_rows (create a voucher via Fortnox) or voucher_number
// (record an existing voucher manually).
export type AccountPayload = {
	voucher_rows?: VoucherRow[];
	voucher_number?: string;
};

export type VoucherSeries = {
	code: string;
	description?: string;
};
