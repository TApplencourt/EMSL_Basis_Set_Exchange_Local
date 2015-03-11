#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""EMSL Api.

Usage:
  EMSL_api.py list_basis        [--atom=<atom_name>...]
                                [--db_path=<db_path>]
                                [--average_mo_number]
                                [--basis=<basis_name>...]
  EMSL_api.py list_atoms  --basis=<basis_name>
                                [--db_path=<db_path>]
  EMSL_api.py get_basis_data --basis=<basis_name>
                                [--atom=<atom_name>...]
                                [--db_path=<db_path>]
                                [--with_l]
                                [(--save [--path=<path>])]
  EMSL_api.py list_formats
  EMSL_api.py create_db      --db_path=<db_path>
                             --format=<format>
                             [--no-contraction]
  EMSL_api.py (-h | --help)
  EMSL_api.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --no-contraction  Basis functions are not contracted

<db_path> is the path to the SQLite3 file containing the Basis sets.
By default is $EMSL_API_ROOT/db/Gausian_uk.db

Example of use:
    ./EMSL_api.py list_basis --atom Al --atom U
    ./EMSL_api.py list_atoms --basis ANO-RCC
    ./EMSL_api.py get_basis_data --basis 3-21++G*
"""

version = "0.2.2"

import sys
import os

from src.docopt import docopt
from src.EMSL_dump import EMSL_dump
from src.EMSL_local import EMSL_local, checkSQLite3

if __name__ == '__main__':

    arguments = docopt(__doc__, version='EMSL Api ' + version)

    # ___
    #  |  ._  o _|_
    # _|_ | | |  |_
    #

    if arguments["--db_path"]:
        db_path = arguments["--db_path"]
    else:
        db_path = os.path.dirname(__file__) + "/db/Gamess-us.db"

    # Check the db
    try:
        if not(arguments['create_db']):
            db_path, db_path_changed = checkSQLite3(db_path)
    except:
        raise

    #  _     _     _    ______           _
    # | |   (_)   | |   | ___ \         (_)
    # | |    _ ___| |_  | |_/ / __ _ ___ _ ___
    # | |   | / __| __| | ___ \/ _` / __| / __|
    # | |___| \__ \ |_  | |_/ / (_| \__ \ \__ \
    # \_____/_|___/\__| \____/ \__,_|___/_|___/

    if arguments["list_basis"]:
        e = EMSL_local(db_path=db_path)

        elts = arguments["--atom"]

        amn = arguments["--average_mo_number"]

        l = e.get_list_basis_available(elts,
                                       arguments["--basis"],
                                       average_mo_number=amn)

        if amn:
            for name, des, avg in l:
                print "- '{}' ({}) || {:<50}".format(name, avg, des)
        else:
            for name, des in l:
                print "- {} || {:<50}".format(name, des)

    #  _     _     _     _____ _                           _
    # | |   (_)   | |   |  ___| |                         | |
    # | |    _ ___| |_  | |__ | | ___ _ __ ___   ___ _ __ | |_ ___
    # | |   | / __| __| |  __|| |/ _ \ '_ ` _ \ / _ \ '_ \| __/ __|
    # | |___| \__ \ |_  | |___| |  __/ | | | | |  __/ | | | |_\__ \
    # \_____/_|___/\__| \____/|_|\___|_| |_| |_|\___|_| |_|\__|___/
    if arguments["list_atoms"]:
        e = EMSL_local(db_path=db_path)

        basis_name = arguments["--basis"]
        l = e.get_list_element_available(basis_name)
        print ", ".join(l)

    # ______           _           _       _
    # | ___ \         (_)         | |     | |
    # | |_/ / __ _ ___ _ ___    __| | __ _| |_ __ _
    # | ___ \/ _` / __| / __|  / _` |/ _` | __/ _` |
    # | |_/ / (_| \__ \ \__ \ | (_| | (_| | || (_| |
    # \____/ \__,_|___/_|___/  \__,_|\__,_|\__\__,_|
    if arguments["get_basis_data"]:
        e = EMSL_local(db_path=db_path)
        basis_name = arguments["--basis"]
        elts = arguments["--atom"]

        l = e.get_basis(basis_name, elts, arguments["--with_l"])
        str_ = "\n\n".join(l) + "\n"

        if arguments["--save"]:

            if arguments["--path"]:
                path = arguments["--path"]
            else:
                path = "_".join([basis_name, ".".join(elts)])
                path = "/tmp/" + path + ".bs"

            with open(path, 'w') as f:
                f.write(str_ + "\n")
            print path
        else:
            print str_

    #  _     _     _      __                           _
    # | |   (_)   | |    / _|                         | |
    # | |    _ ___| |_  | |_ ___  _ __ _ __ ___   __ _| |_ ___
    # | |   | / __| __| |  _/ _ \| '__| '_ ` _ \ / _` | __/ __|
    # | |___| \__ \ |_  | || (_) | |  | | | | | | (_| | |_\__ \
    # \_____/_|___/\__| |_| \___/|_|  |_| |_| |_|\__,_|\__|___/
    if arguments["list_formats"]:
        e = EMSL_dump()
        for i in e.get_list_format():
            print i

    #  _____                _             _ _
    # /  __ \              | |           | | |
    # | /  \/_ __ ___  __ _| |_ ___    __| | |__
    # | |   | '__/ _ \/ _` | __/ _ \  / _` | '_ \
    # | \__/\ | |  __/ (_| | ||  __/ | (_| | |_) |
    #  \____/_|  \___|\__,_|\__\___|  \__,_|_.__/
    if arguments["create_db"]:
        db_path = arguments["--db_path"]
        format = arguments["--format"]

        format_dict = EMSL_dump().get_list_format()
        if format not in format_dict:
            print "Format %s doesn't exist. Run list_formats to get the list of formats." % (format)
            sys.exit(1)
        contraction = not arguments["--no-contraction"]

        e = EMSL_dump(
            db_path=db_path,
            format=format_dict[format],
            contraction=contraction)
        e.new_db()

    #  _
    # /  |  _   _. ._  o ._   _
    # \_ | (/_ (_| | | | | | (_|
    #                         _|

    # Clean up on exit
    if not(arguments['create_db']) and db_path_changed:
        os.system("rm -f /dev/shm/%d.db" % (os.getpid()))
