"""Defines a set of functions that handle naming of the downloaded files."""

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from flickr_api.objects import Photo, Photoset

from flickr_download.utils import get_filename

# The default handler if none is specified
DEFAULT_HANDLER = "title_increment"

FilenameHandler = Callable[[Optional[Photoset], Photo, Optional[str]], str]


def _get_short_docstring(docstring: Optional[str]) -> Optional[str]:
    """Given a docstring return the first sentence of it.

    :param: docstring: the docstring to parse
    :returns: the short docstring
    """
    return docstring.split(".")[0].strip() if docstring else None


def title(pset: Optional[Photoset], photo: Photo, suffix: Optional[str]) -> str:
    """Name file after title (falls back to photo id).

    :param pset: the photoset
    :param photo: the photo
    :param suffix: optional suffix
    :returns: the filename
    """
    if not photo.title:
        return idd(pset, photo, suffix)

    return get_filename(f"{photo.title}{suffix}")


def idd(_: Optional[Photoset], photo: Photo, suffix: Optional[str]) -> str:
    """Name file after photo id.

    :param pset: the photoset
    :param photo: the photo
    :param suffix: optional suffix
    :returns: the filename
    """
    return f"{photo.id}{suffix}"


def title_and_id(pset: Optional[Photoset], photo: Photo, suffix: Optional[str]) -> str:
    """Name file after title and photo id.

    :param pset: the photoset
    :param photo: the photo
    :param suffix: optional suffix
    :returns: the filename
    """
    if not photo.title:
        return idd(pset, photo, suffix)

    return get_filename(f"{photo.title}-{photo.id}{suffix}")


def id_and_title(pset: Optional[Photoset], photo: Photo, suffix: Optional[str]) -> str:
    """Name file after photo id and title.

    :param pset: the photoset
    :param photo: the photo
    :param suffix: optional suffix
    :returns: the filename
    """
    if not photo.title:
        return idd(pset, photo, suffix)

    return get_filename(f"{photo.id}-{photo.title}{suffix}")


# Photoset -> filename index for title_increment function duplicate tracking
INCREMENT_INDEX: Dict[Any, Any] = defaultdict(lambda: defaultdict(int))


def title_increment(pset: Optional[Photoset], photo: Photo, suffix: Optional[str]) -> str:
    """Name file after photo title, but add an incrementing counter on
    duplicates.

    :param pset: the photoset
    :param photo: the photo
    :param suffix: optional suffix
    :returns: the filename
    """
    if not photo.title:
        return idd(pset, photo, suffix)

    extra = ""
    index = pset.id if pset else "1"
    photo_index = INCREMENT_INDEX[index][photo.title]
    if photo_index:
        extra = f"({photo_index})"
    INCREMENT_INDEX[index][photo.title] += 1
    return get_filename(f"{photo.title}{suffix}{extra}")


HANDLERS = {
    "title": title,
    "id": idd,
    "title_and_id": title_and_id,
    "id_and_title": id_and_title,
    "title_increment": title_increment,
}


def get_filename_handler(name: str) -> FilenameHandler:
    """Returns the given filename handler as a function.

    :param name: name of the handler to return
    :returns: handler
    """
    return HANDLERS[name or DEFAULT_HANDLER]


def get_filename_handler_help() -> str:
    """Returns a description of each handler to be used for help output.

    :returns: help text
    """
    ret = []
    HANDLERS.items()
    for name, func in HANDLERS.items():
        default = " (DEFAULT)" if name == DEFAULT_HANDLER else ""
        ret.append(f"  {name} - {_get_short_docstring(func.__doc__)}{default}")
    return "Naming modes:\n" + "\n".join(ret)


def get_filename_handler_names() -> List[str]:
    """Returns list of filename handlers."""
    return list(HANDLERS.keys())
