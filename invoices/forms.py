from django.forms import ModelForm, inlineformset_factory, Select
from django.forms.fields import IntegerField

from invoices.models import InvoicePart, Invoice

# COST_CENTRE_CHOICES = [(cc["CostCentreName"], cc["CostCentreName"]) for cc in
#                        InvoicePart.list_cost_centres_from_gordian()]
# SND_COST_CENTRE_CHOICES = [(scc["SecondaryCostCentreName"], scc["SecondaryCostCentreName"]) for scc in
#                            InvoicePart.list_secondary_cost_centres_from_gordian()]
# BUDGET_LINE_CHOICES = [(bl["BudgetLineName"], bl["BudgetLineName"]) for bl in
#                        InvoicePart.list_budget_lines_from_gordian()]
#

class InvoicePartForm(ModelForm):

    account = IntegerField()

    class Meta:
        model = InvoicePart
        # fields = ["cost_centre", "secondary_cost_centre", "budget_line"]
        exclude = ('cost_centre', 'secondary_cost_centre', 'budget_line')

        # widgets = {"cost_centre": Select(choices=COST_CENTRE_CHOICES),
        #            "secondary_cost_centre": Select(choices=SND_COST_CENTRE_CHOICES),
        #            "budget_line": Select(choices=BUDGET_LINE_CHOICES), }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields["cost_centre"].initial = self.instance.cost_centre
        # self.fields["secondary_cost_centre"].initial = (self.instance.secondary_cost_centre,
        #                                                 self.instance.secondary_cost_centre)
        # self.fields["budget_line"].initial = self.instance.budget_line


InvoicePartFormSet = inlineformset_factory(Invoice, InvoicePart, form=InvoicePartForm, extra=0, )
