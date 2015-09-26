import logging
import os

logging.basicConfig(level=logging.DEBUG)

ci = False
if os.environ.get('CI') == 'true':
    ci = True
