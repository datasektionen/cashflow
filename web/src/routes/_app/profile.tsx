import { createConnectQueryKey, useMutation, useSuspenseQuery, useTransport } from "@connectrpc/connect-query";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { CircleAlert, Landmark } from "lucide-react";
import { toast } from "sonner";
import { useAppForm } from "#/components/form/form";
import { applyServerErrors } from "#/components/form/server-errors";
import { Page } from "#/components/layout/page";
import { Alert, AlertDescription } from "#/components/ui/alert";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "#/components/ui/card";
import { FieldGroup } from "#/components/ui/field";
import type { User } from "#/gen/cashflow/user/v1/user_pb";
import { getMe, updateBankDetails } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { formatBankAccount } from "#/lib/bank";
import { useT } from "#/lib/i18n";

export const Route = createFileRoute("/_app/profile")({
  component: ProfilePage,
});

function ProfilePage() {
  const t = useT();
  const { data } = useSuspenseQuery(getMe, {});
  if (!data.user) throw new Error("GetMe returned no user");

  return (
    <Page title={t.profile.title}>
      <BankDetailsCard user={data.user} />
    </Page>
  );
}

function BankDetailsCard({ user }: { user: User }) {
  const t = useT();
  const queryClient = useQueryClient();
  const transport = useTransport();
  const save = useMutation(updateBankDetails);
  const hasBankDetails = Boolean(user.clearingNumber && user.bankAccount);

  const form = useAppForm({
    defaultValues: {
      clearingNumber: user.clearingNumber,
      bankAccount: user.bankAccount,
      bankName: user.bankName,
    },
    onSubmit: async ({ value, formApi }) => {
      try {
        const { user: saved } = await save.mutateAsync(value);
        // GetMe also carries the user, so update it in place instead of refetching.
        queryClient.setQueryData(
          createConnectQueryKey({ schema: getMe, input: {}, transport, cardinality: "finite" }),
          (old) => (old ? { ...old, user: saved } : old),
        );
        formApi.reset({
          clearingNumber: saved?.clearingNumber ?? "",
          bankAccount: saved?.bankAccount ?? "",
          bankName: saved?.bankName ?? "",
        });
        toast.success(t.profile.saved);
      } catch (error) {
        if (!applyServerErrors(formApi, error, t)) toast.error(t.errors.generic);
      }
    },
  });

  return (
    <Card className="max-w-xl">
      <form
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          void form.handleSubmit();
        }}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Landmark className="size-4 text-primary" /> {t.profile.bankTitle}
          </CardTitle>
          <CardDescription>
            {t.profile.bankDescription}
            {hasBankDetails && (
              <span className="mt-2 block amount text-foreground">
                {formatBankAccount(user.clearingNumber, user.bankAccount)}
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="mt-4">
          {!hasBankDetails && (
            <Alert className="mb-6">
              <CircleAlert />
              <AlertDescription>{t.profile.missing}</AlertDescription>
            </Alert>
          )}
          <FieldGroup>
            <div className="grid gap-4 sm:grid-cols-[10rem_1fr]">
              <form.AppField name="clearingNumber">
                {(field) => (
                  <field.TextField
                    label={t.profile.clearingNumber}
                    description={t.profile.clearingHint}
                    inputMode="numeric"
                    className="amount"
                  />
                )}
              </form.AppField>
              <form.AppField name="bankAccount">
                {(field) => <field.TextField label={t.profile.bankAccount} inputMode="numeric" className="amount" />}
              </form.AppField>
            </div>
            <form.AppField name="bankName">
              {(field) => <field.TextField label={t.profile.bankName} autoComplete="off" placeholder="Swedbank" />}
            </form.AppField>
          </FieldGroup>
        </CardContent>
        <CardFooter className="mt-6 justify-end">
          <form.AppForm>
            <form.SubmitButton>{t.profile.save}</form.SubmitButton>
          </form.AppForm>
        </CardFooter>
      </form>
    </Card>
  );
}
