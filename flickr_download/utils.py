"""Misc utility functions."""
from __future__ import annotations

import logging
import os
import pickle
import signal
import sys
import time
from pathlib import Path
from types import FrameType
from typing import Any, Optional

import flickr_api as Flickr
from dateutil import parser
from flickr_api.cache import SimpleCache
from flickr_api.objects import Person, Photo, Tag
from pathvalidate import sanitize_filename, sanitize_filepath


def get_cache(path: str) -> SimpleCache:
    """Loads the cache from disk, or returns an empty one if not found."""
    cache = SimpleCache(max_entries=20000, timeout=3600)
    cache_path = Path(path)
    if not cache_path.exists():
        return cache

    with cache_path.open("rb") as handle:
        database = pickle.load(handle)
        cache.storage = database["storage"]
        logging.debug("Cache loaded from: %s", cache_path.resolve())
        cache.expire_info = database["expire_info"]
        return cache


def save_cache(path: str, cache: SimpleCache) -> bool:
    """Saves the cache to disk."""
    database = {"storage": cache.storage, "expire_info": cache.expire_info}
    cache_path = Path(path)
    with cache_path.open("wb") as handle:
        pickle.dump(database, handle, protocol=pickle.HIGHEST_PROTOCOL)

    logging.debug("Cache saved to %s", cache_path.resolve())
    return True


def init_cache(path: str) -> SimpleCache:
    """Initialize the cache and install a signal handler to automatically save
    it."""
    cache = get_cache(path)
    Flickr.enable_cache(cache)

    def signal_handler(sig: int, _: Optional[FrameType]) -> Any:
        logging.debug("Hit signal handler for signal %s", sig)
        save_cache(path, cache)
        sys.exit(sig)

    signal.signal(signal.SIGINT, signal_handler)

    logging.info("Caching is enabled")

    return cache


def serialize_json(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, Person):
        return obj.username

    if isinstance(obj, Tag):
        return obj.text
        # return obj.id +"_"+ obj.text

    try:
        ret = obj.__dict__
    except Exception:
        ret = obj
    return ret


def replace_path_sep(name: str) -> str:
    """Replaces the path separator(s) with an underscore.

    :param name: file or dir name
    :returns: new name
    """
    ret = name.replace(os.path.sep, "_")
    if os.path.altsep:
        ret = ret.replace(os.path.altsep, "_")

    return ret


def get_filename(photo: str) -> str:
    """Get a file name for a photo.

    :param photoset: name of photo
    :returns: file name
    """
    return str(sanitize_filename(replace_path_sep(photo)))


def get_dirname(photoset: str) -> str:
    """Get a directory name for a photo set.

    :param photoset: name of photoset
    :returns: directory / path name
    """
    return str(sanitize_filepath(replace_path_sep(photoset)))


def get_full_path(pset: str, photo: str) -> str:
    """Assemble a full path from the photoset and photo titles.

    :param pset: photo set name
    :param photo: photo name
    :returns: full sanitized path
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
