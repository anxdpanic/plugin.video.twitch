from distutils.core import setup
from twitch import VERSION

setup(
    name='python-twitch',
    description='Library for interaction with the videogame streaming platform twitch',
    long_description=open('README.rst').read(),
    version=VERSION,
    packages=['twitch'],
    license='GPLv3',
    author='winlu',
    author_email='derwinlu+python-twitch@gmail.com',
    url='https://pypi.python.org/pypi/python-twitch',
)
