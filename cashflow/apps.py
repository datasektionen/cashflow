from django.apps import AppConfig
import logging


class CashflowConfig(AppConfig):
    name = 'cashflow'

    def ready(self):
        from cashflow import gordian
        logging.getLogger(__name__).info("Attempting to warm up Gordian cache on startup")
        try:
            gordian.list_cost_centres_from_gordian()
            gordian.list_secondary_cost_centres_from_gordian()
            gordian.list_budget_lines_from_gordian()
            logging.getLogger(__name__).info("Warmed up Gordian cache on startup")
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to warm up GOrdian cache on startup: %s", e)