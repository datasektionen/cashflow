import type { FileItem } from "#/components/form/files-field";

export type PartValues = { costCentre: string; secondaryCostCentre: string; budgetLine: string; amount: string };

/** The claim form's state. Amounts are the text typed; parseKronor turns them into öre. */
export type ClaimFormValues = {
  description: string;
  date: string;
  invoiceNumber: string;
  dueDate: string;
  parts: PartValues[];
  files: FileItem[];
};

export const emptyPart: PartValues = { costCentre: "", secondaryCostCentre: "", budgetLine: "", amount: "" };
