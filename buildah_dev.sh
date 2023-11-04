#!/bin/bash
set -x
set -e

bc=$(buildah from docker.io/library/alpine:latest)
buildah run $bc apk add --no-cache git python3 py3-pip
buildah run $bc pip3 install uvicorn[standard] fastapi pydantic gunicorn

buildah config --workingdir=/bjorlileika_api/ $bc
buildah config --env DATA_PATH=/bjorlileika_api/data/ $bc

buildah commit $bc localhost/bjorlileika_api_dev:latest
buildah rm $bc
