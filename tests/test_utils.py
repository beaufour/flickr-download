import os

from flickr_download.utils import get_dirname, get_filename, get_full_path


def test_simple():
    assert get_full_path("moo", "foo.jpg") == "".join(["moo", os.path.sep, "foo.jpg"])


def test_separators():
    assert get_full_path("moo/boo", "foo.jpg") == "".join(["moo_boo", os.path.sep, "foo.jpg"])
    assert get_full_path("moo", "foo/faa.jpg") == "".join(["moo", os.path.sep, "foo_faa.jpg"])
    assert get_full_path("moo/boo", "foo/faa.jpg") == "".join(
        ["moo_boo", os.path.sep, "foo_faa.jpg"]
    )


def test_get_filename():
    assert get_filename("somename.jpg") == "somename.jpg"
    assert get_filename("".join(["and", os.path.sep, "or.jpg"])) == "and_or.jpg"
    assert get_filename("".join(["and*", os.path.sep, "or?.jpg"])) == "and_or.jpg"
    assert get_filename("what*?\\:/<>|what.jpg") == "what_what.jpg"


def test_get_dirname():
    assert get_dirname("somedirname") == "somedirname"
    assert get_dirname("".join(["and", os.path.sep, "or-mypath"])) == "and_or-mypath"
    assert get_dirname("".join(["and*", os.path.sep, "o:r?"])) == "and_or"
