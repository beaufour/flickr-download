import unittest

import os

from flickr_download.utils import get_full_path
from flickr_download.utils import get_filename
from flickr_download.utils import get_dirname


class TestPathSanitization(unittest.TestCase):
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

    def test_get_filename(self):
        self.assertEqual(get_filename('somename.jpg'), 'somename.jpg')
        self.assertEqual(get_filename(''.join(['and', os.path.sep, 'or.jpg'])),
                         'and_or.jpg')
        self.assertEqual(get_filename(''.join(['and*', os.path.sep, 'or?.jpg'])),
                         'and_or.jpg')
        self.assertEqual(get_filename('what*?\:/<>|what.jpg'), 'what_what.jpg')

    def test_get_dirname(self):
        self.assertEqual(get_dirname('somedirname'), 'somedirname')
        self.assertEqual(get_dirname(''.join(['and', os.path.sep, 'or-mypath'])),
                         'and_or-mypath')
        self.assertEqual(get_dirname(''.join(['and*', os.path.sep, 'o:r?'])),
                         'and_or')


if __name__ == '__main__':
    unittest.main()
