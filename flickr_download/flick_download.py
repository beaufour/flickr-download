#!/usr/bin/env python
#
# Util to download a full Flickr set.
#
import argparse
import errno
import json
import logging
import os
import pickle
import signal
import sqlite3
import sys
import time
from pathlib import Path
from types import FrameType
from typing import Any, Dict, Optional, Tuple

import flickr_api as Flickr
import yaml
from flickr_api.cache import SimpleCache
from flickr_api.flickrerrors import FlickrError
from flickr_api.objects import Person, Photo, Photoset, Tag, Walker

from flickr_download.filename_handlers import (
    FilenameHandler,
    get_filename_handler,
    get_filename_handler_help,
)
from flickr_download.utils import get_dirname, get_full_path, get_photo_page, set_file_time

CONFIG_FILE = "~/.flickr_download"
OAUTH_TOKEN_FILE = "~/.flickr_token"
API_RETRIES = 5

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("flickr_download")
except ModuleNotFoundError:
    import importlib_metadata  # pyright: reportMissingImports=false

    __version__ = importlib_metadata.version("flickr_download")


def _init(key: str, secret: str, oauth: Optional[str]) -> bool:
    """Initialize API.

    @see: http://www.flickr.com/services/api/

    @param key: API key
    @param secret: API secret
    """
    Flickr.set_keys(key, secret)
    if not oauth:
        return True

    if os.path.exists(os.path.expanduser(OAUTH_TOKEN_FILE)):
        Flickr.set_auth_handler(os.path.expanduser(OAUTH_TOKEN_FILE))
        return True

    # Get new OAuth credentials
    auth = Flickr.auth.AuthHandler()  # creates the AuthHandler object
    perms = "read"  # set the required permissions
    url = auth.get_authorization_url(perms)
    print("")
    print("\nEnter the following url in a browser to authorize the application:")
    print(url)
    print("Copy and paste the <oauth_verifier> value from XML here and press return:")
    Flickr.set_auth_handler(auth)
    token = input()  # noqa: F821
    auth.set_verifier(token)
    auth.save(os.path.expanduser(OAUTH_TOKEN_FILE))
    print("OAuth token was saved, re-run script to use it.")
    return False


def _load_defaults() -> Dict[str, Any]:
    """Load default parameters from config file.

    @return: default parameters
    """
    filename = os.path.expanduser(CONFIG_FILE)
    logging.debug(f"Loading configuration from {filename}")
    try:
        with open(filename, "r") as cfile:
            vals = yaml.load(cfile.read(), Loader=yaml.FullLoader)
            return vals
    except yaml.YAMLError as ex:
        logging.warning(f"Could not parse configuration file: {ex}")
    except IOError as ex:
        if ex.errno != errno.ENOENT:
            logging.warning(f"Could not open configuration file: {ex}")
        else:
            logging.debug("No config file")

    return {}


def _get_metadata_db(dirname: str) -> sqlite3.Connection:
    conn = sqlite3.connect(Path(dirname) / ".metadata.db")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS downloads (photo_id text, size_label text, suffix text)"
    )
    return conn


def _get_size_and_suffix(photo: Photo, size_label: Optional[str]) -> Tuple[Optional[str], str]:
    photo_size_label: Optional[str] = size_label
    if photo.get("video"):
        pSizes = _get_photo_sizes(photo)
        if pSizes and "HD MP4" in pSizes:
            photo_size_label = "HD MP4"
        else:
            # Fall back for old 'short videos'. This might not exist, but
            # Photo.save() will croak on auto-detecting these old videos, so
            #  better not download than throwing an exception...
            photo_size_label = "Site MP4"
        suffix = ".mp4"
        return (photo_size_label, ".mp4")

    suffix = ".jpg"
    # Flickr returns JPEG, except for when downloading originals. The only way
    # to find the original type it seems is through the source filename. This
    # is not pretty...
    if photo_size_label == "Original" or not photo_size_label:
        pSizes = _get_photo_sizes(photo)
        meta = pSizes and pSizes.get("Original")
        if meta and meta["source"]:
            ext = os.path.splitext(meta["source"])[1]
            if ext:
                suffix = ext

    return (photo_size_label, suffix)


def download_set(
    set_id: str,
    get_filename: FilenameHandler,
    size_label: Optional[str] = None,
    skip_download: bool = False,
    save_json: bool = False,
    metadata_store: Optional[bool] = None,
) -> None:
    """Download the set with 'set_id' to the current directory.

    @param set_id: id of the photo set
    @param get_filename: function that creates a filename for the photo
    @param size_label: size to download (or None for largest available)
    @param skip_download: do not actually download the photo
    @param save_json: save photo info as .json file
    """
    pset = Flickr.Photoset(id=set_id)
    download_list(
        pset, pset.title, get_filename, size_label, skip_download, save_json, metadata_store
    )


def download_list(
    pset: Photoset,
    photos_title: str,
    get_filename: FilenameHandler,
    size_label: Optional[str],
    skip_download: bool = False,
    save_json: bool = False,
    metadata_store: Optional[bool] = None,
) -> None:
    """Download all the photos in the given photo list.

    @param pset: photo list to download
    @param photos_title: name of the photo list
    @param get_filename: function that creates a filename for the photo
    @param size_label: size to download (or None for largest available)
    @param skip_download: do not actually download the photo
    @param save_json: save photo info as .json file
    """

    photos = Walker(pset.getPhotos)

    suffix = " ({})".format(size_label) if size_label else ""

    logging.info(f"Downloading {photos_title}")
    dirname = get_dirname(photos_title)
    if not os.path.exists(dirname):
        try:
            os.mkdir(dirname)
        except OSError as err:
            if err.errno == errno.ENAMETOOLONG:
                logging.warning(f"WARNING: Truncating too long directory name: {dirname}")
                # Not the most fantastic handling here, but it is surprisingly hard to get the max
                # length in an OS-agnostic way... Assuming that most OSes can handle at least 200
                # chars...
                dirname = str(dirname)[:200]
                os.mkdir(dirname)
            else:
                raise

    conn = None
    if metadata_store:
        conn = _get_metadata_db(str(dirname))

    for photo in photos:
        do_download_photo(
            dirname,
            pset,
            photo,
            size_label,
            suffix,
            get_filename,
            skip_download,
            save_json,
            metadata_db=conn,
        )

    if conn:
        conn.close()


def do_download_photo(
    dirname: str,
    pset: Optional[Photoset],
    photo: Photo,
    size_label: Optional[str],
    suffix: Optional[str],
    get_filename: FilenameHandler,
    skip_download: bool = False,
    save_json: bool = False,
    metadata_db: Optional[sqlite3.Connection] = None,
) -> None:
    """Handle the downloading of a single photo.

    @param dirname: directory to download to
    @param pset: photo list to download
    @param photo: photo to download
    @param size_label: size to download (or None for largest available)
    @param suffix: optional suffix to add to file name
    @param get_filename: function that creates a filename for the photo
    @param skip_download: do not actually download the photo
    @param save_json: save photo info as .json file
    @param metadata_db: optional metadata database to record downloads in
    """
    orig_suffix = suffix or ""
    if metadata_db:
        if metadata_db.execute(
            "SELECT * FROM downloads WHERE photo_id = ? AND size_label = ? AND suffix = ?",
            (photo.id, size_label or "", orig_suffix),
        ).fetchone():
            logging.info(f"Skipping download of already downloaded photo with ID: {photo.id}")
            return

    fname = get_full_path(dirname, get_filename(pset, photo, suffix))
    jsonFname = fname + ".json"

    if not photo["loaded"]:
        # trying not trigger two calls to Photo.getInfo here, as it will if it was already loaded
        try:
            photo.load()
        except FlickrError:
            logging.info(f"Skipping {fname}, because cannot get info from Flickr")
            return

    if save_json:
        try:
            logging.info(f"Saving photo info: {jsonFname}")
            jsonFile = open(jsonFname, "w")
            jsonFile.write(json.dumps(photo, default=serialize_json, indent=2, sort_keys=True))
            jsonFile.close()
        except Exception:
            logging.warning("Trouble saving photo info:", sys.exc_info()[0])

    (photo_size_label, suffix) = _get_size_and_suffix(photo, size_label)
    if suffix:
        fname += suffix

    if os.path.exists(fname):
        # TODO: Ideally we should check for file size / md5 here
        # to handle failed downloads.
        logging.info(f"Skipping {fname}, as it exists already")
        return

    logging.info(f"Saving: {fname} ({get_photo_page(photo)})")
    if skip_download:
        return

    try:
        photo.save(fname, photo_size_label)
    except IOError as ex:
        logging.error(f"IO error saving photo: {ex}")
        return
    except FlickrError as ex:
        logging.error(f"Flickr error saving photo: {ex}")
        return

    # Set file times to when the photo was taken
    set_file_time(fname, photo["taken"])

    if metadata_db:
        metadata_db.execute(
            "INSERT INTO downloads VALUES (?, ?, ?)", (photo.id, size_label or "", orig_suffix)
        )
        metadata_db.commit()


def download_photo(
    photo_id: str,
    get_filename: FilenameHandler,
    size_label: Optional[str],
    skip_download: bool = False,
    save_json: bool = False,
) -> None:
    """Download one photo.

    @param photo_id: id of the photo
    @param get_filename: function that creates a filename for the photo
    @param size_label: size to download (or None for largest available)
    @param skip_download: do not actually download the photo
    @param save_json: save photo info as .json file
    """
    photo = Flickr.Photo(id=photo_id)
    suffix = " ({})".format(size_label) if size_label else ""
    do_download_photo(".", None, photo, size_label, suffix, get_filename, skip_download, save_json)


def find_user(userid: str) -> Person:
    if (
        userid.startswith("https://")
        or userid.startswith("www.flickr.com")
        or userid.startswith("flickr.com")
    ):
        user = Flickr.Person.findByUrl(userid)
    elif userid.find("@") > 0:
        user = Flickr.Person.findByEmail(userid)
    else:
        user = Flickr.Person.findByUserName(userid)
    return user


def download_user(
    username: str,
    get_filename: FilenameHandler,
    size_label: Optional[str],
    skip_download: bool = False,
    save_json: bool = False,
) -> None:
    """Download all the sets owned by the given user.

    @param username: username
    @param get_filename: function that creates a filename for the photo
    @param size_label: size to download (or None for largest available)
    @param skip_download: do not actually download the photo
    @param save_json: save photo info as .json file
    """
    user = find_user(username)
    photosets = Walker(user.getPhotosets)
    for photoset in photosets:
        download_set(photoset.id, get_filename, size_label, skip_download, save_json)


def download_user_photos(
    username: str,
    get_filename: FilenameHandler,
    size_label: Optional[str],
    skip_download: bool = False,
    save_json: bool = False,
    metadata_store: Optional[bool] = None,
) -> None:
    """Download all the photos owned by the given user.

    @param username: username
    @param get_filename: function that creates a filename for the photo
    @param size_label: size to download (or None for largest available)
    @param skip_download: do not actually download the photo
    @param save_json: save photo info as .json file
    """
    user = find_user(username)
    download_list(
        user, username, get_filename, size_label, skip_download, save_json, metadata_store
    )


def print_sets(username: str) -> None:
    """Print all sets for the given user.

    @param username: the name of the user
    """
    user = find_user(username)
    photosets = Walker(user.getPhotosets)
    for set in photosets:
        print(f"{set.id} - {set.title}")


def get_cache(path: str) -> SimpleCache:
    cache = SimpleCache(max_entries=20000, timeout=3600)
    cache_path = Path(path)
    if not cache_path.exists():
        return cache

    with cache_path.open("rb") as handle:
        db = pickle.load(handle)
        cache.storage = db["storage"]
        logging.debug(f"Cache loaded from: {cache_path.resolve()}")
        cache.expire_info = db["expire_info"]
        return cache


def save_cache(path: str, cache: SimpleCache) -> bool:
    db = {"storage": cache.storage, "expire_info": cache.expire_info}
    cache_path = Path(path)
    with cache_path.open("wb") as handle:
        pickle.dump(db, handle, protocol=pickle.HIGHEST_PROTOCOL)

    logging.debug(f"Cache saved to {cache_path.resolve()}")
    return True


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


def _get_photo_sizes(photo: Photo) -> Dict[str, Any]:
    for attempt in range(1, (API_RETRIES + 1)):
        try:
            return photo.getSizes()
        except FlickrError as ex:
            logging.warning(
                f"Flickr error getting photo size: {ex}, "
                f"attempt: #{attempt}, "
                f"attempts left: {(API_RETRIES - attempt)}"
            )
            time.sleep(1)
            if attempt >= API_RETRIES:
                raise

    return {}


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Downloads one or more Flickr photo sets.\n"
        "\n"
        "To use it you need to get your own Flickr API key here:\n"
        "https://www.flickr.com/services/api/misc.api_keys.html\n"
        "\n"
        "For more information see:\n"
        "https://github.com/beaufour/flickr-download\n"
        "\n"
        "You can store argument defaults in " + CONFIG_FILE + ". API keys for example:\n"
        "  api_key: .....\n"
        "  api_secret: ...\n",
        epilog="examples:\n"
        "  list all sets for a user:\n"
        "  > {app} -k <api_key> -s <api_secret> -l beaufour\n"
        "\n"
        "  download a given set:\n"
        "  > {app} -k <api_key> -s <api_secret> -d 72157622764287329\n"
        "\n"
        "  download a given set, keeping duplicate names:\n"
        "  > {app} -k <api_key> -s <api_secret> -d 72157622764287329 -n title_increment\n".format(
            app=sys.argv[0]
        ),
    )
    parser.add_argument("-k", "--api_key", type=str, help="Flickr API key")
    parser.add_argument("-s", "--api_secret", type=str, help="Flickr API secret")
    parser.add_argument("-t", "--user_auth", action="store_true", help="Enable user authentication")
    parser.add_argument("-l", "--list", type=str, metavar="USER", help="List photosets for a user")
    parser.add_argument(
        "-d", "--download", type=str, metavar="SET_ID", help="Download the given set"
    )
    parser.add_argument(
        "-p",
        "--download_user_photos",
        type=str,
        metavar="USERNAME",
        help="Download all photos for a given user",
    )
    parser.add_argument(
        "-u",
        "--download_user",
        type=str,
        metavar="USERNAME",
        help="Download all sets for a given user",
    )
    parser.add_argument(
        "-i",
        "--download_photo",
        type=str,
        metavar="PHOTO_ID",
        help="Download one specific photo",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=str,
        metavar="SIZE_LABEL",
        default=None,
        help="Quality of the picture",
    )
    parser.add_argument("-n", "--naming", type=str, metavar="NAMING_MODE", help="Photo naming mode")
    parser.add_argument("-m", "--list_naming", action="store_true", help="List naming modes")
    parser.add_argument(
        "-o",
        "--skip_download",
        action="store_true",
        help="Skip the actual download of the photo",
    )
    parser.add_argument(
        "-j",
        "--save_json",
        action="store_true",
        help="Save photo info like description and tags, one .json file per photo",
    )
    parser.add_argument(
        "-c",
        "--cache",
        type=str,
        metavar="CACHE_FILE",
        help="Cache results in CACHE_FILE (speed things up on large downloads in particular)",
    )
    parser.add_argument(
        "--metadata_store",
        action="store_true",
        help="Store information about downloads in a metadata file (helps with retrying downloads)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Turns on verbose logging")
    parser.add_argument("--version", action="store_true", help="Lists the version of the tool")
    parser.set_defaults(**_load_defaults())

    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cache = None
    if args.cache:
        cache = get_cache(args.cache)
        Flickr.enable_cache(cache)

        def signal_handler(signal: int, frame: Optional[FrameType]) -> Any:
            logging.debug(f"Hit signal handler for signal {signal}")
            save_cache(args.cache, cache)
            sys.exit(signal)

        signal.signal(signal.SIGINT, signal_handler)

        logging.info("Caching is enabled")

    if args.list_naming:
        print(get_filename_handler_help())
        return 1

    if not args.api_key or not args.api_secret:
        print(
            'You need to pass in both "api_key" and "api_secret" arguments',
            file=sys.stderr,
        )
        return 1

    ret = _init(args.api_key, args.api_secret, args.user_auth)
    if not ret:
        return 1

    if args.list:
        print_sets(args.list)
        if cache:
            save_cache(args.cache, cache)
        return 0

    if args.skip_download:
        logging.info("Will skip actual downloading of files")

    if args.save_json:
        logging.info("Will save photo info in .json file with same basename as photo")

    if args.download or args.download_user or args.download_user_photos or args.download_photo:
        try:
            get_filename = get_filename_handler(args.naming)
            if args.download:
                download_set(
                    args.download,
                    get_filename,
                    args.quality,
                    args.skip_download,
                    args.save_json,
                    args.metadata_store,
                )
            elif args.download_user:
                download_user(
                    args.download_user,
                    get_filename,
                    args.quality,
                    args.skip_download,
                    args.save_json,
                )
            elif args.download_photo:
                download_photo(
                    args.download_photo,
                    get_filename,
                    args.quality,
                    args.skip_download,
                    args.save_json,
                )
            else:
                download_user_photos(
                    args.download_user_photos,
                    get_filename,
                    args.quality,
                    args.skip_download,
                    args.save_json,
                    args.metadata_store,
                )
        except KeyboardInterrupt:
            print(
                "Forcefully aborting. Last photo download might be partial :(",
                file=sys.stderr,
            )
        except Exception:
            if cache:
                save_cache(args.cache, cache)
            raise

        if cache:
            save_cache(args.cache, cache)
        return 0

    print("ERROR: Must pass either --list or --download\n", file=sys.stderr)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
