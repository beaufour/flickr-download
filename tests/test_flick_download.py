"""Tests for flickr_download.flick_download module."""

import os
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

from flickr_download.flick_download import (
    _get_metadata_db,
    _load_defaults,
    do_download_photo,
    download_list,
    find_user,
)


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
