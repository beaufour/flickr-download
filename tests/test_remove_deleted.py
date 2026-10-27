"""Tests for remove_deleted_files and --remove_deleted (issue #25)."""

import logging
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from flickr_download.flick_download import (
    _filename_to_photo_id,
    _get_metadata_db,
    do_download_photo,
    download_list,
    remove_deleted_files,
)


def _write(path: Path) -> None:
    path.write_text("x")


class TestFilenameToPhotoId:
    """Tests for _filename_to_photo_id."""

    def test_id_naming(self) -> None:
        assert _filename_to_photo_id("12345.jpg", "id") == "12345"

    def test_id_naming_no_number(self) -> None:
        assert _filename_to_photo_id("title.jpg", "id") is None

    def test_id_and_title_naming(self) -> None:
        assert _filename_to_photo_id("12345-My Photo.jpg", "id_and_title") == "12345"

    def test_title_and_id_naming(self) -> None:
        assert _filename_to_photo_id("My Photo-12345.jpg", "title_and_id") == "12345"

    def test_size_suffix_stripped(self) -> None:
        assert _filename_to_photo_id("12345 (Medium).jpg", "id") == "12345"
        assert _filename_to_photo_id("My Photo-12345 (Medium).jpg", "title_and_id") == "12345"

    def test_title_naming_not_encoded(self) -> None:
        assert _filename_to_photo_id("My Photo.jpg", "title") is None
        assert _filename_to_photo_id("My Photo (1).jpg", "title_increment") is None

    def test_none_naming(self) -> None:
        assert _filename_to_photo_id("12345.jpg", None) is None


class TestRemoveDeletedFiles:
    """Tests for remove_deleted_files."""

    def test_removes_files_with_deleted_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(Path(tmpdir, "12345.jpg"))
            _write(Path(tmpdir, "67890.jpg"))
            removed = remove_deleted_files(tmpdir, {"67890"}, "id")
            assert removed == 1
            assert not Path(tmpdir, "12345.jpg").exists()
            assert Path(tmpdir, "67890.jpg").exists()

    def test_dry_run_does_not_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(Path(tmpdir, "12345.jpg"))
            removed = remove_deleted_files(tmpdir, set(), "id", dry_run=True)
            assert removed == 1
            assert Path(tmpdir, "12345.jpg").exists()

    def test_removes_json_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(Path(tmpdir, "12345.jpg"))
            _write(Path(tmpdir, "12345.jpg.json"))
            remove_deleted_files(tmpdir, set(), "id")
            assert not Path(tmpdir, "12345.jpg").exists()
            assert not Path(tmpdir, "12345.jpg.json").exists()

    def test_uses_metadata_db_for_unknown_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = _get_metadata_db(tmpdir)
            conn.execute(
                "INSERT INTO downloads VALUES (?, ?, ?, ?)",
                ("12345", "", "", str(Path(tmpdir, "My Photo.jpg"))),
            )
            conn.commit()
            _write(Path(tmpdir, "My Photo.jpg"))
            removed = remove_deleted_files(tmpdir, set(), "title", metadata_db=conn)
            assert removed == 1
            assert not Path(tmpdir, "My Photo.jpg").exists()
            # Records for removed photos are purged
            assert conn.execute("SELECT * FROM downloads").fetchall() == []
            conn.close()

    def test_keeps_files_without_resolvable_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(Path(tmpdir, "My Photo.jpg"))
            removed = remove_deleted_files(tmpdir, set(), "title")
            assert removed == 0
            assert Path(tmpdir, "My Photo.jpg").exists()

    def test_ignores_metadata_db_and_part_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write(Path(tmpdir, ".metadata.db"))
            _write(Path(tmpdir, "12345.jpg.part"))
            removed = remove_deleted_files(tmpdir, set(), "id")
            assert removed == 0
            assert Path(tmpdir, ".metadata.db").exists()
            assert Path(tmpdir, "12345.jpg.part").exists()

    def test_subdirectories_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            _write(subdir / "12345.jpg")
            removed = remove_deleted_files(tmpdir, set(), "id")
            assert removed == 0
            assert (subdir / "12345.jpg").exists()


class TestDownloadListRemoveDeleted:
    """Tests for the download_list remove_deleted plumbing."""

    def test_download_list_calls_remove_deleted(self, caplog, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.chdir(tmpdir)
            with patch("flickr_download.flick_download.Flickr.Photoset") as mock_set:
                mock_pset = Mock()
                mock_pset.title = "MySet"
                mock_set.return_value = mock_pset
                mock_pset.getPhotos.return_value = []

                with patch("flickr_download.flick_download.Walker") as mock_walker:

                    def make_photo(pid: str) -> Mock:
                        photo = Mock()
                        photo.id = pid
                        photo.title = f"Photo {pid}"
                        photo.__getitem__ = Mock(
                            side_effect=lambda k: True if k == "loaded" else {"url": []}
                        )
                        photo.get = Mock(return_value=None)
                        photo._getOutputFilename = Mock(
                            return_value=str(Path(tmpdir, f"{pid}.jpg"))
                        )
                        return photo

                    mock_walker.return_value = iter([make_photo("111"), make_photo("222")])

                    # download_list chdir'd to tmpdir, so "MySet" lands there;
                    # pre-create it so download_list does not mkdir over it
                    set_dir = Path(tmpdir, "MySet")
                    set_dir.mkdir()
                    _write(set_dir / "111.jpg")
                    _write(set_dir / "333.jpg")

                    with caplog.at_level(logging.INFO):
                        download_list(
                            mock_pset,
                            "MySet",
                            lambda pset, photo, suffix: str(photo.id),
                            None,
                            skip_download=True,
                            naming="id",
                            remove_deleted=True,
                        )

                    # 333 was not on Flickr, so should be reported removed
                    assert "333.jpg" in caplog.text
                    assert not (set_dir / "333.jpg").exists()
                    assert (set_dir / "111.jpg").exists()

    def test_download_list_dry_run(self, caplog, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.chdir(tmpdir)
            with patch("flickr_download.flick_download.Flickr.Photoset") as mock_set:
                mock_pset = Mock()
                mock_pset.title = "MySet"
                mock_set.return_value = mock_pset
                mock_pset.getPhotos.return_value = []

                with patch("flickr_download.flick_download.Walker") as mock_walker:
                    mock_walker.return_value = iter([])

                    set_dir = Path(tmpdir, "MySet")
                    set_dir.mkdir()
                    _write(set_dir / "333.jpg")

                    with caplog.at_level(logging.INFO):
                        download_list(
                            mock_pset,
                            "MySet",
                            lambda pset, photo, suffix: str(photo.id),
                            None,
                            skip_download=True,
                            naming="id",
                            remove_deleted=True,
                            dry_run=True,
                        )

                    assert "Dry run" in caplog.text
                    assert (set_dir / "333.jpg").exists()


class TestMetadataDbMigration:
    """Tests for the fname column migration in _get_metadata_db."""

    def test_migrates_legacy_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a legacy 3-column database
            conn = sqlite3.connect(Path(tmpdir) / ".metadata.db")
            conn.execute("CREATE TABLE downloads (photo_id text, size_label text, suffix text)")
            conn.execute("INSERT INTO downloads VALUES ('p1', 'Original', ' (Original)')")
            conn.commit()
            conn.close()

            conn = _get_metadata_db(tmpdir)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(downloads)")}
            assert "fname" in columns
            # Legacy rows are preserved with NULL fname
            row = conn.execute("SELECT photo_id, fname FROM downloads").fetchone()
            assert row == ("p1", None)
            conn.close()

    def test_new_db_has_fname(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = _get_metadata_db(tmpdir)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(downloads)")}
            assert "fname" in columns
            conn.close()


class TestDoDownloadPhotoRecordsFname:
    """Verify do_download_photo records the file name in the metadata db."""

    def test_records_fname(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = _get_metadata_db(tmpdir)
            mock_photo = Mock()
            mock_photo.id = "999"
            mock_photo.title = "My Photo"
            mock_photo.__getitem__ = Mock(
                side_effect=lambda k: "2020-01-01" if k == "taken" else None
            )
            mock_photo.get = Mock(return_value=None)
            mock_photo.loaded = True
            mock_photo._getOutputFilename = Mock(return_value=str(Path(tmpdir, "My Photo.jpg")))
            mock_photo.save = Mock()

            with patch("flickr_download.flick_download.set_file_time"):
                do_download_photo(
                    tmpdir,
                    None,
                    mock_photo,
                    None,
                    "",
                    lambda pset, photo, suffix: "My Photo",
                    metadata_db=conn,
                )

            row = conn.execute(
                "SELECT photo_id, fname FROM downloads WHERE photo_id = '999'"
            ).fetchone()
            assert row is not None
            assert row[1] is not None
            assert row[1].endswith("My Photo.jpg")
            conn.close()
