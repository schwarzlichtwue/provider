import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name='provider',
    version="0.0.2",
    author='schwarzlichtwue',
    author_email='schwarzlicht.wuerzburg@gmail.com',
    description=('Content crawler for Twitter and Facebook'),
    long_description=read('readme.md'),
    license='mit',
    include_package_data=False,
    packages=find_packages(),
    entry_points={'console_scripts': [
        'content-provider=provider.script:main',
    ]},
    install_requires=['argparse', 'tweepy', 'python-decouple', 'apscheduler'],
)
