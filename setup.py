#!/usr/bin/env python

from distutils.core import setup

setup(name='xml_models',
      version='0.6.4',
      description='XML backed models queried from external REST apis',
      author='Geoff Ford and Chris Tarttelin and Cam McHugh',
      author_email='g_ford@hotmail.ccom',
      url='http://github.com/alephnullplex/xml_models',
      packages=['rest_client', 'xml_models'],
      install_requires=['lxml', 'python-dateutil', 'pytz'],
      tests_require=['mock', 'coverage']
      )
