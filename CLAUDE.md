# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flickr Download is a command-line utility for downloading photos from Flickr. It supports downloading individual photos, photosets, or all photos from a user, with OAuth authentication for private/restricted content.

## Development Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run tests with coverage
uv run coverage run -m pytest
uv run coverage html -d coverage

# Code quality checks (also run via pre-commit)
uv run ruff check flickr_download tests
uv run ruff format --check flickr_download tests
uv run mypy flickr_download

# Run all pre-commit hooks
uv run pre-commit run --all-files

# Run the CLI
uv run flickr_download [args]
```

## Architecture

### Main Package (`flickr_download/`)

- **flick_download.py** - Main entry point with CLI argument parsing, core download functions (`download_set`, `download_list`, `download_photo`, `download_user`, `download_user_photos`), and OAuth handling
- **filename_handlers.py** - Strategy pattern implementation for file naming (title, id, title_and_id, id_and_title, title_increment)
- **utils.py** - Utility functions for caching (pickle-based), file/path sanitization, JSON serialization, and file metadata handling
- **logging_utils.py** - `APIKeysRedacter` formatter that redacts API keys and OAuth tokens from logs

### Key Patterns

- **OAuth Flow**: Interactive browser-based authentication with token persistence to `~/.flickr_token`
- **Configuration**: Both CLI arguments and YAML config file (`~/.flickr_download`) supported
- **Caching**: Pickle-based API response caching with configurable timeout
- **Metadata**: SQLite database for tracking downloads and enabling resumable operations

## Code Quality Standards

- **Ruff**: Linting and formatting with 100-char line length
- **MyPy**: Type checking enabled
- Python 3.10-3.13 supported
