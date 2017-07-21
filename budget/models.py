from django.db import models


class Year(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Committee(models.Model):
    year = models.ForeignKey(Year)
    name = models.TextField()

    def __str__(self):
        return self.year.__str__() + ": " + self.name

    def __unicode__(self):
        return self.year.__unicode__() + ": " + self.name


class CostCentre(models.Model):
    committee = models.ForeignKey(Committee)
    name = models.TextField()

    def __str__(self):
        return self.committee.__str__() + " -> " + self.name

    def __unicode__(self):
        return self.committee.__unicode__() + " -> " + self.name


class BudgetLine(models.Model):
    cost_centre = models.ForeignKey(CostCentre)
    name = models.TextField()
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    spent = models.DecimalField(decimal_places=2, max_digits=9)

    def __str__(self):
        return self.cost_centre.__str__() + " -> " + self.name

    def __unicode__(self):
        return self.cost_centre.__unicode__() + " -> " + self.name
