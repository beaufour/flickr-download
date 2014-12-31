import unittest

import os

from flickr_download.utils import get_full_path


class TestGetFullPath(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(get_full_path('moo', 'foo.jpg'),
                         ''.join(['moo', os.path.sep, 'foo.jpg']))

    def test_separators(self):
        self.assertEqual(get_full_path('moo/boo', 'foo.jpg'),
                         ''.join(['moo_boo', os.path.sep, 'foo.jpg']))
        self.assertEqual(get_full_path('moo', 'foo/faa.jpg'),
                         ''.join(['moo', os.path.sep, 'foo_faa.jpg']))
        self.assertEqual(get_full_path('moo/boo', 'foo/faa.jpg'),
                         ''.join(['moo_boo', os.path.sep, 'foo_faa.jpg']))


if __name__ == '__main__':
    unittest.main()
