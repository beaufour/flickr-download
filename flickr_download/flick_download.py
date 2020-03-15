#!/usr/bin/env python
#
# Util to download a full Flickr set.
#

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import errno
import json
import logging
import os
import sys
import time

import flickr_api as Flickr
import yaml
from dateutil import parser
from flickr_api.flickrerrors import FlickrAPIError, FlickrError
from flickr_api.objects import Person, Tag

from flickr_download.filename_handlers import (get_filename_handler,
                                               get_filename_handler_help)
from flickr_download.utils import (Timer, get_dirname, get_full_path,
                                   get_photo_page)

CONFIG_FILE = "~/.flickr_download"
OAUTH_TOKEN_FILE = "~/.flickr_token"
API_RETRIES = 5


def _init(key, secret, oauth):
    """
    Initialize API.

    @see: http://www.flickr.com/services/api/

    @param key: str, API key
    @param secret: str, API secret
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
    print
    print("\nEnter the following url in a browser to authorize the application:")
    print(url)
    print("Copy and paste the <oauth_verifier> value from XML here and press return:")
    Flickr.set_auth_handler(auth)
    token = raw_input()  # noqa: F821
    auth.set_verifier(token)
    auth.save(os.path.expanduser(OAUTH_TOKEN_FILE))
    print("OAuth token was saved, re-run script to use it.")
    return False


def _load_defaults():
    """
    Load default parameters from config file

    @return: dict, default parameters
    """
    filename = os.path.expanduser(CONFIG_FILE)
    logging.debug("Loading configuration from {}".format(filename))
    try:
        with open(filename, "r") as cfile:
            vals = yaml.load(cfile.read(), Loader=yaml.FullLoader)
            return vals
    except yaml.YAMLError as ex:
        logging.warning("Could not parse configuration file: {}".format(ex))
    except IOError as ex:
        if ex.errno != errno.ENOENT:
            logging.warning("Could not open configuration file: {}".format(ex))
        else:
            logging.debug("No config file")

    return {}


def download_set(
    set_id, get_filename, size_label=None, skip_download=False, save_json=False
):
    """
    Download the set with 'set_id' to the current directory.

    @param set_id: str, id of the photo set
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    @param skip_download: bool, do not actually download the photo
    @param save_json: bool, save photo info as .json file
    """
    pset = Flickr.Photoset(id=set_id)
    download_list(pset, pset.title, get_filename, size_label, skip_download, save_json)


def download_list(
    pset, photos_title, get_filename, size_label, skip_download=False, save_json=False
):
    """
    Download all the photos in the given photo list

    @param pset: FlickrList, photo list to download
    @param photos_title: str, name of the photo list
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    @param skip_download: bool, do not actually download the photo
    @param save_json: bool, save photo info as .json file
    """
    with Timer("getPhotos()"):
        photos = pset.getPhotos()
    pagenum = 2
    while True:
        try:
            if pagenum > photos.info.pages:
                break
            with Timer("getPhotos()"):
                page = pset.getPhotos(page=pagenum)
            photos.extend(page)
            pagenum += 1
        except FlickrAPIError as ex:
            if ex.code == 1:
                break
            raise

    suffix = " ({})".format(size_label) if size_label else ""

    dirname = get_dirname(photos_title)
    if not os.path.exists(dirname):
        try:
            os.mkdir(dirname)
        except OSError as err:
            if err.errno == errno.ENAMETOOLONG:
                print("WARNING: Truncating too long directory name: {}".format(dirname))
                # Not the most fantastic handling here, but it is surprisingly hard to get the max
                # length in an OS-agnostic way... Assuming that most OSes can handle at least 200
                # chars...
                dirname = dirname[:200]
                os.mkdir(dirname)
            else:
                raise

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
        )


def do_download_photo(
    dirname,
    pset,
    photo,
    size_label,
    suffix,
    get_filename,
    skip_download=False,
    save_json=False,
):
    """
    Handle the downloading of a single photo

    @param dirname: str, directory to download to
    @param pset: FlickrList, photo list to download
    @param photo: FlickrPhoto, photo to download
    @param size_label: str|None, size to download (or None for largest available)
    @param suffix: str|None, optional suffix to add to file name
    @param get_filename: Function, function that creates a filename for the photo
    @param skip_download: bool, do not actually download the photo
    @param save_json: bool, save photo info as .json file
    """
    fname = get_full_path(dirname, get_filename(pset, photo, suffix))
    jsonFname = fname + ".json"

    pInfo = {}
    try:
        with Timer("getInfo()"):
            pInfo = photo.getInfo()
    except FlickrError:
        print("Skipping {0}, because cannot get info from Flickr".format(fname))
        return

    if save_json:
        try:
            print("Saving photo info: {}".format(jsonFname))
            jsonFile = open(jsonFname, "w")
            jsonFile.write(
                json.dumps(pInfo, default=serialize_json, indent=2, sort_keys=True)
            )
            jsonFile.close()
        except Exception:
            print("Trouble saving photo info:", sys.exc_info()[0])

    if "video" in pInfo:
        with Timer("getSizes()"):
            pSizes = get_photo_sizes(photo)
        if "HD MP4" in pSizes:
            photo_size_label = "HD MP4"
        else:
            # Fall back for old 'short videos'
            photo_size_label = "Site MP4"
        fname = fname + ".mp4"
    else:
        photo_size_label = size_label
        suffix = ".jpg"
        # Flickr returns JPEG, except for when downloading originals. The only way to find the
        # original type it seems is through the source filename. This is not pretty...
        if photo_size_label == "Original" or not photo_size_label:
            with Timer("getSizes()"):
                pSizes = get_photo_sizes(photo)
            meta = pSizes.get("Original")
            if meta and meta["source"]:
                ext = os.path.splitext(meta["source"])[1]
                if ext:
                    suffix = ext

        fname = fname + suffix

    if os.path.exists(fname):
        # TODO: Ideally we should check for file size / md5 here
        # to handle failed downloads.
        print("Skipping {0}, as it exists already".format(fname))
        return

    print("Saving: {} ({})".format(fname, get_photo_page(pInfo)))
    if skip_download:
        return

    try:
        with Timer("save()"):
            photo.save(fname, photo_size_label)
    except IOError as ex:
        logging.warning("IO error saving photo: {}".format(ex.strerror))
        return
    except FlickrError as ex:
        logging.warning("Flickr error saving photo: {}".format(str(ex)))
        return

    # Set file times to when the photo was taken
    taken = parser.parse(pInfo["taken"])
    taken_unix = time.mktime(taken.timetuple())
    os.utime(fname, (taken_unix, taken_unix))


def download_photo(
    photo_id, get_filename, size_label, skip_download=False, save_json=False
):
    """
    Download one photo

    @param photo_id: str, id of the photo
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    @param skip_download: bool, do not actually download the photo
    @param save_json: bool, save photo info as .json file
    """
    photo = Flickr.Photo(id=photo_id)
    suffix = " ({})".format(size_label) if size_label else ""
    do_download_photo(
        ".", None, photo, size_label, suffix, get_filename, skip_download, save_json
    )


def find_user(userid):
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
    username, get_filename, size_label, skip_download=False, save_json=False
):
    """
    Download all the sets owned by the given user.

    @param username: str, username
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    @param skip_download: bool, do not actually download the photo
    @param save_json: bool, save photo info as .json file
    """
    user = find_user(username)
    with Timer("getPhotosets()"):
        photosets = user.getPhotosets()
    for photoset in photosets:
        download_set(photoset.id, get_filename, size_label, skip_download, save_json)


def download_user_photos(
    username, get_filename, size_label, skip_download=False, save_json=False
):
    """
    Download all the photos owned by the given user.

    @param username: str, username
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    @param skip_download: bool, do not actually download the photo
    @param save_json: bool, save photo info as .json file
    """
    user = find_user(username)
    download_list(user, username, get_filename, size_label, skip_download, save_json)


def print_sets(username):
    """
    Print all sets for the given user

    @param username: str,
    """
    with Timer("find_user()"):
        user = find_user(username)
    with Timer("getPhotosets()"):
        photosets = user.getPhotosets()
    for photo in photosets:
        print("{0} - {1}".format(photo.id, photo.title))


def serialize_json(obj):
    """JSON serializer for objects not serializable by default json code"""

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


def get_photo_sizes(photo):
    for attempt in range(1, (API_RETRIES + 1)):
        try:
            return photo.getSizes()
        except FlickrError as ex:
            logging.warning(
                "Flickr error getting photo size: {}, "
                "attempt: #{}, "
                "attempts left: {}".format(str(ex), attempt, (API_RETRIES - attempt))
            )
            time.sleep(1)
            if attempt >= API_RETRIES:
                raise


def main():
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
        "You can store argument defaults in "
        + CONFIG_FILE
        + ". API keys for example:\n"
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
    parser.add_argument(
        "-t", "--user_auth", action="store_true", help="Enable user authentication"
    )
    parser.add_argument(
        "-l", "--list", type=str, metavar="USER", help="List photosets for a user"
    )
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
    parser.add_argument(
        "-n", "--naming", type=str, metavar="NAMING_MODE", help="Photo naming mode"
    )
    parser.add_argument(
        "-m", "--list_naming", action="store_true", help="List naming modes"
    )
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
    parser.set_defaults(**_load_defaults())

    args = parser.parse_args()

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
        return 0

    if args.skip_download:
        print("Will skip actual downloading of files")

    if args.save_json:
        print("Will save photo info in .json file with same basename as photo")

    if (
        args.download
        or args.download_user
        or args.download_user_photos
        or args.download_photo
    ):
        try:
            with Timer("total run"):
                get_filename = get_filename_handler(args.naming)
                if args.download:
                    download_set(
                        args.download,
                        get_filename,
                        args.quality,
                        args.skip_download,
                        args.save_json,
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
                    )
        except KeyboardInterrupt:
            print(
                "Forcefully aborting. Last photo download might be partial :(",
                file=sys.stderr,
            )
        return 0

    print("ERROR: Must pass either --list or --download\n", file=sys.stderr)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
