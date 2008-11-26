#!/bin/sh
VERSION=0.1.1
cd ..
tar jcvf theory-${VERSION}.tar.bz2 --exclude 'theory/theory/public/img/art/*' theory/theory theory/README theory/server.ini theory/run-theory.sh  theory/go-pylons.py theory/install.sh  theory/theory.egg-info/ theory/Changelog
