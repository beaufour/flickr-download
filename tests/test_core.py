from unittest.mock import Mock

from flickr_api.objects import Photo
from flickr_download.flick_download import _get_size_and_suffix


def tests_get_size_and_suffix_video() -> None:
    # Fallback when no video formats
    photo = Mock(Photo)
    photo.getSizes.return_value = None
    # The code does a .get("video")... slightly ugly mocking.
    photo.get.return_value = True
    (size, suffix) = _get_size_and_suffix(photo, None)
    assert size == "Site MP4"
    assert suffix == ".mp4"

    # The standard video format
    photo.getSizes.return_value = {"HD MP4": {}}
    (size, suffix) = _get_size_and_suffix(photo, None)
    assert size == "HD MP4"
    assert suffix == ".mp4"


def tests_get_size_and_suffix_extension() -> None:
    # Source is there
    photo = Mock(Photo)
    photo.getSizes.return_value = {"Original": {"source": "some_file.png"}}
    photo.get.return_value = False
    (size, suffix) = _get_size_and_suffix(photo, None)
    assert size is None
    assert suffix == ".png"

    # Source is not there
    photo = Mock(Photo)
    photo.getSizes.return_value = {}
    photo.get.return_value = False
    (size, suffix) = _get_size_and_suffix(photo, None)
    assert size is None
    assert suffix == ".jpg"

    # Different source is there
    photo = Mock(Photo)
    photo.getSizes.return_value = {"Large": {"source": "some_file.png"}}
    photo.get.return_value = False
    (size, suffix) = _get_size_and_suffix(photo, None)
    assert size is None
    assert suffix == ".jpg"

    # Source is there, size is passed in
    photo = Mock(Photo)
    photo.getSizes.return_value = {"Original": {"source": "some_file.jpeg"}}
    photo.get.return_value = False
    (size, suffix) = _get_size_and_suffix(photo, "Original")
    assert size == "Original"
    assert suffix == ".jpeg"
