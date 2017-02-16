# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-01-17 03:48
from __future__ import unicode_literals

import inspect
from logging import getLogger

from django.apps import apps as all_apps
from django.db import migrations, models
from django.db.utils import ProgrammingError
import django.db.models.deletion

from djtriggers.models import Trigger


logger = getLogger(__name__)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('djtriggers', '0003_auto_20160512_0847'),
    ]

    operations = [
        migrations.AddField(
            model_name='trigger',
            name='content_type',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='trigger',
            name='number_of_tries',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='date_received',
            field=models.DateTimeField(default=django.utils.timezone.now),
        )
    ]
