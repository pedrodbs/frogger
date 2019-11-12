#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='frogger',
      version='1.0',
      description='Frogger game implemented in Python with interfaces to PLE and OpenAI Gym.',
      url='https://github.com/pedrodbs/frogger.git',
      author='Pedro Sequeira',
      author_email='pedrodbs@gmail.com',
      packages=find_packages(),
      scripts=[
            'examples/manual_gym.py', 'examples/random_gym.py', 'examples/random_ple.py'
      ],
      install_requires=[
          'numpy', 'gym', 'pygame'
      ],
      zip_safe=True
      )
