"""Tests for flickr_download.flick_download module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from flickr_download.flick_download import _load_defaults, find_user


class TestFindUser:
    """Tests for find_user function."""

    @patch("flickr_download.flick_download.Flickr")
    def test_find_user_by_username(self, mock_flickr: Mock) -> None:
        """find_user looks up by username for simple strings."""
        mock_person = Mock()
        mock_flickr.Person.findByUserName.return_value = mock_person

        result = find_user("someuser")

        mock_flickr.Person.findByUserName.assert_called_once_with("someuser")
        assert result == mock_person

    @patch("flickr_download.flick_download.Flickr")
    def test_find_user_by_email(self, mock_flickr: Mock) -> None:
        """find_user looks up by email when @ is present."""
        mock_person = Mock()
        mock_flickr.Person.findByEmail.return_value = mock_person

        result = find_user("user@example.com")

        mock_flickr.Person.findByEmail.assert_called_once_with("user@example.com")
        assert result == mock_person

    @patch("flickr_download.flick_download.Flickr")
    def test_find_user_by_https_url(self, mock_flickr: Mock) -> None:
        """find_user looks up by URL for https:// URLs."""
        mock_person = Mock()
        mock_flickr.Person.findByUrl.return_value = mock_person

        result = find_user("https://www.flickr.com/photos/someuser")

        mock_flickr.Person.findByUrl.assert_called_once_with(
            "https://www.flickr.com/photos/someuser"
        )
        assert result == mock_person

    @patch("flickr_download.flick_download.Flickr")
    def test_find_user_by_www_url(self, mock_flickr: Mock) -> None:
        """find_user looks up by URL for www.flickr.com URLs."""
        mock_person = Mock()
        mock_flickr.Person.findByUrl.return_value = mock_person

        result = find_user("www.flickr.com/photos/someuser")

        mock_flickr.Person.findByUrl.assert_called_once_with("www.flickr.com/photos/someuser")
        assert result == mock_person

    @patch("flickr_download.flick_download.Flickr")
    def test_find_user_by_flickr_url(self, mock_flickr: Mock) -> None:
        """find_user looks up by URL for flickr.com URLs."""
        mock_person = Mock()
        mock_flickr.Person.findByUrl.return_value = mock_person

        result = find_user("flickr.com/photos/someuser")

        mock_flickr.Person.findByUrl.assert_called_once_with("flickr.com/photos/someuser")
        assert result == mock_person


class TestLoadDefaults:
    """Tests for _load_defaults function."""

    def test_load_defaults_no_file(self) -> None:
        """_load_defaults returns empty dict when no config file."""
        with patch("flickr_download.flick_download.CONFIG_FILE", "/nonexistent/config"):
            result = _load_defaults()
            assert result == {}

    def test_load_defaults_valid_yaml(self) -> None:
        """_load_defaults parses valid YAML config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("api_key: test_key\napi_secret: test_secret\n")
            f.flush()

            with patch("flickr_download.flick_download.CONFIG_FILE", f.name):
                result = _load_defaults()

            assert result["api_key"] == "test_key"
            assert result["api_secret"] == "test_secret"

            Path(f.name).unlink()

    def test_load_defaults_invalid_yaml(self) -> None:
        """_load_defaults returns empty dict for invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [[[")
            f.flush()

            with patch("flickr_download.flick_download.CONFIG_FILE", f.name):
                result = _load_defaults()

            assert result == {}

            Path(f.name).unlink()
