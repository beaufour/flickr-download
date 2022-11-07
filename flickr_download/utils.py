"""Misc utility functions."""
from __future__ import annotations

import logging
import os
import time

from dateutil import parser
from flickr_api.objects import Photo
from pathvalidate import sanitize_filename, sanitize_filepath


def replace_path_sep(name: str) -> str:
    """Replaces the path separator(s) with an underscore.

    @param name: file or dir name
    @return: new name
    """
    ret = name.replace(os.path.sep, "_")
    if os.path.altsep:
        ret = ret.replace(os.path.altsep, "_")

    return ret


def get_filename(photo: str) -> str:
    """Get a file name for a photo.

    @param photoset: name of photo
    @return: file name
    """
    return str(sanitize_filename(replace_path_sep(photo)))


def get_dirname(photoset: str) -> str:
    """Get a directory name for a photo set.

    @param photoset: name of photoset
    @return: directory / path name
    """
    return str(sanitize_filepath(replace_path_sep(photoset)))


def get_full_path(pset: str, photo: str) -> str:
    """Assemble a full path from the photoset and photo titles.

    @param pset: photo set name
    @param photo: photo name
    @return: full sanitized path
    """
    return os.path.join(get_dirname(pset), get_filename(photo))


def get_photo_page(photo_info: Photo) -> str:
    """Get the photo page URL from a photo info object."""
    if photo_info.get("urls") and photo_info["urls"].get("url"):
        for url in photo_info["urls"]["url"]:
            if url.get("type") == "photopage":
                return url.get("text")

    return ""


def set_file_time(fname: str, taken_str: str) -> None:
    """Set the file time to the time when the photo was taken."""
    taken = parser.parse(taken_str)
    try:
        taken_unix = time.mktime(taken.timetuple())
    except OverflowError:
        logging.warning("Cannot set file time to: %s", taken)
        return

    os.utime(fname, (taken_unix, taken_unix))
