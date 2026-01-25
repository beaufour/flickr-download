"""Integration tests that hit the real Flickr API.

These tests require valid API credentials in ~/.flickr_download config file.
They use a known public photoset for testing.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from flickr_download.flick_download import (
    _init,
    _load_defaults,
    download_photo,
    find_user,
    print_sets,
)
from flickr_download.filename_handlers import get_filename_handler


# Known public user for testing
TEST_USER = "beaufour"


@pytest.fixture(scope="module")
def api_setup() -> bool:
    """Set up API credentials from config file."""
    defaults = _load_defaults()
    if not defaults.get("api_key") or not defaults.get("api_secret"):
        pytest.skip("No API credentials found in ~/.flickr_download")

    result = _init(defaults["api_key"], defaults["api_secret"], oauth=False)
    if not result:
        pytest.skip("Failed to initialize Flickr API")
    return True


@pytest.fixture(scope="module")
def test_photo_id(api_setup: bool) -> str:
    """Get a real public photo ID from the test user's photostream."""
    user = find_user(TEST_USER)
    # Get the first photo from the user's public photos
    photos = user.getPhotos(per_page=1)
    if not photos:
        pytest.skip(f"No public photos found for user {TEST_USER}")
    return str(photos[0].id)


class TestFindUserIntegration:
    """Integration tests for user lookup."""

    def test_find_user_by_username(self, api_setup: bool) -> None:
        """Find a real user by username."""
        user = find_user(TEST_USER)
        assert user is not None
        assert user.username == TEST_USER

    def test_find_user_by_url(self, api_setup: bool) -> None:
        """Find a real user by Flickr URL."""
        user = find_user(f"https://www.flickr.com/photos/{TEST_USER}")
        assert user is not None
        assert user.username == TEST_USER


class TestDownloadPhotoIntegration:
    """Integration tests for single photo download."""

    def test_download_single_photo(self, api_setup: bool, test_photo_id: str) -> None:
        """Download a single photo and verify file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                get_filename = get_filename_handler("id")
                download_photo(
                    test_photo_id,
                    get_filename,
                    size_label="Small",  # Use small size for faster download
                    skip_download=False,
                    save_json=False,
                )

                # Check that a file was created
                files = list(Path(".").glob("*"))
                assert len(files) == 1
                assert files[0].suffix in [".jpg", ".png", ".gif"]
                assert files[0].stat().st_size > 0
            finally:
                os.chdir(original_cwd)

    def test_download_photo_with_json(self, api_setup: bool, test_photo_id: str) -> None:
        """Download a photo with JSON metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                get_filename = get_filename_handler("id")
                download_photo(
                    test_photo_id,
                    get_filename,
                    size_label="Small",
                    skip_download=False,
                    save_json=True,
                )

                # Check that both photo and JSON were created
                photo_files = list(Path(".").glob("*.jpg")) + list(Path(".").glob("*.png"))
                json_files = list(Path(".").glob("*.json"))

                assert len(photo_files) >= 1
                assert len(json_files) == 1

                # Verify JSON contains expected fields
                with open(json_files[0]) as f:
                    data = json.load(f)
                assert "id" in data
                assert "title" in data
            finally:
                os.chdir(original_cwd)

    def test_download_photo_skip_existing(self, api_setup: bool, test_photo_id: str) -> None:
        """Verify that existing photos are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                get_filename = get_filename_handler("id")

                # Download once
                download_photo(
                    test_photo_id,
                    get_filename,
                    size_label="Small",
                    skip_download=False,
                    save_json=False,
                )

                files = list(Path(".").glob("*"))
                assert len(files) == 1
                first_mtime = files[0].stat().st_mtime

                # Download again - should skip
                download_photo(
                    test_photo_id,
                    get_filename,
                    size_label="Small",
                    skip_download=False,
                    save_json=False,
                )

                # File should not have been modified
                files = list(Path(".").glob("*"))
                assert len(files) == 1
                assert files[0].stat().st_mtime == first_mtime
            finally:
                os.chdir(original_cwd)


class TestPrintSetsIntegration:
    """Integration tests for listing photosets."""

    def test_print_sets(self, api_setup: bool, capsys: pytest.CaptureFixture[str]) -> None:
        """List photosets for a real user."""
        print_sets(TEST_USER)

        captured = capsys.readouterr()
        # Should output at least one line with set ID and title
        assert captured.out.strip() != ""
        lines = captured.out.strip().split("\n")
        assert len(lines) >= 1
        # Each line should have format "id - title"
        assert " - " in lines[0]
