import os
import sys

from setuptools import find_packages, setup

sys.path.insert(0, os.path.abspath('src'))
import pew

setup(
    name='pyeverywhere',
    version=pew.__version__,
    description='Build and deploy cross-platform desktop and mobile apps using Python.',
    author='Kevin Ollivier',
    author_email='kevin@kosoftworks.com',
    license='APL',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    setup_requires=['requests'],
    # test_suite = 'your.module.tests',
    entry_points={
        'console_scripts': [
            'pew = pew.tool:main'
        ]
    }
)
