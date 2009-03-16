#!/usr/bin/env python

import os
import shutil
import sys
import subprocess 
import cairo


def main():
    version = '0.1.8'

    script_location = sys.argv[0]
    script_path = os.path.abspath(script_location)
    app_path = os.sep.join(script_path.split(os.sep)[:-3])

    src = os.path.join(app_path,'theory')
    dest = os.path.join(app_path,"theory-%s" % version)
    tar_file = os.path.join(app_path,"theory-%s.tar.bz2" % version)
    exclude_file = os.path.join(src,"tar_exclude")


    # remove destination dir in case it exists
    try:
        shutil.rmtree(dest)
    except OSError:
        pass
    shutil.copytree(src,dest)

    # draw logo
    imgpath = os.path.join(dest,'theory','public','img','theory-logo.png')
    logo_exec = os.path.join(app_path,'theory','scripts','draw_theory_logo.py')
    args = [logo_exec,version,imgpath]
    subprocess.call(args)

    os.chdir(app_path)

    args = ["tar","jcvf",tar_file,"--exclude-from=%s" % exclude_file,"--exclude-vcs","theory-%s" % version]

    subprocess.call(args)

    
def exclude_check(f):
    print "check_exclude: %s" % f

if __name__ ==  "__main__":
    main()
