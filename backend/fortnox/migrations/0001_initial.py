import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('AccountID', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('URL', models.TextField()),
                ('Active', models.BooleanField()),
                ('BalanceBroughtForward', models.DecimalField(decimal_places=2, max_digits=9)),
                ('CostCenter', models.TextField()),
                ('CostCenterSettings', models.TextField()),
                ('Description', models.TextField()),
                ('Number', models.IntegerField()),
                ('Project', models.TextField()),
                ('ProjectSettings', models.TextField()),
                ('SRU', models.IntegerField()),
                ('VATCode', models.TextField()),
                ('Year', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='APIUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authenticated_by', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('access_token', models.TextField()),
                ('refresh_token', models.TextField()),
                ('expires_at', models.DateTimeField()),
            ],
        ),
    ]
