"""Tests for flickr_download.flick_download module."""

from unittest.mock import Mock, patch

from flickr_download.flick_download import find_user


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
