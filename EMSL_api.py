#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""EMSL Api.

Usage:
  EMSL_api.py get_list_basis <db_path>
  EMSL_api.py get_list_elements <db_path> <basis_name>
  EMSL_api.py get_basis_data <db_path> <basis_name> <elts>...
  EMSL_api.py get_list_formats
  EMSL_api.py create_db <db_path> <format> [--no-contraction]
  EMSL_api.py (-h | --help)
  EMSL_api.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --no-contraction  Basis functions are not contracted

<db_path> is the path to the SQLite3 file containing the Basis sets.
"""

version = "0.1.1"


import sys
sys.path.append('./src/')

from docopt import docopt
from EMSL_utility import EMSL_dump
from EMSL_utility import format_dict
from EMSL_utility import EMSL_local

if __name__ == '__main__':

    arguments = docopt(__doc__, version='EMSL Api ' + version)
#    print arguments

    if arguments["get_list_basis"]:
        db_path = arguments["<db_path>"]

        e = EMSL_local(db_path=db_path)
        l = e.get_list_basis_available()
        for i in l:
            print i

    elif arguments["get_list_elements"]:

        db_path = arguments["<db_path>"]
        basis_name = arguments["<basis_name>"]

        e = EMSL_local(db_path=db_path)
        l = e.get_list_element_available(basis_name)
        for i in l:
            print i

    elif arguments["get_basis_data"]:

        db_path = arguments["<db_path>"]
        basis_name = arguments["<basis_name>"]
        elts = arguments["<elts>"]

        e = EMSL_local(db_path=db_path)

        l = e.get_basis(basis_name, elts)
        for i in l:
            print i, '\n'

    elif arguments["get_list_formats"]:
        for i in format_dict:
            print i

    elif arguments["create_db"]:
        db_path = arguments["<db_path>"]
        format = arguments["<format>"]
        if format not in format_dict:
            print "Format %s doesn't exist. Run get_list_formats to get the list of formats." % (format)
            sys.exit(1)
        contraction = not arguments["--no-contraction"]

        e = EMSL_dump(
            db_path=db_path, format=format_dict[format], contraction=contraction)
        e.new_db()
