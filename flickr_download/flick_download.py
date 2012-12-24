#!/usr/bin/python
#
# Util to download a full Flickr set.
#

from __future__ import absolute_import
from __future__ import unicode_literals
import argparse
import os
import sys
import time

import flickr_api as Flickr
from dateutil import parser


def init(key, secret):
    """
    Initialize API.

    @see: http://www.flickr.com/services/api/

    @param key: str, API key
    @param secret: str, API secret
    """
    Flickr.set_keys(key, secret)


def download_set(set_id, size_label=None):
    """
    Download the set with 'set_id' to the current directory.

    @param set_id: str, id of the photo set
    @param size_label: str|None, size to download (or None for largest available)
    """
    pset = Flickr.Photoset(id=set_id)
    photos = pset.getPhotos()
    for photo in photos:
        fname = '{0}.jpg'.format(photo.id)
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
    parser.add_argument('-k', '--api_key', type=str, required=True,
                        help='Flickr API key')
    parser.add_argument('-s', '--api_secret', type=str, required=True,
                        help='Flickr API secret')
    parser.add_argument('-l', '--list', type=str, metavar='USER',
                        help='List photosets for a user')
    parser.add_argument('-d', '--download', type=str, metavar='SET_ID',
                        help='Download the given set')

    args = parser.parse_args()
    init(args.api_key, args.api_secret)
    if args.list:
        print_sets(args.list)
    elif args.download:
        download_set(args.download)
    else:
        print >> sys.stderr, 'ERROR: Must pass either --list or --download\n'
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
