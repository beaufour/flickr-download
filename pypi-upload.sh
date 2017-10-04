#!/bin/bash
#
# Very crude upload script for PyPI
#
set -e

rm -f dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
