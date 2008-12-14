#!/bin/sh

SELF=$(cd $(dirname $0); pwd -P)/
# if the user is installing from source make sure the album img dir exists
if [ ! -e "$SELF/theory/public/img/art/" ];
then
    mkdir "$SELF/theory/public/img/art/"
fi

echo "installing theory prerequisites and Python virtual environment to $SELF/env/"
python go-pylons.py --no-site-packages "$SELF/env/" &&
"$SELF/env/bin/easy_install" python-mpd

