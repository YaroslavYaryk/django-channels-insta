# Generated by Django 4.1.2 on 2022-11-06 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_messageimage_remove_message_image_message_images"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="images",
            field=models.ManyToManyField(
                blank=True, to="chat.messageimage", verbose_name=""
            ),
        ),
    ]
