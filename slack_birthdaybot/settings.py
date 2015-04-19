from os import path
import sys


API_KEY = None

NOTIFIER_CHANNEL = "general"

BASE_DIR = path.dirname(path.dirname(__file__))

DATABASE = path.join(BASE_DIR, "database.db")

USERNAME = "Birthday Bot"

DEBUG = True


try:
    from settings_local import *
except ImportError:
    pass
