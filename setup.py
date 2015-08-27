#!/usr/bin/env python

from setuptools import setup

try:
    import pypandoc

    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='xml_models2',
    version='0.8.0',
    description='XML backed models queried from external REST apis',
    long_description=long_description,
    author='Geoff Ford and Chris Tarttelin and Cam McHugh',
    author_email='g_ford@hotmail.ccom',
    url='http://github.com/alephnullplex/xml_models',
    packages=['xml_models', 'xml_models.rest_client'],
    install_requires=['lxml', 'python-dateutil', 'pytz', 'future', 'requests'],
    tests_require=['mock', 'nose', 'coverage'],
    test_suite="nose.collector"
)
