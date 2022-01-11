# Generated by Django 3.2 on 2021-12-23 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parking_permits", "0004_alter_orderitem_permit"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="talpa_checkout_url",
            field=models.URLField(blank=True, verbose_name="Talpa checkout url"),
        ),
        migrations.AddField(
            model_name="order",
            name="talpa_receipt_url",
            field=models.URLField(blank=True, verbose_name="Talpa receipt_url"),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="vat",
            field=models.DecimalField(
                decimal_places=4, max_digits=6, verbose_name="VAT"
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="vat",
            field=models.DecimalField(
                decimal_places=4, max_digits=6, verbose_name="VAT"
            ),
        ),
    ]