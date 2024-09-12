from django.db import models
from django.contrib.auth.models import User
from expenses.models import *

"""
Represents an invoice.
"""
class Invoice(models.Model):
    created_date = models.DateField(auto_now_add=True)
    invoice_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    confirmed_by = models.ForeignKey(User, blank=True, null=True)
    confirmed_at = models.DateField(blank=True, null=True, default=None)
    owner = models.ForeignKey('expenses.Profile')
    description = models.TextField()
    file_is_original = models.BooleanField()
    verification = models.CharField(max_length=7, blank=True)
    payed_at = models.DateField(blank=True, null=True, default=None)
    payed_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="payed")

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
        comment = Comment(
            author=user.profile,
            invoice=self,
            content="Betalade fakturan ```" + str(self) + "```"
        )
        comment.save()

    # Return the total amount of the invoice parts
    def total_amount(self):
        total = 0
        for part in self.invoicepart_set.all():
            total += part.amount
        return total

    # Returns the cost centres belonging to the invoice as a list [{ cost_centre: 'Name' }, ...]
    def cost_centres(self):
        return self.invoicepart_set.order_by('cost_centre').values('cost_centre').distinct()

    def is_attested(self):
        return self.invoicepart_set.filter(attested_by__isnull=True).count() == 0

    def is_payed(self):
        if self.payed_at and self.payed_by:
            return True
        return False

    # TODO
    def is_payable(self):
        if self.payed_at:
            return False
        for ip in self.invoicepart_set.all():
            if ip.attested_by == None: return False
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
    def view_attestable(may_attest, user):
        filters = {
            'invoicepart__attested_by': None,
        }
        if 'firmatecknare' not in may_attest:
            filters['invoicepart__cost_centre__iregex'] = r'(' + '|'.join(may_attest) + ')'
        return Invoice.objects.order_by('-due_date').filter(**filters).distinct()

    # TODO
    @staticmethod
    def payable():
        return Invoice.objects. \
            exclude(payed_at__isnull=False). \
            exclude(invoicepart__attested_by=None). \
            order_by('due_date')

    # TODO
    @staticmethod
    def view_accountable(may_account):
        if '*' in may_account:
            return Invoice.objects.exclude(payed_at__isnull=True).filter(verification='').distinct()
        return Invoice.objects.exclude(payed_at__isnull=True).filter(
            verification='',
            invoicepart__cost_centre__iregex=r'(' + '|'.join(may_account) + ')'
        ).distinct()

"""
Defines an invoice part, which is a specification of a part of an invoice.
"""
class InvoicePart(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    cost_centre = models.TextField(blank=True)
    secondary_cost_centre = models.TextField(blank=True)
    budget_line = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey('expenses.Profile', blank=True, null=True)
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
        comment = Comment(
            author=user.profile,
            invoice=self.invoice,
            content="Attesterar fakturadelen ```" + str(self) + "```"
        )
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
