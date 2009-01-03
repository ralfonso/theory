#!/bin/sh
SELF=$(cd $(dirname $0); pwd -P)/

if [ ! -e "$SELF/env/bin/paster" ]
then
	echo "please install the prerequisites by using the included install.sh script"
	exit
fi
"$SELF/env/bin/paster" serve --reload "$SELF/development.ini"
