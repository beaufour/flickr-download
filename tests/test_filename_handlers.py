from unittest.mock import Mock

from flickr_api.objects import Photo, Photoset
from flickr_download.filename_handlers import get_filename_handler


class TestFilenameHandlers:
    def setup_method(self) -> None:
        self._pset = Mock(Photoset, title="Some Set", id=999)
        self._photo = Mock(Photo, title="Some Photo", id=123)
        self._suffix = ""

    def teardown_method(self) -> None:
        fn = get_filename_handler("title")
        assert fn(self._pset, self._photo, self._suffix) == "Some Photo"

    def test_title_empty_title(self) -> None:
        photo = Mock(Photo, title="", id=192)
        fn = get_filename_handler("title")
        assert fn(self._pset, photo, self._suffix) == "192"

    def test_title_and_id(self) -> None:
        fn = get_filename_handler("title_and_id")
        assert fn(self._pset, self._photo, self._suffix) == "Some Photo-123"

    def test_title_and_id_empty_title(self) -> None:
        photo = Mock(Photo, title="", id=1389)
        fn = get_filename_handler("title_and_id")
        assert fn(self._pset, photo, self._suffix) == "1389"

    def test_id(self) -> None:
        fn = get_filename_handler("id")
        assert fn(self._pset, self._photo, self._suffix) == "123"

    def test_title_increment(self) -> None:
        fn = get_filename_handler("title_increment")
        # Ensure increment on same title
        assert fn(self._pset, self._photo, self._suffix) == "Some Photo"
        assert fn(self._pset, self._photo, self._suffix) == "Some Photo(1)"

        # Ensure no increment on different title
        photo2 = Mock(Photo, title="Some Other Photo", id=124)
        assert fn(self._pset, photo2, self._suffix) == "Some Other Photo"

        # Ensure no increment on same title, but different set
        pset2 = Mock(Photoset, title="Some Other Set", id=1000)
        assert fn(pset2, self._photo, self._suffix) == "Some Photo"

    def test_title_increment_empty_title(self) -> None:
        photo = Mock(Photo, title="", id=175)
        fn = get_filename_handler("title_increment")
        assert fn(self._pset, photo, self._suffix) == "175"

    def test_valid_path(self) -> None:
        photo = Mock(Photo, title='fi:l*e/p"a?t>h|', id=199)

        fn = get_filename_handler("title")
        assert fn(self._pset, photo, self._suffix) == "file_path"

        fn = get_filename_handler("title_increment")
        assert fn(self._pset, photo, self._suffix) == "file_path"

        fn = get_filename_handler("title_and_id")
        assert fn(self._pset, photo, self._suffix) == "file_path-199"
