# Generated by Django 3.2 on 2021-10-19 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parking_permits_app", "0026_customer_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="parkingpermit",
            name="order_id",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="parkingpermit",
            name="subscription_id",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
