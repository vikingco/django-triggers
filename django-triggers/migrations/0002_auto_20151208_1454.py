# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django-triggers", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trigger",
            name="date_received",
            field=models.DateTimeField(default=datetime.datetime.now),
            preserve_default=True,
        ),
    ]
