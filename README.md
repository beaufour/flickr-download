Introduction
============

Simple script to download a [Flickr](http://flickr.com) set:

    flickr_download -k <api key> -s <api secret> -d <set id>

It can also list the public set ids for a given user:

    flickr_download -k <api key> -s <api secret> -l <user name>

Get a public set using the title and id to name the downloaded files:

    flickr_download -k <api key> -s <api secret> -d <set id> -n title_and_id

Download private or restricted photos by authorising against the users account. (see below)

API key
==================

Get your [Flickr API key](http://www.flickr.com/services/api/).

You can also set your API key and secret in `~/.flickr_download`:

    api_key: my_key
    api_secret: my_secret

User Authentication Support
===========================

The script also allows you to authenticate as a user account. That way you can download sets that
are private and public photos that are restricted. To use this mode, initialise the authorisation by
running the script with the `t` parameter to authorize the app.

    flickr_download -k <api key> -s <api secret> -t

This will save `.flickr_token` containing the authorisation. Subsequent calls with `-t` will use the
stored token.

Requirements
============

* [argparse](http://docs.python.org/2.7/library/argparse.html) (Python 2.7+)
* [Python Dateutil](http://labix.org/python-dateutil)
* [Python Flickr API](https://github.com/alexis-mignon/python-flickr-api/)
* [PyYAML](http://pyyaml.org/)

[![Build Status](https://travis-ci.org/beaufour/flickr-download.svg)](https://travis-ci.org/beaufour/flickr-download)
