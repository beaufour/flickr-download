# Flickr Download

## Introduction

[![pre-commit](https://github.com/beaufour/flickr-download/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/beaufour/flickr-download/actions/workflows/pre-commit.yml) [![test](https://github.com/beaufour/flickr-download/actions/workflows/test.yml/badge.svg)](https://github.com/beaufour/flickr-download/actions/workflows/test.yml) [![Coverage Status](https://coveralls.io/repos/github/beaufour/flickr-download/badge.svg)](https://coveralls.io/github/beaufour/flickr-download)

Simple script to download a [Flickr](http://flickr.com) set.

To use it you need to get your own Flickr API key here:
<https://www.flickr.com/services/api/misc.api_keys.html>

## Installation

To install this script use the Python pip utility bundled with your Python distribution:

    > pip install flickr_download

## Examples

List the sets for a user (`-l` prints `<set id> - <title>` for each set):

    flickr_download -k <api key> -s <api secret> -l <user name>

The user name can be passed in as a URL, email, or user name.

Download a given set (by default `title_increment` naming, so no files are ever overwritten):

    flickr_download -k <api key> -s <api secret> -d <set id>

Download all sets for a given user:

    flickr_download -k <api key> -s <api secret> -u <username>

Download all photos for a given user:

    flickr_download -k <api key> -s <api secret> -p <username>

Download a single photo:

    flickr_download -k <api key> -s <api secret> -i <photo id>

Get a public set using the title and id to name the downloaded files:

    flickr_download -k <api key> -s <api secret> -d <set id> -n title_and_id

Pick a specific photo quality instead of the largest available:

    flickr_download -k <api key> -s <api secret> -d <set id> -q Large

Save the photo description and tags in a `.json` file next to each photo:

    flickr_download -k <api key> -s <api secret> -d <set id> -j

Preview the filenames without downloading anything:

    flickr_download -k <api key> -s <api secret> -d <set id> -o

Download private or restricted photos by authorizing against the user's account (see below).

## API key

Get your [Flickr API key](http://www.flickr.com/services/api/).

You can also set your API key and secret in `~/.flickr_download`:

    api_key: my_key
    api_secret: my_secret

This is a YAML file, and it can also hold defaults for any other command line
argument. For example, to always use verbose logging and an API cache:

    api_key: my_key
    api_secret: my_secret
    verbose: true
    cache: api_cache

Command line arguments override these defaults.

## User Authentication Support

The script also allows you to authenticate as a user account. That way you can download sets that
are private and public photos that are restricted. To use this mode, initialize the authorization by
running the script with the `t` parameter to authorize the app.

    flickr_download -k <api key> -s <api secret> -t

This will save `~/.flickr_token` containing the authorization. Subsequent calls with `-t` will use the
stored token. For example using

    flickr_download -k <api key> -s <api secret> -l <USER>

with _USER_ set to your own username, will only fetch your publicly available sets, whereas adding `-t`

    flickr_download -k <api key> -s <api secret> -l <USER> -t

will fetch all your sets including private restricted sets.

Note, if you want to log in as another user delete `~/.flickr_token`.

## Naming modes

Photo filenames are controlled with the `-n`/`--naming` argument. The available modes are
listed by running `flickr_download -m`:

    title            - Name file after title (falls back to photo id)
    id               - Name file after photo id
    title_and_id     - Name file after title and photo id
    id_and_title     - Name file after photo id and title
    title_increment  - Name file after photo title, but add an incrementing counter on
                       duplicates (DEFAULT)

## Downloading a lot of photos

If you are downloading a lot of photos, two parameters will speed things up. Especially on errors (which the Flickr API seems to like to throw regularly). Those parameters are:

* `--cache <cache_file>` – this will cache API responses in the given file, and will thus speed up repeated calls to the same API
* `--metadata_store` - this will store metadata information for the set downloads in `.metadata.db`, which makes it faster to skip already downloaded files.

So to download all the sets for a given user `XXX`, including private photos and sets, do:

    > flickr_download -k KEY -s SECRET --user_auth --cache api_cache --metadata_store --download_user XXX

## Command line arguments

Full reference, as shown by `flickr_download --help`:

| Argument | Description |
| --- | --- |
| `-h`, `--help` | Show help message and exit |
| `-k API_KEY`, `--api_key API_KEY` | Flickr API key |
| `-s API_SECRET`, `--api_secret API_SECRET` | Flickr API secret |
| `-t`, `--user_auth` | Enable user authentication |
| `-l USER`, `--list USER` | List photosets for a user |
| `-d SET_ID`, `--download SET_ID` | Download the given set |
| `-p USERNAME`, `--download_user_photos USERNAME` | Download all photos for a given user |
| `-u USERNAME`, `--download_user USERNAME` | Download all sets for a given user |
| `-i PHOTO_ID`, `--download_photo PHOTO_ID` | Download one specific photo |
| `-q SIZE_LABEL`, `--quality SIZE_LABEL` | Quality of the picture. Examples: Original/Large/Medium/Small. By default the largest available is used. |
| `-n NAMING_MODE`, `--naming NAMING_MODE` | Photo naming mode. Use `--list_naming` to get a list of possible NAMING_MODEs |
| `-m`, `--list_naming` | List naming modes |
| `-o`, `--skip_download` | Skip the actual download of the photo |
| `-j`, `--save_json` | Save photo info like description and tags, one .json file per photo |
| `-c CACHE_FILE`, `--cache CACHE_FILE` | Cache results in CACHE_FILE (speed things up on large downloads in particular) |
| `--metadata_store` | Store information about downloads in a metadata file (helps with retrying downloads) |
| `-v`, `--verbose` | Turns on verbose logging |
| `--version` | Lists the version of the tool |

Pass only one main action (`-l`, `-d`, `-p`, `-u`, or `-i`) per run. If several are given, the
earlier one in the list `-d`, `-u`, `-i`, `-p` takes precedence.
