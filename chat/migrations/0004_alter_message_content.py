# Generated by Django 4.1.2 on 2022-11-06 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_alter_message_images"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="content",
            field=models.CharField(blank=True, max_length=512),
        ),
    ]