#!/bin/bash
set -x
set -e

bc=$(buildah from docker.io/library/python:slim)

buildah config --workingdir=/bjorlileika_api/ $bc
buildah config --env SQLITE_DB_PATH=/bjorlileika_api/data/ $bc

buildah copy $bc requirements.txt /tmp/requirements.txt
buildah run $bc pip install -r /tmp/requirements.txt

buildah commit $bc localhost/bjorlileika_api_dev:latest
buildah rm $bc
