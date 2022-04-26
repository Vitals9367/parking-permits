# Generated by Django 3.2.12 on 2022-04-26 13:25

from django.db import migrations, models
import django.db.models.deletion

DROP_ORDER_NUMBER_SQL = """
ALTER TABLE parking_permits_order
DROP COLUMN order_number;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("parking_permits", "0024_subscription"),
    ]

    operations = [
        migrations.RunSQL(DROP_ORDER_NUMBER_SQL, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="order",
            name="id",
        ),
        migrations.RemoveField(
            model_name="order",
            name="order_type",
        ),
        migrations.RemoveField(
            model_name="order",
            name="talpa_subscription_id",
        ),
        migrations.AddField(
            model_name="order",
            name="order_number",
            field=models.BigAutoField(
                editable=False,
                primary_key=True,
                serialize=False,
                verbose_name="order number",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="subscription",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="parking_permits.subscription",
                verbose_name="Subscription",
            ),
        ),
    ]
