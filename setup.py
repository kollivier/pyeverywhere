from setuptools import setup
import pew

setup(
    name='pyeverywhere',
    version=pew.__version__,
    description='Build and deploy cross-platform desktop and mobile apps using Python.',
    author='Kevin Ollivier',
    author_email='kevin@kosoftworks.com',
    license='APL',
    scripts=['pew'],
    package_dir={'': 'src'},
    packages=['pew', 'pewtools'],
    setup_requires=['requests']
    # test_suite = 'your.module.tests',
)
