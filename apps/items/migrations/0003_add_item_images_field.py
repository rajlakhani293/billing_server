# Generated manually to fix missing item_images field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='item_images',
            field=models.JSONField(blank=True, default=list, help_text='List of item images with metadata'),
        ),
    ]
