import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from flickr_api.objects import Person, Tag
from flickr_download.utils import (
    get_cache,
    get_dirname,
    get_filename,
    get_full_path,
    save_cache,
    serialize_json,
    set_file_time,
)


def test_simple() -> None:
    assert get_full_path("moo", "foo.jpg") == "".join(["moo", os.path.sep, "foo.jpg"])


def test_separators() -> None:
    assert get_full_path("moo/boo", "foo.jpg") == "".join(["moo_boo", os.path.sep, "foo.jpg"])
    assert get_full_path("moo", "foo/faa.jpg") == "".join(["moo", os.path.sep, "foo_faa.jpg"])
    assert get_full_path("moo/boo", "foo/faa.jpg") == "".join(
        ["moo_boo", os.path.sep, "foo_faa.jpg"]
    )


def test_get_filename() -> None:
    assert get_filename("somename.jpg") == "somename.jpg"
    assert get_filename("".join(["and", os.path.sep, "or.jpg"])) == "and_or.jpg"
    assert get_filename("".join(["and*", os.path.sep, "or?.jpg"])) == "and_or.jpg"
    assert get_filename("what*?\\:/<>|what.jpg") == "what_what.jpg"


def test_get_dirname() -> None:
    assert get_dirname("somedirname") == "somedirname"
    assert get_dirname("".join(["and", os.path.sep, "or-mypath"])) == "and_or-mypath"
    assert get_dirname("".join(["and*", os.path.sep, "o:r?"])) == "and_or"


def test_set_file_time() -> None:
    with patch("os.utime") as mocked:
        set_file_time("test_file_delete", "2020-03-05 08:00:00")
        mocked.assert_called_once()


@pytest.mark.skipif(sys.platform != "darwin", reason="only seen fail on Mac so far")
def test_set_file_time_overflow() -> None:
    with patch("os.utime") as mocked:
        # Assuming that a date from 1212 cannot be represented properly, no
        # matter the OS.
        set_file_time("test_file_delete", "1212-01-01 00:00:00")
        mocked.assert_not_called()


def test_get_cache_no_file() -> None:
    """get_cache returns empty cache when file doesn't exist."""
    cache = get_cache("/nonexistent/path/cache.pkl")
    assert cache.storage == {}


def test_save_and_get_cache() -> None:
    """save_cache and get_cache round-trip works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = str(Path(tmpdir) / "test_cache.pkl")

        # Get fresh cache and add data
        cache = get_cache(cache_path)
        cache.storage["test_key"] = "test_value"
        cache.expire_info["test_key"] = 9999999999

        # Save and reload
        save_cache(cache_path, cache)
        loaded_cache = get_cache(cache_path)

        assert loaded_cache.storage["test_key"] == "test_value"


def test_serialize_json_person() -> None:
    """serialize_json handles Person objects."""
    person = Mock(spec=Person)
    person.username = "testuser"
    result = serialize_json(person)
    assert result == "testuser"


def test_serialize_json_tag() -> None:
    """serialize_json handles Tag objects."""
    tag = Mock(spec=Tag)
    tag.text = "testtag"
    result = serialize_json(tag)
    assert result == "testtag"


def test_serialize_json_dict() -> None:
    """serialize_json handles objects with __dict__."""

    class CustomObj:
        def __init__(self) -> None:
            self.foo = "bar"

    result = serialize_json(CustomObj())
    assert result == {"foo": "bar"}


def test_serialize_json_primitive() -> None:
    """serialize_json passes through primitives."""
    assert serialize_json("string") == "string"
    assert serialize_json(123) == 123
