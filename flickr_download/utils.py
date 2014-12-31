import os


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
