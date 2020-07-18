# Generated by Django 3.0.7 on 2020-07-16 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitewide', '0003_zappyuser_pic'),
    ]

    operations = [
        migrations.AddField(
            model_name='zappyuser',
            name='apple_expires_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='zappyuser',
            name='apple_product_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
