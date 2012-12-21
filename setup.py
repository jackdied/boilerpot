#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup, find_packages

setup(name="boilerpot",
      version="0.9"
      description="HTML content extraction",
      author="Jack Diederich",
      author_email="jackdied@gmail.com",
      url="http://github.com/jackdied/boilerpot",
      packages = find_packages(),
      license = "Apache License",
      keywords="html, scraping, templating",
      zip_safe = True,
      py_modules=['boilerpot'],
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
