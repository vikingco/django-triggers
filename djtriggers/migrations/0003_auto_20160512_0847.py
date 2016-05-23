# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djtriggers', '0002_auto_20151208_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='source',
            field=models.CharField(db_index=True, max_length=250, null=True, blank=True),
        ),
    ]
