# Generated by Django 4.0.4 on 2022-05-26 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserTokenDatabase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255)),
                ('database', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'user_database',
            },
        ),
    ]
