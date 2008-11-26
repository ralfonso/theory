#!/bin/sh

SELF=$(cd $(dirname $0); pwd -P)/
echo "installing theory prerequisites and Python virtual environment to $SELF/env/"
python go-pylons.py --no-site-packages "$SELF/env/" &&
"$SELF/env/bin/easy_install" python-mpd

