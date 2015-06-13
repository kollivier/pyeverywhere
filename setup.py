from setuptools import setup

setup(
    name='pyeverywhere',
    version='1.0',
    description='Build and deploy cross-platform desktop and mobile apps using Python.',
    author='Kevin Ollivier',
    author_email='kevin@kosoftworks.com',
    license='APL',
    scripts=['pew'],
    package_dir={'': 'src'},
    packages=['pew', 'pewtools'],
    # test_suite = 'your.module.tests',
)
