import ast
import re

from distutils.core import setup

_version_re = re.compile(r'VERSION\s+=\s+(.*)')
with open('twitch/__init__.py', 'rb') as f:
    VERSION = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='python-twitch',
    description='Library for interaction with the videogame streaming platform twitch',
    long_description=open('README.rst').read(),
    version=VERSION,
    packages=['twitch', 'twitch.api', 'twitch.api.v2', 'twitch.api.v3'],
    install_requires=['six >= 1.9.0'],
    license='GPLv3',
    author='winlu',
    author_email='derwinlu+python-twitch@gmail.com',
    url='https://pypi.python.org/pypi/python-twitch',
)
