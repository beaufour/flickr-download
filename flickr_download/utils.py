import os
from timeit import default_timer

from pathvalidate import sanitize_filename, sanitize_filepath


def replace_path_sep(name):
    """
    Replaces the path separator(s) with an underscore.

    @param name: str, file or dir name
    @return: str, new name
    """
    ret = name.replace(os.path.sep, "_")
    if os.path.altsep:
        ret = ret.replace(os.path.altsep, "_")

    return ret


def get_filename(photo):
    """
    Get a file name for a photo

    @param photoset: str, name of photo
    @return: str, file name
    """
    return sanitize_filename(replace_path_sep(photo))


def get_dirname(photoset):
    """
    Get a directory name for a photo set

    @param photoset: str, name of photoset
    @return: str, directory / path name
    """
    return sanitize_filepath(replace_path_sep(photoset))


def get_full_path(pset, photo):
    """
    Assemble a full path from the photoset and photo titles

    @param pset: str, photo set name
    @param photo: str, photo name
    @return: str, full sanitized path
    """
    return os.path.join(get_dirname(pset), get_filename(photo))


class Timer(object):
    """
    Helper context manager to time pieces of code.
    """

    def __init__(self, msg, verbose=False):
        self.msg = msg
        self.verbose = verbose
        self.timer = default_timer

    def __enter__(self):
        self.start = self.timer()
        return self

    def __exit__(self, *args):
        end = self.timer()
        self.elapsed_secs = end - self.start
        self.elapsed = self.elapsed_secs * 1000
        if self.verbose:
            print("--> time: {} = {:0.02f}ms".format(self.msg, self.elapsed))


def get_photo_page(photo_info):
    """
    Get the photo page URL from a photo info object
    """
    ret = ""
    if photo_info.get("urls") and photo_info["urls"].get("url"):
        for url in photo_info["urls"]["url"]:
            if url.get("type") == "photopage":
                ret = url.get("text")
    return ret
