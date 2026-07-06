# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0026_alter_payment_account'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='default_account',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='account',
        ),
        migrations.DeleteModel(
            name='BankAccount',
        ),
    ]
