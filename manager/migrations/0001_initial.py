# Generated by Django 3.2.7 on 2023-06-01 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='manager',
            fields=[
                ('mId', models.AutoField(primary_key=True, serialize=False)),
                ('pwd', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='staff',
            fields=[
                ('staffId', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=24)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=11)),
                ('pwd', models.CharField(max_length=20)),
                ('staffType', models.CharField(choices=[('S', 'service'), ('F', 'finance')], max_length=20)),
                ('staffStatus', models.CharField(choices=[('A', 'active'), ('D', 'depart'), ('S', 'stop')], max_length=20)),
            ],
        ),
    ]
