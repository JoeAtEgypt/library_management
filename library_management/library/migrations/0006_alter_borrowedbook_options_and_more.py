# Generated by Django 5.1.11 on 2025-06-22 16:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_alter_borrowtransaction_borrowed_books_count'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='borrowedbook',
            options={'verbose_name': 'Borrowed Book', 'verbose_name_plural': 'Borrowed Books'},
        ),
        migrations.AlterUniqueTogether(
            name='borrowedbook',
            unique_together={('transaction', 'book')},
        ),
    ]
