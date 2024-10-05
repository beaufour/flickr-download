"""Init file for the flickr_download package."""

from usingversion import getattr_with_version

__getattr__ = getattr_with_version("flickr_download", __file__, __name__)
