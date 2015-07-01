#!/usr/bin/env python

from setuptools import setup

setup(name='xml_models',
      version='0.7.0',
      description='XML backed models queried from external REST apis',
      author='Geoff Ford and Chris Tarttelin and Cam McHugh',
      author_email='g_ford@hotmail.ccom',
      url='http://github.com/alephnullplex/xml_models',
      packages=['xml_models'],
      install_requires=['lxml', 'python-dateutil', 'pytz', 'future', 'requests'],
      tests_require=['mock', 'nose', 'coverage'],
      test_suite="nose.collector"
      )
