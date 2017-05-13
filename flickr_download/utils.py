import os
from timeit import default_timer


def sanitize_filepath(fname):
    """
    Ensure that a file path does not have path name separators in it.

    @param fname: str, path to sanitize
    @return: str, sanitized path
    """
    ret = fname.replace(os.path.sep, '_')
    if os.path.altsep:
        ret = ret.replace(os.path.altsep, '_')
    return ret


def get_full_path(pset, photo):
    """
    Assemble a full path from the photoset and photo titles

    @param pset: str, photo set name
    @param photo: str, photo name
    @return: str, full sanitized path
    """
    return os.path.join(sanitize_filepath(pset), sanitize_filepath(photo))


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
            print('--> time: {} = {:0.02f}ms'.format(self.msg, self.elapsed))


def get_photo_page(photo_info):
    """
    Get the photo page URL from a photo info object
    """
    ret = ''
    if photo_info.get('urls') and photo_info['urls'].get('url'):
        for url in photo_info['urls']['url']:
            if url.get('type') == 'photopage':
                ret = url.get('text')
    return ret
