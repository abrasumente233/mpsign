#!/usr/bin/env python
import os
from setuptools import setup, find_packages

if os.environ.get('CONVERT_README'):
    import pypandoc

    long_desc = pypandoc.convert('README.md', 'rst')

    with open('README.rst', 'wb') as f:
        f.write(long_desc.encode('utf-8'))
else:
    long_desc = ''

with open(os.path.join(os.path.dirname(__file__), 'mpsign/VERSION'), 'rb') as f:
    version = f.read().decode('ascii').strip()

setup(name='mpsign',
      version=version,
      description='a tool which signs your bars on Baidu Tieba',
      long_description=long_desc,
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Intended Audience :: Developers',
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
                        'tinydb', 'pycrypto'],
      include_package_data=True,
      entry_points={'console_scripts': ['mpsign = mpsign.cmd:cmd']})
