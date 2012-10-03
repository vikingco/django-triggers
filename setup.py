#!/usr/bin/env python
from setuptools import setup, find_packages
import djtriggers

setup(
    name="django-triggers",
    version=djtriggers.__version__,
    url='https://github.com/citylive/django-triggers',
    license='BSD',
    description="Framework to create and process triggers.",
    long_description=open('README.rst', 'r').read(),
    author='Olivier Sels, City Live nv',
    packages=find_packages(),
    package_data=dict(djtriggers=['']),
    zip_safe=False, # Don't create egg files, Django cannot find templates in egg files.
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
