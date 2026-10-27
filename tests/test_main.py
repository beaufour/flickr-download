"""Testing that the main function actually loads.

This ensures that all the dependencies actually load too.
"""

from unittest.mock import Mock, patch

import pytest

from flickr_api.flickrerrors import FlickrError

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


@patch("flickr_download.flick_download._init")
@patch("flickr_download.flick_download.download_set")
def test_main_download_set(mock_download: Mock, mock_init: Mock) -> None:
    """Main with -d downloads a set."""
    mock_init.return_value = True

    with (
        patch("sys.argv", ["flickr_download", "-k", "key", "-s", "secret", "-d", "12345"]),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
    ):
        result = main()

    assert result == 0
    mock_download.assert_called_once()
    call_args = mock_download.call_args
    assert call_args[0][0] == "12345"  # set_id


@patch("flickr_download.flick_download._init")
@patch("flickr_download.flick_download.print_sets")
def test_main_list_sets(mock_print: Mock, mock_init: Mock) -> None:
    """Main with -l lists sets for user."""
    mock_init.return_value = True

    with (
        patch("sys.argv", ["flickr_download", "-k", "key", "-s", "secret", "-l", "testuser"]),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
    ):
        result = main()

    assert result == 0
    mock_print.assert_called_once_with("testuser")


@patch("flickr_download.flick_download._init")
@patch("flickr_download.flick_download.download_photo")
def test_main_download_photo(mock_download: Mock, mock_init: Mock) -> None:
    """Main with -i downloads a single photo."""
    mock_init.return_value = True

    with (
        patch("sys.argv", ["flickr_download", "-k", "key", "-s", "secret", "-i", "99999"]),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
    ):
        result = main()

    assert result == 0
    mock_download.assert_called_once()
    call_args = mock_download.call_args
    assert call_args[0][0] == "99999"  # photo_id


@patch("flickr_download.flick_download._init")
def test_main_init_failure(mock_init: Mock) -> None:
    """Main returns 1 when _init fails."""
    mock_init.return_value = False

    with (
        patch("sys.argv", ["flickr_download", "-k", "key", "-s", "secret", "-d", "12345"]),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
    ):
        result = main()

    assert result == 1


@patch("flickr_download.flick_download._init")
@patch("flickr_download.flick_download.download_set", side_effect=KeyboardInterrupt)
def test_main_keyboard_interrupt(mock_download: Mock, _mock_init: Mock, capsys) -> None:
    """Main handles Ctrl-C gracefully and returns 0."""
    with (
        patch("sys.argv", ["flickr_download", "-k", "key", "-s", "secret", "-d", "12345"]),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
    ):
        result = main()

    assert result == 0
    assert "Forcefully aborting" in capsys.readouterr().err


@patch("flickr_download.flick_download.save_cache")
@patch("flickr_download.flick_download.init_cache")
@patch("flickr_download.flick_download._init")
@patch("flickr_download.flick_download.download_set", side_effect=FlickrError("boom"))
def test_main_saves_cache_on_error(
    _mock_download: Mock, _mock_init: Mock, mock_init_cache: Mock, mock_save: Mock
) -> None:
    """Main saves the cache before re-raising an unexpected error."""
    cache = Mock()
    mock_init_cache.return_value = cache

    with (
        patch(
            "sys.argv",
            ["flickr_download", "-k", "key", "-s", "secret", "-d", "12345", "-c", "cache.pkl"],
        ),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
        pytest.raises(FlickrError),
    ):
        main()

    mock_save.assert_called_once_with("cache.pkl", cache)


@patch("flickr_download.flick_download.save_cache")
@patch("flickr_download.flick_download.init_cache")
@patch("flickr_download.flick_download._init")
@patch("flickr_download.flick_download.download_set")
def test_main_saves_cache_on_success(
    _mock_download: Mock, _mock_init: Mock, mock_init_cache: Mock, mock_save: Mock
) -> None:
    """Main saves the cache after a successful download."""
    cache = Mock()
    mock_init_cache.return_value = cache

    with (
        patch(
            "sys.argv",
            ["flickr_download", "-k", "key", "-s", "secret", "-d", "12345", "-c", "cache.pkl"],
        ),
        patch("flickr_download.flick_download._load_defaults", return_value={}),
    ):
        assert main() == 0

    mock_save.assert_called_once_with("cache.pkl", cache)
