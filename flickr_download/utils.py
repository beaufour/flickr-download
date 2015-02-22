import os

from dateutil import parser


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


def get_foldername(photo, pattern):
    """
    Returns a partial folder path form parsing the photo time with the date format pattern.
    e.g. The the date Dec 24, 1973 and the pattern '%Y/%m/%d' would return '1973/12/24'
    @param photo: Flickr.Photo, the photo
    @param patter: Python date format pattern
    """
    info = photo.getInfo()
    taken = parser.parse(info['taken'])
    foldername = taken.strftime(pattern)
    return foldername
