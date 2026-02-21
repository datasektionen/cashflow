import re
from datetime import date

from django.contrib.auth.models import User
from django.db import models
from django.forms.models import model_to_dict


class Invoice(models.Model):
    """
    Represents an invoice.
    """
    created_date = models.DateField(auto_now_add=True)
    invoice_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    # TODO: Is there a better choice for on_delete?
    confirmed_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.DO_NOTHING)
    confirmed_at = models.DateField(blank=True, null=True, default=None)
    owner = models.ForeignKey('expenses.Profile', on_delete=models.DO_NOTHING)
    description = models.TextField()
    file_is_original = models.BooleanField()
    verification = models.CharField(max_length=7, blank=True)
    payed_at = models.DateField(blank=True, null=True, default=None)
    payed_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="payed",
                                 on_delete=models.DO_NOTHING)

    # Returns a string representation of the invoice
    def __str__(self):
        return self.description

    # Returns a unicode representation of the invoice
    def __unicode__(self):
        return self.description

    # Returns a json dict from the invoice
    def __repr__(self):
        return str(self.to_dict())

    def status(self):
        if self.verification: return "Bokförd som " + str(self.verification)
        return "Oklart"

    def pay(self, user):
        self.payed_by = user
        self.payed_at = date.today()
        self.save()

        from expenses.models import Comment
        comment = Comment(author=user.profile, invoice=self, content="Betalade fakturan ```" + str(self) + "```")
        comment.save()

    # Return the total amount of the invoice parts
    def total_amount(self):
        return sum([part.amount for part in self.parts.all()])  # return total

    # Returns the cost centres belonging to the invoice as a list [{ cost_centre: 'Name' }, ...]
    def cost_centres(self):
        return self.parts.order_by('cost_centre').values('cost_centre').distinct()

    def is_attested(self):
        return self.parts.filter(attested_by__isnull=True).count() == 0

    def is_payed(self):
        if self.payed_at and self.payed_by:
            return True
        return False

    # TODO
    def is_payable(self):
        if self.payed_at:
            return False
        for ip in self.parts.all():
            if ip.attested_by is None: return False
        return True

    # Returns a dict representation of the model
    def to_dict(self):
        exp = model_to_dict(self)
        exp['invoice_parts'] = [part.to_dict() for part in InvoicePart.objects.filter(invoice=self)]
        exp['owner_username'] = self.owner.user.username
        exp['owner_first_name'] = self.owner.user.first_name
        exp['owner_last_name'] = self.owner.user.last_name
        exp['amount'] = self.total_amount()
        exp['cost_centres'] = [cost_centre['cost_centre'] for cost_centre in self.cost_centres()]
        return exp

    @staticmethod
    def view_attestable(user):
        filters = {'invoicepart__attested_by': None, }
        cost_centres = user.profile.attestable_cost_centres()
        if cost_centres is not True:
            escaped = [re.escape(cc) for cc in cost_centres]
            filters['invoicepart__cost_centre__iregex'] = r'(' + '|'.join(escaped) + ')'
        return Invoice.objects.order_by('due_date').filter(**filters).distinct()

    # # TODO
    @staticmethod
    def payable():
        return Invoice.objects.exclude(payed_at__isnull=True, invoicepart__attested_by__isnull=True)

    # TODO
    @staticmethod
    def view_accountable(user):
        return Invoice.objects.exclude(payed_at__isnull=True).order_by("invoice_date")


class InvoicePart(models.Model):
    """
    Defines an invoice part, which is a specification of a part of an invoice.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="parts",
                                related_query_name="invoicepart")
    cost_centre = models.TextField(blank=True)
    secondary_cost_centre = models.TextField(blank=True)
    budget_line = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey('expenses.Profile', blank=True, null=True, on_delete=models.DO_NOTHING)
    attest_date = models.DateField(blank=True, null=True)

    # Returns string representation of the model
    def __str__(self):
        return self.invoice.__str__() + " (" + self.budget_line + ": " + str(self.amount) + " kr)"

    # Returns unicode representation of the model
    def __unicode__(self):
        return self.invoice.__unicode__() + " (" + self.budget_line + ": " + str(self.amount) + " kr)"

    def attest(self, user):
        self.attested_by = user.profile
        self.attest_date = date.today()

        self.save()
        from expenses.models import Comment
        comment = Comment(author=user.profile, invoice=self.invoice,
                          content="Attesterar fakturadelen ```" + str(self) + "```")
        comment.save()

    # Returns dict representation of the model
    def to_dict(self):
        exp_part = model_to_dict(self)
        del exp_part['invoice']
        if self.attested_by is not None:
            exp_part['attested_by_username'] = self.attested_by.user.username
            exp_part['attested_by_first_name'] = self.attested_by.user.first_name
            exp_part['attested_by_last_name'] = self.attested_by.user.last_name
        return exp_part
