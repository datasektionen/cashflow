from django.core.management.base import BaseCommand

from cashflow import gordian


class Command(BaseCommand):
    help = "Warm the Gordian cache (cost centres, secondary cost centres, budget lines)."

    def handle(self, *args, **options):
        cost_centres = gordian.list_cost_centres_from_gordian(force_refresh=True)
        snd_cost_centres = gordian.list_secondary_cost_centres_from_gordian(force_refresh=True)
        budget_lines = gordian.list_budget_lines_from_gordian(force_refresh=True)

        self.stdout.write(self.style.SUCCESS(
            f"Warmed Gordian cache: {len(cost_centres)} cost centres, "
            f"{len(snd_cost_centres)} secondary cost centres, "
            f"{len(budget_lines)} budget lines."
        ))
