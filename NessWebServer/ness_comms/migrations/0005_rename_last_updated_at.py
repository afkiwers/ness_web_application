from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ness_comms', '0004_systemstatus_esp_offline_banner_enabled'),
    ]

    operations = [
        migrations.RenameField(
            model_name='systemstatus',
            old_name='last_updated_at',
            new_name='status_last_requested',
        ),
        migrations.AlterField(
            model_name='systemstatus',
            name='status_last_requested',
            field=models.DateTimeField(blank=True, null=True, verbose_name='ESP Status Last Requested'),
        ),
    ]
