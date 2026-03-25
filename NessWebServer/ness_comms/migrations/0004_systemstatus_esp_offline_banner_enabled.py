from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ness_comms', '0003_add_webhook_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemstatus',
            name='esp_offline_banner_enabled',
            field=models.BooleanField(default=False, verbose_name='ESP Offline Banner Enabled'),
        ),
    ]
