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
uv run python -c "
import tomllib
import re

with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
version = data['project']['version']
parts = version.split('.')
parts[-1] = str(int(parts[-1]) + 1)
new_version = '.'.join(parts)

with open('pyproject.toml', 'r') as f:
    content = f.read()
content = re.sub(r'version = \"' + version + '\"', 'version = \"' + new_version + '\"', content)
with open('pyproject.toml', 'w') as f:
    f.write(content)
print(new_version)
"
git add pyproject.toml
git commit -m "Bumps to version $(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")"
git push

echo Remember to edit the release notes on https://github.com/beaufour/flickr-download/releases
