# Generated by Django 4.2.3 on 2023-07-10 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_book_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='rating',
            field=models.DecimalField(decimal_places=2, default=None, max_digits=3, null=True),
        ),
    ]