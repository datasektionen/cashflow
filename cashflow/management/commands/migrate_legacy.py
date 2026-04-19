
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import connection, connections, transaction
from django.db.models.signals import post_save
from django.utils.timezone import now

from expenses.models import Comment, Expense, ExpensePart
from expenses.models import create_user_profile, save_user_profile, send_mail
from invoices.models import Invoice, InvoicePart
from cashflow import snapshots


def copy_table(legacy_cursor, table_name):
    legacy_cursor.execute(f"SELECT * FROM {table_name}")
    cols = [d[0] for d in legacy_cursor.description]
    rows = legacy_cursor.fetchall()
    col_names = ", ".join(cols)
    placeholders = ", ".join(["%s"] * len(cols))
    with connection.cursor() as dest:
        for row in rows:
            dest.execute(
                f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                row,
            )
    return len(rows)


class Command(BaseCommand):
    help = "Migrates all data from the legacy database, generating snapshots for expenses"

    def handle(self, *args, **options):
        with connections['legacy'].cursor() as cursor:
            cursor.execute("""
                SELECT e.id, e.created_date, e.expense_date, e.confirmed_by_id, e.confirmed_at,
                       e.owner_id, e.description, e.reimbursement_id, e.verification, e.is_flagged,
                       au.first_name, au.last_name, au.email
                FROM expenses_expense e
                JOIN expenses_profile ep ON ep.id = e.owner_id
                JOIN auth_user au ON au.id = ep.user_id
            """)
            expenses = cursor.fetchall()

            cursor.execute("""
                SELECT ep.id, ep.expense_id, ep.amount, ep.attested_by_id, ep.attest_date,
                       ep.cost_centre, ep.secondary_cost_centre, ep.budget_line
                FROM expenses_expensepart ep
            """)
            parts = cursor.fetchall()

            cursor.execute("""
                SELECT i.id, i.created_date, i.invoice_date, i.due_date, i.confirmed_by_id, i.confirmed_at,
                       i.owner_id, i.description, i.file_is_original, i.verification, i.payed_at, i.payed_by_id,
                       au.first_name, au.last_name, au.email
                FROM invoices_invoice i
                JOIN expenses_profile ep ON ep.id = i.owner_id
                JOIN auth_user au ON au.id = ep.user_id
            """)
            invoices = cursor.fetchall()

            cursor.execute("""
                SELECT ip.id, ip.invoice_id, ip.amount, ip.attested_by_id, ip.attest_date,
                       ip.cost_centre, ip.secondary_cost_centre, ip.budget_line
                FROM invoices_invoicepart ip
            """)
            invoice_parts = cursor.fetchall()

        parts_by_expense = {}
        for part in parts:
            parts_by_expense.setdefault(part[1], []).append(part)

        parts_by_invoice = {}
        for part in invoice_parts:
            parts_by_invoice.setdefault(part[1], []).append(part)

        with connections['legacy'].cursor() as cursor, transaction.atomic():
            post_save.disconnect(create_user_profile, sender=User)
            post_save.disconnect(save_user_profile, sender=User)
            post_save.disconnect(send_mail, sender=Comment)

            for table in [
                "auth_user",
                "expenses_profile",
                "expenses_payment",
            ]:
                n = copy_table(cursor, table)
                self.stdout.write(f"Copied {n} rows from {table}")

            self.stdout.write("Migrating expenses and expense parts...")
            for row in expenses:
                (eid, created_date, expense_date, confirmed_by_id, confirmed_at,
                 owner_id, description, reimbursement_id, verification, is_flagged,
                 first_name, last_name, email) = row

                captured_at = now()
                expense_snapshot = snapshots.ExpenseSnapshot(
                    captured_at=captured_at,
                    owner=snapshots.Owner(name=f"{first_name} {last_name}", email=email),
                )
                Expense.objects.update_or_create(
                    id=eid,
                    defaults=dict(
                        created_date=created_date, expense_date=expense_date,
                        confirmed_by_id=confirmed_by_id, confirmed_at=confirmed_at,
                        owner_id=owner_id, description=description,
                        reimbursement_id=reimbursement_id, verification=verification,
                        is_flagged=is_flagged,
                        snapshot=expense_snapshot.model_dump(mode='json'),
                    ),
                )

                for pid, _, amount, attested_by_id, attest_date, cost_centre, secondary_cost_centre, budget_line in parts_by_expense.get(eid, []):
                    part_snapshot = snapshots.ExpensePartSnapshot(
                        captured_at=captured_at,
                        budget_line=snapshots.Budgetline(
                            name=budget_line,
                            cost_center=cost_centre,
                            secondary_cost_center=secondary_cost_centre,
                        ),
                    )
                    ExpensePart.objects.update_or_create(
                        id=pid,
                        defaults=dict(
                            expense_id=eid, gordian_budget_line=None,
                            amount=amount, attested_by_id=attested_by_id,
                            attest_date=attest_date,
                            snapshot=part_snapshot.model_dump(mode='json'),
                        ),
                    )

            self.stdout.write("Migrating invoices and invoice parts...")
            for row in invoices:
                (iid, created_date, invoice_date, due_date, confirmed_by_id, confirmed_at,
                 owner_id, description, file_is_original, verification, payed_at, payed_by_id,
                 first_name, last_name, email) = row

                captured_at = now()
                invoice_snapshot = snapshots.InvoiceSnapshot(
                    captured_at=captured_at,
                    owner=snapshots.Owner(name=f"{first_name} {last_name}", email=email),
                )
                Invoice.objects.update_or_create(
                    id=iid,
                    defaults=dict(
                        created_date=created_date, invoice_date=invoice_date, due_date=due_date,
                        confirmed_by_id=confirmed_by_id, confirmed_at=confirmed_at,
                        owner_id=owner_id, description=description,
                        file_is_original=file_is_original, verification=verification,
                        payed_at=payed_at, payed_by_id=payed_by_id,
                        snapshot=invoice_snapshot.model_dump(mode='json'),
                    ),
                )

                for pid, _, amount, attested_by_id, attest_date, cost_centre, secondary_cost_centre, budget_line in parts_by_invoice.get(iid, []):
                    part_snapshot = snapshots.InvoicePartSnapshot(
                        captured_at=captured_at,
                        budget_line=snapshots.Budgetline(
                            name=budget_line,
                            cost_center=cost_centre,
                            secondary_cost_center=secondary_cost_centre,
                        ),
                    )
                    InvoicePart.objects.update_or_create(
                        id=pid,
                        defaults=dict(
                            invoice_id=iid, gordian_budget_line=None,
                            amount=amount, attested_by_id=attested_by_id,
                            attest_date=attest_date,
                            snapshot=part_snapshot.model_dump(mode='json'),
                        ),
                    )

            for table in ["expenses_comment", "expenses_file"]:
                n = copy_table(cursor, table)
                self.stdout.write(f"Copied {n} rows from {table}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Migrated {len(expenses)} expenses, {len(parts)} expense parts, "
            f"{len(invoices)} invoices and {len(invoice_parts)} invoice parts."
        ))