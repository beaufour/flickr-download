#!/bin/bash

VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
echo Getting ready to release version ${VERSION}

if [[ $(git tag -l | grep ${VERSION}) ]]; then
    echo ERROR: ${VERSION} tag already exists, bailing...
    exit 1
fi

if [[ -n $(git status -s) ]]; then
  echo ERROR: Repo is modified or has untracked files, bailing...
  exit 1
fi

git tag v${VERSION}
git push --tags
uv build
uv publish
# Note: uv doesn't have built-in version bumping, you'll need to manually update pyproject.toml
echo "Remember to manually bump version in pyproject.toml and commit"
echo "Remember to edit the release notes on https://github.com/beaufour/flickr-download/releases"
