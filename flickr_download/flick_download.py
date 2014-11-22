#!/usr/bin/env python
#
# Util to download a full Flickr set.
#

from __future__ import absolute_import
from __future__ import unicode_literals
import argparse
import errno
import logging
import os
import sys
import time

import flickr_api as Flickr
from flickr_api.flickrerrors import FlickrAPIError
from dateutil import parser
import yaml

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
    print "Enter the following url in a browser to authorize the application:"
    print url
    print "Copy and paste the <oauth_verifier> value from XML here and press return:"
    Flickr.set_auth_handler(auth)
    token = raw_input()
    auth.set_verifier(token)
    auth.save(os.path.expanduser(OAUTH_TOKEN_FILE))
    print "OAuth token was saved, re-run script to use it."
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


def download_set(set_id, size_label=None):
    """
    Download the set with 'set_id' to the current directory.

    @param set_id: str, id of the photo set
    @param size_label: str|None, size to download (or None for largest available)
    """
    suffix = " ({})".format(size_label) if size_label else ""
    pset = Flickr.Photoset(id=set_id)
    photos = pset.getPhotos()
    pagenum = 2
    while True:
        try:
            page = pset.getPhotos(page=pagenum)
            photos.extend(page)
            pagenum += 1
        except FlickrAPIError as ex:
            if ex.code == 1:
                break
            raise

    if not os.path.exists(pset.title):
        os.mkdir(pset.title)
    for photo in photos:
        fname = '{0}/{1}{2}.jpg'.format(pset.title, photo.title, suffix)
        if os.path.exists(fname):
            # TODO: Ideally we should check for file size / md5 here
            # to handle failed downloads.
            print 'Skipping {0}, as it exists already'.format(fname)
            continue

        print 'Saving: {0}'.format(fname)
        photo.save(fname, size_label)

        # Set file times to when the photo was taken
        info = photo.getInfo()
        taken = parser.parse(info['taken'])
        taken_unix = time.mktime(taken.timetuple())
        os.utime(fname, (taken_unix, taken_unix))


def print_sets(username):
    """
    Print all sets for the given user

    @param username: str,
    """
    user = Flickr.Person.findByUserName(username)
    photosets = user.getPhotosets()
    for photo in photosets:
        print '{0} - {1}'.format(photo.id, photo.title)


def main():
    parser = argparse.ArgumentParser('Download a Flickr Set')
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
    parser.add_argument('-q', '--quality', type=str, metavar='SIZE_LABEL',
                        default=None, help='Quality of the picture')
    parser.set_defaults(**_load_defaults())

    args = parser.parse_args()

    if not args.api_key or not args.api_secret:
        print >> sys.stderr, 'You need to pass in both "api_key" and "api_secret" arguments'
        return 1

    ret = _init(args.api_key, args.api_secret, args.user_auth)
    if not ret:
        return 1

    if args.list:
        print_sets(args.list)
    elif args.download:
        try:
            download_set(args.download, args.quality)
        except KeyboardInterrupt:
            print >> sys.stderr, 'Forcefully aborting. Last photo download might be partial :('
    else:
        print >> sys.stderr, 'ERROR: Must pass either --list or --download\n'
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
