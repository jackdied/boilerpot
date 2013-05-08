#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="boilerpot",
      version="0.91",
      description="HTML content extraction",
      long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
      author="Jack Diederich",
      author_email="jackdied@gmail.com",
      url="http://github.com/jackdied/boilerpot",
      packages = ['boilerpot'],
      license = "Apache License",
      keywords="html, scraping, templating",
      zip_safe = True,
      py_modules=[],
      classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
     )
