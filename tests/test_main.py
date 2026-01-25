"""Testing that the main function actually loads.

This ensures that all the dependencies actually load too.
"""

from unittest.mock import patch

from flickr_download.flick_download import main


def test_main_no_args() -> None:
    """Main with no args should print error and return 1."""
    with patch("sys.argv", ["flickr_download"]):
        result = main()
        assert result == 1


def test_main_missing_api_key() -> None:
    """Main without API key should return 1."""
    with (
        patch("sys.argv", ["flickr_download", "-d", "12345"]),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
    ):
        result = main()
        assert result == 1


def test_main_list_naming() -> None:
    """Main with --list_naming should print help and return 1."""
    with patch("sys.argv", ["flickr_download", "--list_naming"]):
        result = main()
        assert result == 1
