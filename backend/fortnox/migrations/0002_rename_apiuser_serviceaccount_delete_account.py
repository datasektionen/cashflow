from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fortnox', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='APIUser',
            new_name='ServiceAccount',
        ),
        migrations.DeleteModel(
            name='Account',
        ),
    ]
