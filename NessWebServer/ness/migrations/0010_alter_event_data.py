# Generated by Django 4.1.5 on 2023-03-05 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ness', '0009_alter_event_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='data',
            field=models.CharField(max_length=60, verbose_name='Data Field'),
        ),
    ]
