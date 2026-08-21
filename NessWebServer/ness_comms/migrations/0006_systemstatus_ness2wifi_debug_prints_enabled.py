from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ness_comms', '0005_rename_last_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemstatus',
            name='ness2wifi_debug_prints_enabled',
            field=models.BooleanField(default=False, verbose_name='Ness WiFi Debug Prints Enabled'),
        ),
    ]
