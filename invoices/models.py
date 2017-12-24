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
    verification = models.CharField(max_length=7, blank=True, null=True)
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

    # Returns the committees belonging to the invoice as a list [{ committee_name: 'Name' }, ...]
    def committees(self):
        return self.invoicepart_set.order_by('committee_name').values('committee_name').distinct()

    # Returns the committees belonging to the invoice as a list [{ committee_name: 'Name' }, ...]
    def is_attested(self):
        print(self.invoicepart_set.filter(attested_by__isnull=True).count())
        return self.invoicepart_set.filter(attested_by__isnull=True).count() == 0

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
        exp['committees'] = [committee['committee_name'] for committee in self.committees()]
        return exp

    @staticmethod
    def attestable(may_attest, user):
        if '*' in may_attest:
            return Invoice.objects.exclude(owner__user=user).filter(invoicepart__attested_by=None).distinct()
        return Invoice.objects.exclude(owner__user=user).filter(
            invoicepart__attested_by=None,
            invoicepart__committee_name__iregex=r'(' + '|'.join(may_attest) + ')'
        ).distinct()

    # TODO
    @staticmethod
    def payable():
        return Invoice.objects. \
            exclude(payed_at__isnull=False). \
            exclude(invoicepart__attested_by=None). \
            order_by('owner__user__username')

    # TODO
    @staticmethod
    def accountable(may_account):
        if '*' in may_account:
            return Invoice.objects.exclude(reimbursement=None).filter(verification='').distinct()
        return Invoice.objects.exclude(reimbursement=None).filter(
            verification='',
            invoicepart__committee_name__iregex=r'(' + '|'.join(may_account) + ')'
        ).distinct()

"""
Defines an invoice part, which is a specification of a part of an invoice.
"""
class InvoicePart(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    budget_line_id = models.IntegerField(default=0)
    budget_line_name = models.TextField(blank=True)
    cost_centre_name = models.TextField(blank=True)
    cost_centre_id = models.IntegerField(default=0)
    committee_name = models.TextField(blank=True)
    committee_id = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey('expenses.Profile', blank=True, null=True)
    attest_date = models.DateField(blank=True, null=True)

    # Returns string representation of the model
    def __str__(self):
        return self.invoice.__str__() + " (" + self.budget_line_name + ": " + str(self.amount) + " kr)"

    # Returns unicode representation of the model
    def __unicode__(self):
        return self.invoice.__unicode__() + " (" + self.budget_line_name + ": " + str(self.amount) + " kr)"

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