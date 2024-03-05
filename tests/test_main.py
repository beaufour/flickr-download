"""Testing that the main function actually loads.

This ensures that all the dependencies actually load too.
"""

from flickr_download.flick_download import main


def test_main() -> None:
    """Loads the main function and expects an exit code of 1."""
    assert main() == 1
