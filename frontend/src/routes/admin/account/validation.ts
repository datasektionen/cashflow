import { create, enforce, only, test } from 'vest';

export type VoucherFormData = {
	description: string;
};

export enum VoucherFormField {
	Description = 'description'
}

export enum ValidationError {
	BlankDescription = 'blank_description',
	DescriptionContainsEmoji = 'description_contains_emoji'
}

const EMOJI_PATTERN = /[\p{Extended_Pictographic}\p{Regional_Indicator}]/u;

// A field only gets a key once it has failed, hence Partial.
export type VoucherNumberErrors = Partial<Record<VoucherFormField, ValidationError[]>>;

export const voucherValidation = create((data: VoucherFormData, currentField?: string) => {
	only(currentField);

	test(VoucherFormField.Description, ValidationError.BlankDescription, () => {
		enforce(data.description).isNotBlank();
	});

	test(VoucherFormField.Description, ValidationError.DescriptionContainsEmoji, () => {
		enforce(data.description).notMatches(EMOJI_PATTERN);
	});
});
