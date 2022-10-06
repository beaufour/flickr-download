import os
import sys
from unittest.mock import patch

import pytest
from flickr_download.utils import get_dirname, get_filename, get_full_path, set_file_time


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
