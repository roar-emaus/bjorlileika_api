#!/bin/bash
set -x
set -e

bc=$(buildah from docker.io/library/alpine:latest)
buildah run $bc apk add --no-cache git python3 py3-pip
buildah run $bc pip3 install uvicorn[standard] fastapi pydantic gunicorn
buildah run $bc git clone https://github.com/roar-emaus/bjorlileika_api.git

buildah config --workingdir=/bjorlileika_api/ $bc
buildah config --env DATA_PATH=/bjorlileika_api/data/ $bc
buildah config --cmd "gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:80" $bc

buildah commit $bc localhost/bjorlileika_api:latest
buildah rm $bc
