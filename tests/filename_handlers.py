import unittest

from attrdict import AttrDict

from flickr_download.filename_handlers import get_filename_handler


class TestFilenameHandlers(unittest.TestCase):
    def setUp(self):
        self._pset = AttrDict({'title': 'Some Set', 'id': 999})
        self._photo = AttrDict({'title': 'Some Photo', 'id': 123})
        self._suffix = ""

    def test_title(self):
        fn = get_filename_handler('title')
        self.assertEqual(fn(self._pset, self._photo, self._suffix),
                         'Some Photo')

    def test_title_empty_title(self):
        photo = AttrDict({'title': '', 'id': 192})
        fn = get_filename_handler('title')
        self.assertEqual(fn(self._pset, photo, self._suffix),
                         '192')

    def test_title_and_id(self):
        fn = get_filename_handler('title_and_id')
        self.assertEqual(fn(self._pset, self._photo, self._suffix),
                         'Some Photo-123')

    def test_title_and_id_empty_title(self):
        photo = AttrDict({'title': '', 'id': 1389})
        fn = get_filename_handler('title_and_id')
        self.assertEqual(fn(self._pset, photo, self._suffix),
                         '1389')

    def test_id(self):
        fn = get_filename_handler('id')
        self.assertEqual(fn(self._pset, self._photo, self._suffix),
                         '123')

    def test_title_increment(self):
        fn = get_filename_handler('title_increment')
        # Ensure increment on same title
        self.assertEqual(fn(self._pset, self._photo, self._suffix),
                         'Some Photo')
        self.assertEqual(fn(self._pset, self._photo, self._suffix),
                         'Some Photo(1)')

        # Ensure no increment on different title
        photo2 = AttrDict({'title': 'Some Other Photo', 'id': 124})
        self.assertEqual(fn(self._pset, photo2, self._suffix),
                         'Some Other Photo')

        # Ensure no increment on same title, but different set
        pset2 = AttrDict({'title': 'Some Other Set', 'id': 1000})
        self.assertEqual(fn(pset2, self._photo, self._suffix),
                         'Some Photo')

    def test_title_increment_empty_title(self):
        photo = AttrDict({'title': '', 'id': 175})
        fn = get_filename_handler('title_increment')
        self.assertEqual(fn(self._pset, photo, self._suffix),
                         '175')

if __name__ == '__main__':
    unittest.main()
