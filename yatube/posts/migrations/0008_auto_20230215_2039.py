# Generated by Django 2.2.16 on 2023-02-15 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20230215_2034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='created',
            field=models.DateField(auto_now=True),
        ),
    ]
