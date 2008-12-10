#!/bin/sh
SELF=$(cd $(dirname $0); pwd -P)/


start() {
	if [ ! -e "$SELF/env/bin/paster" ]
	then
		echo "please install the prerequisites by using the included install.sh script"
		exit
	fi
	echo "starting theory"
	"$SELF/env/bin/paster" serve --daemon --reload "$SELF/server.ini"
}

stop() {
	echo "stopping theory"
	"$SELF/env/bin/paster" serve "$SELF/server.ini" stop
}

case $1 in
'start')
	start;
	;;
'stop')
	stop;
	;;
*)
	echo "usage: run-theory (start|stop)"
	;;
esac

