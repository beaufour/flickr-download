import os.path
import unittest2


def get_tests():
    start_dir = os.path.dirname(__file__)
    return unittest2.TestLoader().discover(start_dir, pattern="*.py")
