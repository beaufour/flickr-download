Introduction
============

Simple script to download a [Flickr](http://flickr.com) set:

    flickr_download -k <api key> -s <api secret> -d <set id>

It can also list the set ids for a given user:

    flickr_download -k <api key> -s <api secret> -l <user name>

Get a set using the title and id to name the downloaded files:

    flickr_download -k <api key> -s <api secret> -d <set id> -n title_and_id

API key
==================

Get your [Flickr API key](http://www.flickr.com/services/api/).

You can also set your API key and secret in `~/.flickr_download`:

    api_key: my_key
    api_secret: my_secret

User Authentication Support
===========================

The script also allows you to authenticate as your user account. That way you can download sets that
are private and public photos that are restricted. To use this mode, pass in `-t` to the script too.

The setup the first time is slightly hacky, but it works :)

Requirements
============

* [argparse](http://docs.python.org/2.7/library/argparse.html) (Python 2.7+)
* [Python Dateutil](http://labix.org/python-dateutil)
* [Python Flickr API](https://github.com/alexis-mignon/python-flickr-api/)
* [PyYAML](http://pyyaml.org/)

[![Build Status](https://travis-ci.org/beaufour/flickr-download.svg)](https://travis-ci.org/beaufour/flickr-download)
