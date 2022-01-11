# Generated by Django 3.2 on 2022-01-11 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parking_permits", "0006_product_user_stamped"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="unit",
            field=models.CharField(
                choices=[("MONTHLY", "Monthly"), ("PIECES", "Pieces")],
                default="MONTHLY",
                max_length=50,
                verbose_name="Unit",
            ),
        ),
    ]