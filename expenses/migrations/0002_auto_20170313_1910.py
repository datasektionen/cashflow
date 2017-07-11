# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-03-13 19:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='receiver',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to='expenses.Person'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='payment',
            name='payer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payer', to='expenses.Person'),
        ),
    ]