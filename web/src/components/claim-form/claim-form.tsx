import { createConnectQueryKey, useMutation, useTransport } from "@connectrpc/connect-query";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate, useRouter } from "@tanstack/react-router";
import { Info } from "lucide-react";
import { toast } from "sonner";
import { isPending } from "#/components/form/files-field";
import { useAppForm } from "#/components/form/form";
import { applyServerErrors } from "#/components/form/server-errors";
import { Button } from "#/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "#/components/ui/card";
import { FieldGroup } from "#/components/ui/field";
import { type Claim, ClaimKind, ClaimService } from "#/gen/cashflow/claim/v1/claim_pb";
import { createClaim, getClaim, updateClaim } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { claimLink } from "#/lib/claims";
import { type Locale, type Messages, useLocale, useT } from "#/lib/i18n";
import { oreToInput, parseKronor } from "#/lib/money";
import { PartsSection } from "./parts-section";
import { type ClaimFormValues, emptyPart } from "./values";

const todayIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

function initialValues(kind: ClaimKind, claim: Claim | undefined, locale: Locale): ClaimFormValues {
  if (!claim?.summary) {
    return {
      description: "",
      date: kind === ClaimKind.EXPENSE ? todayIso() : "",
      invoiceNumber: "",
      dueDate: "",
      parts: [{ ...emptyPart }],
      files: [],
    };
  }
  return {
    description: claim.summary.description,
    date: claim.summary.date,
    invoiceNumber: claim.invoiceNumber,
    dueDate: claim.dueDate,
    parts: claim.parts.map((p) => ({
      costCentre: p.costCentre,
      secondaryCostCentre: p.secondaryCostCentre,
      budgetLine: p.budgetLine,
      amount: oreToInput(p.amountOre, locale),
    })),
    files: claim.files.map((f) => ({
      key: `existing-${f.id}`,
      name: f.name,
      contentType: f.contentType,
      previewUrl: f.url,
      status: "done",
      progress: 1,
      existingId: f.id,
    })),
  };
}

/**
 * What only the browser can know: uploads still running, and amounts that
 * don't parse. Everything else, such as required fields and "at least one
 * receipt", is the server's to judge, so all problems show at once.
 */
function validateLocally(values: ClaimFormValues, t: Messages) {
  const fields: Record<string, string> = {};
  values.parts.forEach((part, i) => {
    if (part.amount.trim() && parseKronor(part.amount) === undefined)
      fields[`parts[${i}].amount`] = t.validation["amount.invalid"] ?? "";
  });
  if (values.files.some(isPending)) fields.files = t.claimForm.waitForUploads;
  return Object.keys(fields).length ? { fields } : undefined;
}

/**
 * Create or edit an expense or invoice. The receipt comes first on phones,
 * where people start by taking a photo, and sits beside the form on large
 * screens. The server validates everything again and its errors land on the
 * fields they concern.
 */
export function ClaimForm({ kind, claim }: { kind: ClaimKind; claim?: Claim }) {
  const t = useT();
  const locale = useLocale();
  const navigate = useNavigate();
  const router = useRouter();
  const queryClient = useQueryClient();
  const transport = useTransport();
  const create = useMutation(createClaim);
  const update = useMutation(updateClaim);
  const isExpense = kind === ClaimKind.EXPENSE;
  const editing = Boolean(claim?.summary);
  const f = t.claimForm;

  const form = useAppForm({
    defaultValues: initialValues(kind, claim, locale),
    validators: { onSubmit: ({ value }) => validateLocally(value, t) },
    onSubmit: async ({ value, formApi }) => {
      const input = {
        description: value.description,
        date: value.date,
        invoiceNumber: value.invoiceNumber,
        dueDate: value.dueDate,
        parts: value.parts.map((p) => ({
          costCentre: p.costCentre,
          secondaryCostCentre: p.secondaryCostCentre,
          budgetLine: p.budgetLine,
          amountOre: parseKronor(p.amount) ?? 0n,
        })),
      };
      const uploadIds = value.files.flatMap((file) => (file.uploadId ? [file.uploadId] : []));
      try {
        let saved: Claim | undefined;
        if (claim?.summary) {
          const kept = new Set(value.files.map((file) => file.existingId));
          const removeFileIds = claim.files.filter((file) => !kept.has(file.id)).map((file) => file.id);
          saved = (
            await update.mutateAsync({
              ref: { kind, number: claim.summary.number },
              claim: input,
              uploadIds,
              removeFileIds,
            })
          ).claim;
        } else {
          saved = (await create.mutateAsync({ kind, claim: input, uploadIds })).claim;
        }
        if (!saved?.summary) return;
        const { number } = saved.summary;
        queryClient.setQueryData(
          createConnectQueryKey({ schema: getClaim, input: { kind, number }, transport, cardinality: "finite" }),
          { $typeName: "cashflow.claim.v1.GetClaimResponse", claim: saved },
        );
        void queryClient.invalidateQueries({
          queryKey: createConnectQueryKey({ schema: ClaimService, transport, cardinality: undefined }),
        });
        toast.success(editing ? f.saved : f.created);
        void navigate({ ...claimLink(kind, number), replace: editing });
      } catch (error) {
        // The server's "parts[0].amount_ore" is the form's "parts[0].amount".
        const shown = applyServerErrors(formApi, error, t, (field) => field.replace(/\.amountOre$/, ".amount"));
        if (!shown) toast.error(t.errors.generic);
      }
    },
  });

  const title = editing ? (isExpense ? f.editExpense : f.editInvoice) : isExpense ? f.newExpense : f.newInvoice;

  return (
    <main className="mx-auto w-full max-w-6xl p-6 md:p-10">
      <h1 className="font-display font-semibold text-3xl tracking-tight md:text-4xl">{title}</h1>
      <p className="mt-1 text-muted-foreground">{isExpense ? f.expenseIntro : f.invoiceIntro}</p>

      <form
        noValidate
        className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]"
        onSubmit={(event) => {
          event.preventDefault();
          void form.handleSubmit();
        }}
      >
        {/* Files first on phones; beside the form on large screens. */}
        <Card className="lg:sticky lg:top-6 lg:col-start-2 lg:row-span-2 lg:row-start-1">
          <CardContent>
            <form.AppField name="files">
              {(field) => <field.FilesField label={isExpense ? f.files : f.filesInvoice} description={f.filesHint} />}
            </form.AppField>
          </CardContent>
        </Card>

        <div className="flex flex-col gap-6 lg:col-start-1 lg:row-start-1">
          <Card>
            <CardContent>
              <FieldGroup>
                <form.AppField name="description">
                  {(field) => (
                    <field.TextField label={f.description} description={f.descriptionHint} autoFocus={!editing} />
                  )}
                </form.AppField>
                {isExpense ? (
                  <form.AppField name="date">
                    {(field) => (
                      <field.TextField
                        type="date"
                        label={f.expenseDate}
                        description={f.expenseDateHint}
                        max={todayIso()}
                        className="w-48"
                      />
                    )}
                  </form.AppField>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-3">
                    <form.AppField name="invoiceNumber">
                      {(field) => <field.TextField label={f.invoiceNumber} />}
                    </form.AppField>
                    <form.AppField name="date">
                      {(field) => <field.TextField type="date" label={`${f.invoiceDate} (${f.optional})`} />}
                    </form.AppField>
                    <form.AppField name="dueDate">
                      {(field) => <field.TextField type="date" label={`${f.dueDate} (${f.optional})`} />}
                    </form.AppField>
                  </div>
                )}
              </FieldGroup>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{f.parts}</CardTitle>
              <CardDescription>{f.partsHint}</CardDescription>
            </CardHeader>
            <CardContent>
              <PartsSection form={form} exclude={claim?.summary ? { kind, number: claim.summary.number } : undefined} />
            </CardContent>
          </Card>

          {editing && isExpense && (
            <p className="flex items-center gap-2 text-muted-foreground text-sm">
              <Info className="size-4 shrink-0" /> {f.resetsConfirmation}
            </p>
          )}

          <div className="flex flex-wrap justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => router.history.back()}>
              {f.cancel}
            </Button>
            <form.AppForm>
              <form.SubmitButton requireChanges={editing}>
                {editing ? f.save : isExpense ? f.submitExpense : f.submitInvoice}
              </form.SubmitButton>
            </form.AppForm>
          </div>
        </div>
      </form>
    </main>
  );
}
