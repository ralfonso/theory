#!/bin/sh
SELF=$(cd $(dirname $0); pwd -P)/
VERSION=0.1.5
NAME="theory-${VERSION}"

cd "$SELF/.."
cp -Rp theory "${NAME}"
tar jcvf "${NAME}.tar.bz2" --exclude-from=theory/tar_exclude --exclude-vcs ${NAME}
rm -rf "${NAME}"
