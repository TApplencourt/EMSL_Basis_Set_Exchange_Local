#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

ins = False

d = {'y': True,
     'n': False}

try:
    import requests
except:
    print "You need requests for dowload the basis, without you still can read a existing DB"

    while True:
        choice = raw_input('Do you want to install it ? [Y/N]')
        try:
            ins = d[choice.lower()]
            break
        except:
            print "not a valid choice"


if ins:
    try:
        import pip
        pip.main(['install', "requests"])
    except:
        print "You need pip, (http://pip.readthedocs.org/en/latest/installing.html)"
        sys.exit(1)

path = os.path.split(os.path.abspath(sys.argv[0]))[0]

with open(path + "/EMSL_api.rc", "w") as f:
    f.write("export EMSL_API_ROOT=%s" % path + "\n")
    f.write("export PYTHONPATH=${PYTHONPATH}:${EMSL_API_ROOT}/src" + "\n")

print "Source EMSL_api.rc, pls"
