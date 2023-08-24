#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import environ
from sys import argv

if __name__ == "__main__":
    environ.setdefault("DJANGO_SETTINGS_MODULE", "django-triggers.tests.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(argv)
