# Generated by Django 3.2.7 on 2023-06-01 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='point',
            name='finTime',
            field=models.DateTimeField(null=True),
        ),
    ]
