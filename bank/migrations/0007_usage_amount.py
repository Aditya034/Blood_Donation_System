# Generated by Django 4.2.1 on 2023-05-26 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0006_usage'),
    ]

    operations = [
        migrations.AddField(
            model_name='usage',
            name='amount',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
