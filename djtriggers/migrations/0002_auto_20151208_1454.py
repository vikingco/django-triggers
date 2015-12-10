# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('djtriggers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trigger',
            name='date_received',
            field=models.DateTimeField(default=datetime.datetime.now),
            preserve_default=True,
        ),
    ]
