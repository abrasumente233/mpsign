#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='mpsign',
      version='1.1',
      description='a tool which signs your bars on Baidu Tieba',
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Topic :: Utilities'
      ],
      author='abrasumente mp',
      author_email='abrasumentee@gmail.com',
      url='https://github.com/abrasumente233/mpsign',
      license='MIT',
      zip_safe=False,
      packages=find_packages(exclude=('tests', 'tests.*')),
      install_requires=['docopt', 'requests', 'beautifulsoup4', 'cached_property',
                        'tinydb', 'ujson'],
      entry_points={'console_scripts': ['mpsign = mpsign.cmd:cmd']})