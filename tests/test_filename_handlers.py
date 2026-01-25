from unittest.mock import Mock

from flickr_api.objects import Photo, Photoset

from flickr_download.filename_handlers import (
    get_filename_handler,
    get_filename_handler_help,
    get_filename_handler_names,
)


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


def test_id_and_title() -> None:
    """Test id_and_title handler."""
    pset = Mock(Photoset, title="Some Set", id=999)
    photo = Mock(Photo, title="Some Photo", id=123)

    fn = get_filename_handler("id_and_title")
    assert fn(pset, photo, "") == "123-Some Photo"


def test_id_and_title_empty_title() -> None:
    """Test id_and_title handler with empty title."""
    pset = Mock(Photoset, title="Some Set", id=999)
    photo = Mock(Photo, title="", id=123)

    fn = get_filename_handler("id_and_title")
    assert fn(pset, photo, "") == "123"


def test_get_filename_handler_names() -> None:
    """Test get_filename_handler_names returns all handlers."""
    names = get_filename_handler_names()
    assert "title" in names
    assert "id" in names
    assert "title_and_id" in names
    assert "id_and_title" in names
    assert "title_increment" in names


def test_get_filename_handler_help() -> None:
    """Test get_filename_handler_help returns help text."""
    help_text = get_filename_handler_help()
    assert "title" in help_text
    assert "id" in help_text


def test_get_filename_handler_default() -> None:
    """Test get_filename_handler returns default for None."""
    fn = get_filename_handler(None)  # type: ignore[arg-type]
    pset = Mock(Photoset, title="Some Set", id=999)
    photo = Mock(Photo, title="Test", id=123)
    # Default should be title_increment which returns "Test" for first occurrence
    result = fn(pset, photo, "")
    assert result == "Test"
