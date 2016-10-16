#!/usr/bin/env python
#
# Util to download a full Flickr set.
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import argparse
import codecs
import errno
import locale
import logging
import os
import sys
import time

import flickr_api as Flickr
from flickr_api.flickrerrors import FlickrAPIError
from dateutil import parser
import yaml

from flickr_download.filename_handlers import get_filename_handler
from flickr_download.filename_handlers import get_filename_handler_help
from flickr_download.utils import get_full_path

CONFIG_FILE = "~/.flickr_download"
OAUTH_TOKEN_FILE = "~/.flickr_token"


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
    token = raw_input()
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
    logging.debug('Loading configuration from {}'.format(filename))
    try:
        with open(filename, 'r') as cfile:
            vals = yaml.load(cfile.read())
            return vals
    except yaml.YAMLError as ex:
        logging.warning('Could not parse configuration file: {}'.format(ex))
    except IOError as ex:
        if ex.errno != errno.ENOENT:
            logging.warning('Could not open configuration file: {}'.format(ex))
        else:
            logging.debug('No config file')

    return {}


def download_set(set_id, get_filename, size_label=None):
    """
    Download the set with 'set_id' to the current directory.

    @param set_id: str, id of the photo set
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    """
    pset = Flickr.Photoset(id=set_id)
    download_list(pset, pset.title, get_filename, size_label)


def download_list(pset, photos_title, get_filename, size_label):
    """
    Download all the photos in the given photo list

    @param pset: FlickrList, photo list to download
    @param photos_title: str, name of the photo list
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    """
    photos = pset.getPhotos()
    pagenum = 2
    while True:
        try:
            if pagenum > photos.info.pages:
                break
            page = pset.getPhotos(page=pagenum)
            photos.extend(page)
            pagenum += 1
        except FlickrAPIError as ex:
            if ex.code == 1:
                break
            raise

    suffix = " ({})".format(size_label) if size_label else ""

    # we need to convert pathname separator to something else to create a valid directory
    dirname = photos_title.replace(os.sep, "_")
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    for photo in photos:
        do_download_photo(dirname, pset, photo, size_label, suffix, get_filename)


def do_download_photo(dirname, pset, photo, size_label, suffix, get_filename):
    """
    Handle the downloading of a single photo

    @param dirname: str, directory to download to
    @param pset: FlickrList, photo list to download
    @param photo: FlickrPhoto, photo to download
    @param size_label: str|None, size to download (or None for largest available)
    @param suffix: str|None, optional suffix to add to file name
    @param get_filename: Function, function that creates a filename for the photo
    """
    fname = get_full_path(dirname, get_filename(pset, photo, suffix))

    if 'video' in photo.getInfo():
        if 'HD MP4' in photo.getSizes():
            photo_size_label = 'HD MP4'
        else:
            # Fall back for old 'short videos'
            photo_size_label = 'Site MP4'
        fname = fname + '.mp4'
    else:
        photo_size_label = size_label
        fname = fname + '.jpg'

    if os.path.exists(fname):
        # TODO: Ideally we should check for file size / md5 here
        # to handle failed downloads.
        print('Skipping {0}, as it exists already'.format(fname))
        return

    print('Saving: {} ({})'.format(fname, photo.getPageUrl()))
    try:
        photo.save(fname, photo_size_label)
    except IOError, ex:
        logging.warning('IO error saving photo: {}'.format(ex.strerror))
        return

    # Set file times to when the photo was taken
    info = photo.getInfo()
    taken = parser.parse(info['taken'])
    taken_unix = time.mktime(taken.timetuple())
    os.utime(fname, (taken_unix, taken_unix))


def download_photo(photo_id, get_filename, size_label):
    """
    Download one photo

    @param photo_id: str, id of the photo
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    """
    photo = Flickr.Photo(id=photo_id)
    suffix = " ({})".format(size_label) if size_label else ""
    do_download_photo(".", None, photo, size_label, suffix, get_filename)


def download_user(username, get_filename, size_label):
    """
    Download all the sets owned by the given user.

    @param username: str, username
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    """
    user = Flickr.Person.findByUserName(username)
    photosets = user.getPhotosets()
    for photoset in photosets:
        download_set(photoset.id, get_filename, size_label)


def download_user_photos(username, get_filename, size_label):
    """
    Download all the photos owned by the given user.

    @param username: str, username
    @param get_filename: Function, function that creates a filename for the photo
    @param size_label: str|None, size to download (or None for largest available)
    """
    user = Flickr.Person.findByUserName(username)
    download_list(user, username, get_filename, size_label)


def print_sets(username):
    """
    Print all sets for the given user

    @param username: str,
    """
    user = Flickr.Person.findByUserName(username)
    photosets = user.getPhotosets()
    for photo in photosets:
        print('{0} - {1}'.format(photo.id, photo.title))


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description='Downloads one or more Flickr photo sets.\n'
        '\n'
        'To use it you need to get your own Flickr API key here:\n'
        'https://www.flickr.com/services/api/misc.api_keys.html\n'
        '\n'
        'For more information see:\n'
        'https://github.com/beaufour/flickr-download',
        epilog='examples:\n'
        '  list all sets for a user:\n'
        '  > {app} -k <api_key> -s <api_secret> -l beaufour\n'
        '\n'
        '  download a given set:\n'
        '  > {app} -k <api_key> -s <api_secret> -d 72157622764287329\n'
        '\n'
        '  download a given set, keeping duplicate names:\n'
        '  > {app} -k <api_key> -s <api_secret> -d 72157622764287329 -n title_increment\n'
        .format(app=sys.argv[0])
    )
    parser.add_argument('-k', '--api_key', type=str,
                        help='Flickr API key')
    parser.add_argument('-s', '--api_secret', type=str,
                        help='Flickr API secret')
    parser.add_argument('-t', '--user_auth', action='store_true',
                        help='Enable user authentication')
    parser.add_argument('-l', '--list', type=str, metavar='USER',
                        help='List photosets for a user')
    parser.add_argument('-d', '--download', type=str, metavar='SET_ID',
                        help='Download the given set')
    parser.add_argument('-p', '--download_user_photos', type=str, metavar='USERNAME',
                        help='Download all photos for a given user')
    parser.add_argument('-u', '--download_user', type=str, metavar='USERNAME',
                        help='Download all sets for a given user')
    parser.add_argument('-i', '--download_photo', type=str, metavar='PHOTO_ID',
                        help='Download one specific photo')
    parser.add_argument('-q', '--quality', type=str, metavar='SIZE_LABEL',
                        default=None, help='Quality of the picture')
    parser.add_argument('-n', '--naming', type=str, metavar='NAMING_MODE',
                        help='Photo naming mode')
    parser.add_argument('-m', '--list_naming', action='store_true',
                        help='List naming modes')
    parser.set_defaults(**_load_defaults())

    args = parser.parse_args()

    if args.list_naming:
        print(get_filename_handler_help())
        return 1

    if not args.api_key or not args.api_secret:
        print ('You need to pass in both "api_key" and "api_secret" arguments', file=sys.stderr)
        return 1

    ret = _init(args.api_key, args.api_secret, args.user_auth)
    if not ret:
        return 1

    # Replace stdout with a non-strict writer that replaces unknown characters instead of throwing
    # an exception. This "fixes" print issues on the standard Windows terminal, and when there is no
    # terminal at all.
    if sys.stdout.isatty():
        default_encoding = sys.stdout.encoding
    else:
        default_encoding = locale.getpreferredencoding()
    if default_encoding != 'utf-8':
        sys.stdout = codecs.getwriter(default_encoding)(sys.stdout, 'replace')

    if args.list:
        print_sets(args.list)
        return 0

    if args.download or args.download_user or args.download_user_photos or args.download_photo:
        try:
            get_filename = get_filename_handler(args.naming)
            if args.download:
                download_set(args.download, get_filename, args.quality)
            elif args.download_user:
                download_user(args.download_user, get_filename, args.quality)
            elif args.download_photo:
                download_photo(args.download_photo, get_filename, args.quality)
            else:
                download_user_photos(args.download_user_photos, get_filename, args.quality)
        except KeyboardInterrupt:
            print('Forcefully aborting. Last photo download might be partial :(', file=sys.stderr)
        return 0

    print('ERROR: Must pass either --list or --download\n', file=sys.stderr)
    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())
