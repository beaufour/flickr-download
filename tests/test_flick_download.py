"""Tests for flickr_download.flick_download module."""

import os
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import requests.exceptions
from flickr_api.flickrerrors import FlickrAPIError, FlickrError

from flickr_download.flick_download import (
    _check_file_exists_by_id,
    _get_metadata_db,
    _load_defaults,
    do_download_photo,
    download_list,
    find_user,
)


class TestCheckFileExistsById:
    """Tests for _check_file_exists_by_id function."""

    def test_finds_file_starting_with_id(self) -> None:
        """Finds file that starts with photo ID (id naming)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file starting with ID
            Path(tmpdir, "12345.jpg").touch()

            result = _check_file_exists_by_id(tmpdir, "12345")
            assert result is not None
            assert "12345" in result

    def test_finds_file_with_id_and_title(self) -> None:
        """Finds file with ID at start (id_and_title naming)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with ID-title pattern
            Path(tmpdir, "12345-My Photo.jpg").touch()

            result = _check_file_exists_by_id(tmpdir, "12345")
            assert result is not None
            assert "12345" in result

    def test_finds_file_with_title_and_id(self) -> None:
        """Finds file with ID at end (title_and_id naming)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with title-ID pattern
            Path(tmpdir, "My Photo-12345.jpg").touch()

            result = _check_file_exists_by_id(tmpdir, "12345")
            assert result is not None
            assert "12345" in result

    def test_returns_none_when_no_match(self) -> None:
        """Returns None when no file matches photo ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with different ID
            Path(tmpdir, "99999.jpg").touch()

            result = _check_file_exists_by_id(tmpdir, "12345")
            assert result is None

    def test_returns_none_for_empty_directory(self) -> None:
        """Returns None for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _check_file_exists_by_id(tmpdir, "12345")
            assert result is None


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


class TestMetadataDb:
    """Tests for metadata database functions."""

    def test_get_metadata_db_creates_table(self) -> None:
        """_get_metadata_db creates downloads table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = _get_metadata_db(tmpdir)

            # Verify table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'"
            )
            assert cursor.fetchone() is not None

            conn.close()

    def test_get_metadata_db_table_schema(self) -> None:
        """_get_metadata_db creates correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = _get_metadata_db(tmpdir)

            # Insert and retrieve data to verify schema
            conn.execute(
                "INSERT INTO downloads VALUES (?, ?, ?)",
                ("photo123", "Original", " (Original)"),
            )
            conn.commit()

            cursor = conn.execute("SELECT * FROM downloads")
            row = cursor.fetchone()
            assert row == ("photo123", "Original", " (Original)")

            conn.close()


class TestDoDownloadPhoto:
    """Tests for do_download_photo function."""

    def test_skip_already_downloaded_with_metadata_db(self) -> None:
        """do_download_photo skips photos already in metadata db."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up metadata db with existing download
            conn = _get_metadata_db(tmpdir)
            conn.execute(
                "INSERT INTO downloads VALUES (?, ?, ?)",
                ("123", "Original", " (Original)"),
            )
            conn.commit()

            mock_photo = Mock()
            mock_photo.id = "123"
            mock_photo.title = "Test Photo"
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should skip and not call save
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                "Original",
                " (Original)",
                mock_get_filename,
                metadata_db=conn,
            )

            mock_photo.save.assert_not_called()
            conn.close()

    def test_skip_existing_file_by_id_pattern(self) -> None:
        """do_download_photo skips if file exists matching photo ID (local-first check)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing file matching photo ID
            existing_file = Path(tmpdir) / "12345-Some Title.jpg"
            existing_file.touch()

            mock_photo = Mock()
            mock_photo.id = "12345"
            mock_photo.title = "Different Title"
            mock_photo.save = Mock()
            mock_photo._getOutputFilename = Mock()  # Should not be called

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Different Title"

            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

            # Should skip due to local-first check - no API calls made
            mock_photo.save.assert_not_called()
            mock_photo._getOutputFilename.assert_not_called()

    def test_skip_existing_file(self) -> None:
        """do_download_photo skips if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing file
            existing_file = Path(tmpdir) / "Test Photo.jpg"
            existing_file.touch()

            mock_photo = Mock()
            mock_photo.id = "123"
            mock_photo.title = "Test Photo"
            mock_photo.__getitem__ = Mock(return_value=True)  # loaded = True
            mock_photo._getOutputFilename = Mock(return_value=str(existing_file))
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

            # Should not call save since file exists
            mock_photo.save.assert_not_called()

    @patch("flickr_download.flick_download.set_file_time")
    def test_download_photo_saves_file(self, mock_set_file_time: Mock) -> None:
        """do_download_photo saves new photo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = Mock()
            mock_photo.id = "123"
            mock_photo.title = "Test Photo"
            mock_photo.__getitem__ = Mock(
                side_effect=lambda k: {
                    "loaded": True,
                    "taken": "2020-01-01 12:00:00",
                }.get(k)
            )
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            mock_photo.save = Mock()
            mock_photo.get = Mock(return_value=None)

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

            mock_photo.save.assert_called_once()

    @patch("flickr_download.flick_download.set_file_time")
    def test_download_photo_records_in_metadata_db(self, mock_set_file_time: Mock) -> None:
        """do_download_photo records download in metadata db."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = _get_metadata_db(tmpdir)
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = Mock()
            mock_photo.id = "456"
            mock_photo.title = "Test Photo"
            mock_photo.__getitem__ = Mock(
                side_effect=lambda k: {
                    "loaded": True,
                    "taken": "2020-01-01 12:00:00",
                }.get(k)
            )
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            mock_photo.save = Mock()
            mock_photo.get = Mock(return_value=None)

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                "Large",
                " (Large)",
                mock_get_filename,
                metadata_db=conn,
            )

            # Verify recorded in db
            cursor = conn.execute("SELECT * FROM downloads WHERE photo_id = ?", ("456",))
            row = cursor.fetchone()
            assert row == ("456", "Large", " (Large)")
            conn.close()

    def test_skip_download_flag(self) -> None:
        """do_download_photo respects skip_download flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = Mock()
            mock_photo.id = "123"
            mock_photo.title = "Test Photo"
            mock_photo.__getitem__ = Mock(
                side_effect=lambda k: {
                    "loaded": True,
                    "taken": "2020-01-01 12:00:00",
                }.get(k)
            )
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            mock_photo.save = Mock()
            mock_photo.get = Mock(return_value=None)

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
                skip_download=True,
            )

            # Should not call save with skip_download=True
            mock_photo.save.assert_not_called()


class TestDownloadList:
    """Tests for download_list function."""

    @patch("flickr_download.flick_download.Walker")
    @patch("flickr_download.flick_download.do_download_photo")
    def test_download_list_creates_directory(
        self, mock_do_download: Mock, mock_walker: Mock
    ) -> None:
        """download_list creates directory for photoset."""
        mock_walker.return_value = iter([])  # Empty photo list

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                mock_pset = Mock()
                mock_pset.getPhotos = Mock()

                def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                    return "test"

                download_list(
                    mock_pset,
                    "Test Album",
                    mock_get_filename,
                    None,
                )

                assert Path("Test Album").is_dir()
            finally:
                os.chdir(original_cwd)

    @patch("flickr_download.flick_download.Walker")
    @patch("flickr_download.flick_download.do_download_photo")
    def test_download_list_iterates_photos(self, mock_do_download: Mock, mock_walker: Mock) -> None:
        """download_list calls do_download_photo for each photo."""
        mock_photo1 = Mock()
        mock_photo2 = Mock()
        mock_walker.return_value = iter([mock_photo1, mock_photo2])

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                mock_pset = Mock()
                mock_pset.getPhotos = Mock()

                def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                    return "test"

                download_list(
                    mock_pset,
                    "Test Album",
                    mock_get_filename,
                    None,
                )

                assert mock_do_download.call_count == 2
            finally:
                os.chdir(original_cwd)


def _create_mock_photo(
    photo_id: str = "123",
    title: str = "Test Photo",
    loaded: bool = True,
    taken: str = "2020-01-01 12:00:00",
) -> Mock:
    """Helper to create a properly configured mock photo object."""
    mock_photo = Mock()
    mock_photo.id = photo_id
    mock_photo.title = title

    # Configure __getitem__ to return photo data
    photo_data = {"loaded": loaded, "taken": taken, "urls": None}
    mock_photo.__getitem__ = Mock(side_effect=lambda k: photo_data.get(k))

    # Configure get() method for get_photo_page() compatibility
    mock_photo.get = Mock(side_effect=lambda k, default=None: photo_data.get(k, default))

    return mock_photo


class TestDoDownloadPhotoErrorHandling:
    """Tests for error handling in do_download_photo function."""

    def test_ioerror_on_save_is_handled(self) -> None:
        """do_download_photo handles IOError during save gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo()
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            mock_photo.save = Mock(side_effect=IOError("Connection refused"))

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - error is handled internally
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

    def test_flickrerror_on_save_is_handled(self) -> None:
        """do_download_photo handles FlickrError during save gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo()
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            mock_photo.save = Mock(side_effect=FlickrError("API Error"))

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - error is handled internally
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

    def test_connection_error_on_save_is_handled(self) -> None:
        """do_download_photo handles ConnectionError during save gracefully.

        ConnectionError inherits from OSError, which is aliased as IOError in Python 3.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo()
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            mock_photo.save = Mock(
                side_effect=requests.exceptions.ConnectionError("Failed to resolve hostname")
            )

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - ConnectionError inherits from OSError
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

    def test_connection_error_on_get_output_filename_is_handled(self) -> None:
        """do_download_photo handles ConnectionError during _getOutputFilename.

        This is the fix for issue #166 - network errors during metadata retrieval
        are now caught and the photo is skipped gracefully.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_photo = _create_mock_photo()
            mock_photo._getOutputFilename = Mock(
                side_effect=requests.exceptions.ConnectionError("Failed to resolve hostname")
            )
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - error is handled and photo is skipped
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

            # Save should not be called since we return early after error
            mock_photo.save.assert_not_called()

    def test_connection_error_on_get_largest_size_label_is_handled(self) -> None:
        """do_download_photo handles ConnectionError during _getLargestSizeLabel.

        Network errors when checking video size labels are now caught.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo()
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(
                side_effect=requests.exceptions.ConnectionError("Failed to resolve hostname")
            )
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - error is handled and photo is skipped
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,  # size_label=None triggers _getLargestSizeLabel check
                "",
                mock_get_filename,
            )

            # Save should not be called since we return early after error
            mock_photo.save.assert_not_called()

    def test_connection_error_on_photo_load_is_handled(self) -> None:
        """do_download_photo handles ConnectionError during photo.load().

        Network errors like ConnectionError (which inherit from OSError)
        are now caught along with FlickrError.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo(loaded=False)
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo.load = Mock(
                side_effect=requests.exceptions.ConnectionError("Failed to resolve hostname")
            )
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - OSError/ConnectionError is now caught
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

            # Save should not be called since we return early after error
            mock_photo.save.assert_not_called()

    def test_flickrerror_on_photo_load_is_handled(self) -> None:
        """do_download_photo handles FlickrError during photo.load() gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo(loaded=False)
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo.load = Mock(side_effect=FlickrError("Photo not found"))
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - FlickrError is caught and photo is skipped
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
            )

            # Save should not be called since we return early after FlickrError
            mock_photo.save.assert_not_called()

    @patch("flickr_download.flick_download.set_file_time")
    def test_flickr_api_error_permission_denied_on_exif(self, mock_set_file_time: Mock) -> None:
        """do_download_photo handles permission denied error on getExif gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo()
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            # Error code 2 means "Permission denied" for EXIF
            mock_photo.getExif = Mock(side_effect=FlickrAPIError(2, "Permission denied"))
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Should not raise - permission error code 2 is handled
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
                save_json=True,
            )

    @patch("flickr_download.flick_download.set_file_time")
    def test_flickr_api_error_other_code_on_exif_raises(self, mock_set_file_time: Mock) -> None:
        """do_download_photo re-raises non-permission FlickrAPIError on getExif."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "Test Photo.jpg"

            mock_photo = _create_mock_photo()
            mock_photo._getOutputFilename = Mock(return_value=str(target_file))
            mock_photo._getLargestSizeLabel = Mock(return_value="Original")
            # Error code 99 is some other error
            mock_photo.getExif = Mock(side_effect=FlickrAPIError(99, "Unknown error"))
            mock_photo.save = Mock()

            mock_pset = Mock()
            mock_pset.title = "Test Set"

            def mock_get_filename(pset: object, photo: object, suffix: Optional[str]) -> str:
                return "Test Photo"

            # Non-permission errors are re-raised (but then caught by broad except)
            # The broad except at line 248 will catch it and log a warning
            do_download_photo(
                tmpdir,
                mock_pset,
                mock_photo,
                None,
                "",
                mock_get_filename,
                save_json=True,
            )
