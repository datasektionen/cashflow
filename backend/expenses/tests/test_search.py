import pytest

from expenses.factories import ExpenseFactory
from expenses.models import Expense
from expenses.search import expense_search


@pytest.mark.django_db
class TestExpenseSearch:
    def test_description_matches_exact_substring(self):
        match = ExpenseFactory(description="Coffee machine repair")
        ExpenseFactory(description="Office chairs")

        result = expense_search(Expense.objects.all(), description="coffee")

        assert list(result) == [match]

    def test_description_fuzzy_matches_typo(self):
        match = ExpenseFactory(description="Coffee machine repair")
        ExpenseFactory(description="Train tickets to Gothenburg")

        result = expense_search(
            Expense.objects.all(), description_fuzzy="Cofee machne repair"
        )

        assert list(result) == [match]

    def test_no_search_fields_returns_all(self):
        ExpenseFactory.create_batch(3)

        result = expense_search(Expense.objects.all())

        assert result.count() == 3

    def test_accounted_true_returns_only_accounted(self):
        accounted = ExpenseFactory(verification="A123")
        ExpenseFactory(verification="")

        result = expense_search(Expense.objects.all(), accounted=True)

        assert list(result) == [accounted]

    def test_accounted_false_returns_only_unaccounted(self):
        ExpenseFactory(verification="A123")
        unaccounted = ExpenseFactory(verification="")

        result = expense_search(Expense.objects.all(), accounted=False)

        assert list(result) == [unaccounted]
