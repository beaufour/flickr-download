Simple script to download a [Flickr](http://flickr.com) set:

    flickr_download -k <api key> -s <api secret> -d <set id>

It can also list the set ids for a given user:

    flickr_download -k <api key> -s <api secret> -l <user name>

Get your [Flickr API key](http://www.flickr.com/services/api/).

Requirements
============

* [argparse](http://docs.python.org/2.7/library/argparse.html) (Python 2.7+)
* [Python Dateutil](http://labix.org/python-dateutil)
* [Python Flickr API](https://github.com/alexis-mignon/python-flickr-api/)
