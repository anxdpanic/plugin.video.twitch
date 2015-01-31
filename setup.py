from distutils.core import setup
from twitch import VERSION

setup(
    name='python-twitch',
    description='Python Module for interaction with twitch.tv',
    version=VERSION,
    packages=['twitch'],
    license='GPLv3',
    long_description=open('README.md').read(),
    author='winlu',
    author_email='derwinlu+python-twitch@gmail.com',
    url='https://pypi.python.org/pypi/python-twitch',
)

