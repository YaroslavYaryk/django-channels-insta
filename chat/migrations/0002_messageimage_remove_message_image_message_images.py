# Generated by Django 4.1.2 on 2022-11-06 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image", models.ImageField(null=True, upload_to="message_images/")),
            ],
        ),
        migrations.RemoveField(
            model_name="message",
            name="image",
        ),
        migrations.AddField(
            model_name="message",
            name="images",
            field=models.ManyToManyField(
                blank=True, null=True, to="chat.messageimage", verbose_name=""
            ),
        ),
    ]
