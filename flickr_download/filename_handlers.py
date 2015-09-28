"""
Defines a set of functions that handle naming of the downloaded files.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from collections import defaultdict

DEFAULT_HANDLER = 'title'
"""The default handler if none is specified"""


def _get_short_docstring(docstring):
    """
    Given a docstring return the first sentence of it.

    @param: docstring: str, the docstring to parsde
    @return: str, the short docstring
    """
    return docstring.split('.')[0].strip()


def title(pset, photo, suffix):
    """
    Name file after title (falls back to photo id).

    @param pset: Flickr.Photoset, the photoset
    @param photo: Flickr.Photo, the photo
    @param suffice: str, optional suffix
    @return: str, the filename
    """
    if not photo.title:
        return idd(pset, photo, suffix)

    return '{0}{1}.jpg'.format(photo.title, suffix)


def idd(pset, photo, suffix):
    """
    Name file after photo id.

    @param pset: Flickr.Photoset, the photoset
    @param photo: Flickr.Photo, the photo
    @param suffice: str, optional suffix
    @return: str, the filename
    """
    return '{0}{1}.jpg'.format(photo.id, suffix)


def title_and_id(pset, photo, suffix):
    """
    Name file after title and photo id.

    @param pset: Flickr.Photoset, the photoset
    @param photo: Flickr.Photo, the photo
    @param suffice: str, optional suffix
    @return: str, the filename
    """
    if not photo.title:
        return idd(pset, photo, suffix)

    return '{0}-{1}{2}.jpg'.format(photo.title, photo.id, suffix)


INCREMENT_INDEX = defaultdict(lambda: defaultdict(int))
"""Photoset -> filename index for title_increment function duplicate tracking"""


def title_increment(pset, photo, suffix):
    """
    Name file after photo title, but add an incrementing counter on duplicates.

    @param pset: Flickr.Photoset, the photoset
    @param photo: Flickr.Photo, the photo
    @param suffice: str, optional suffix
    @return: str, the filename
    """
    if not photo.title:
        return idd(pset, photo, suffix)

    extra = ''
    photo_index = INCREMENT_INDEX[pset.id][photo.title]
    if photo_index:
        extra = '({0})'.format(photo_index)
    INCREMENT_INDEX[pset.id][photo.title] += 1
    return '{0}{1}{2}.jpg'.format(photo.title, suffix, extra)


HANDLERS = {
    'title': title,
    'id': idd,
    'title_and_id': title_and_id,
    'title_increment': title_increment,
}


def get_filename_handler(name):
    """
    Returns the given filename handler as a function
    @param name: str, name of the handler to return
    @return: Function, handler
    """
    return HANDLERS[name or DEFAULT_HANDLER]


def get_filename_handler_help():
    """
    Returns a description of each handler to be used for help output.

    @return: str, help text
    """
    ret = []
    for name, func in HANDLERS.iteritems():
        ret.append('  {handler} - {doc}{default}'
                   .format(handler=name,
                           doc=_get_short_docstring(func.__doc__),
                           default=(' (DEFAULT)' if name == DEFAULT_HANDLER else '')))
    return 'Naming modes:\n' + '\n'.join(ret)
