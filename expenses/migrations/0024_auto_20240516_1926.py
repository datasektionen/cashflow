# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2024-05-16 19:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0023_expense_is_digital'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expensepart',
            old_name='budget_line_name',
            new_name='budget_line',
        ),
        migrations.RenameField(
            model_name='expensepart',
            old_name='committee_name',
            new_name='cost_centre',
        ),
        migrations.RenameField(
            model_name='expensepart',
            old_name='cost_centre_name',
            new_name='secondary_cost_centre',
        ),
        migrations.RemoveField(
            model_name='expensepart',
            name='budget_line_id',
        ),
        migrations.RemoveField(
            model_name='expensepart',
            name='committee_id',
        ),
        migrations.RemoveField(
            model_name='expensepart',
            name='cost_centre_id',
        ),
    ]
