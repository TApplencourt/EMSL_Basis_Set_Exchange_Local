#!/usr/bin/env python3

"""EMSL Api.

Usage:
  EMSL_api.py list_basis [--basis=<basis_name>...]
                         [--atom=<atom_name>...]
                         [--db_path=<db_path> |--db_dump_path=<db_dump_path>]
                         [--average_mo_number]
  EMSL_api.py list_atoms --basis=<basis_name>
                         [--db_path=<db_path> |--db_dump_path=<db_dump_path>]
  EMSL_api.py get_basis_data --basis=<basis_name>
                             [--atom=<atom_name>...]
                             [--db_path=<db_path> |--db_dump_path=<db_dump_path>]
                             [(--save [--path=<path>])]
                             [--check=<program_name>]
                             [--treat_l]
  EMSL_api.py list_formats
  EMSL_api.py create_db --format=<format>
                        [--db_path=<db_path> |--db_dump_path=<db_dump_path>]
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
    ./EMSL_api.py list_basis --atom S --basis 'cc-pV*' --average_mo_number
    ./EMSL_api.py list_atoms --basis ANO-RCC
    ./EMSL_api.py get_basis_data --basis 3-21++G*
"""
from __future__ import print_function

import os

from src.EMSL_dump import EMSL_dump
from src.EMSL_local import EMSL_local
from src.misc.docopt import docopt

version = "0.8.1"


if __name__ == '__main__':

    arguments = docopt(__doc__, version='EMSL Api ' + version)
    # ___
    #  |  ._  o _|_
    # _|_ | | |  |_
    #

    if arguments["--db_path"]:
        db_path = arguments["--db_path"]
        db_dump_path = None
    elif arguments["--db_dump_path"]:
        db_path = None
        db_dump_path = arguments["--db_dump_path"]
    else:
        db_dump_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    "db/GAMESS-US.dump")
        db_path = None
#        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
#                               "db/GAMESS-US.db")

    # Check the db
#    try:
#        if not(arguments['create_db']):
#            from src.EMSL_local import checkSQLite3
#            db_path, db_path_changed = checkSQLite3(db_path)
#    except:
#        raise

    #  _     _     _    ______           _
    # | |   (_)   | |   | ___ \         (_)
    # | |    _ ___| |_  | |_/ / __ _ ___ _ ___
    # | |   | / __| __| | ___ \/ _` / __| / __|
    # | |___| \__ \ |_  | |_/ / (_| \__ \ \__ \
    # \_____/_|___/\__| \____/ \__,_|___/_|___/

    if arguments["list_basis"]:
        e = EMSL_local(db_path=db_path, db_dump_path=db_dump_path)

        l = e.list_basis_available(arguments["--atom"],
                                   arguments["--basis"],
                                   arguments["--average_mo_number"])

        if arguments["--average_mo_number"]:
            for name, des, avg in l:
                des_str = "{0:<50}".format(des)
                print("- '{0}' ({1}) || {2}".format(name, avg, des_str))
        else:
            for name, des in l:
                des_str = "{0:<50}".format(des)
                print("- '{0}' || {1}".format(name, des_str))

    #  _     _     _     _____ _                           _
    # | |   (_)   | |   |  ___| |                         | |
    # | |    _ ___| |_  | |__ | | ___ _ __ ___   ___ _ __ | |_ ___
    # | |   | / __| __| |  __|| |/ _ \ '_ ` _ \ / _ \ '_ \| __/ __|
    # | |___| \__ \ |_  | |___| |  __/ | | | | |  __/ | | | |_\__ \
    # \_____/_|___/\__| \____/|_|\___|_| |_| |_|\___|_| |_|\__|___/
    elif arguments["list_atoms"]:
        e = EMSL_local(db_path=db_path, db_dump_path=db_dump_path)

        basis_name = arguments["--basis"]
        l = e.get_list_element_available(basis_name)
        print(", ".join(l))

    # ______           _           _       _
    # | ___ \         (_)         | |     | |
    # | |_/ / __ _ ___ _ ___    __| | __ _| |_ __ _
    # | ___ \/ _` / __| / __|  / _` |/ _` | __/ _` |
    # | |_/ / (_| \__ \ \__ \ | (_| | (_| | || (_| |
    # \____/ \__,_|___/_|___/  \__,_|\__,_|\__\__,_|
    elif arguments["get_basis_data"]:
        e = EMSL_local(db_path=db_path, db_dump_path=db_dump_path)
        basis_name = arguments["--basis"][0]
        elts = arguments["--atom"]

        l_atom_basis = e.get_basis(basis_name, elts,
                                   arguments["--treat_l"],
                                   arguments["--check"])
        # Add separation between atoms, and a empty last line
        str_ = "\n\n".join(l_atom_basis) + "\n"

        if arguments["--save"]:

            if arguments["--path"]:
                path = arguments["--path"]
            else:
                # The defaut path is bais
                path = "_".join([basis_name, ".".join(elts)])
                path = "/tmp/" + path + ".bs"

            with open(path, 'w') as f:
                f.write(str_ + "\n")
            print(path)
        else:
            print(str_)

    #  _     _     _      __                           _
    # | |   (_)   | |    / _|                         | |
    # | |    _ ___| |_  | |_ ___  _ __ _ __ ___   __ _| |_ ___
    # | |   | / __| __| |  _/ _ \| '__| '_ ` _ \ / _` | __/ __|
    # | |___| \__ \ |_  | || (_) | |  | | | | | | (_| | |_\__ \
    # \_____/_|___/\__| |_| \___/|_|  |_| |_| |_|\__,_|\__|___/
    elif arguments["list_formats"]:
        for i in EMSL_dump.get_list_format():
            print(i)

    #  _____                _             _ _
    # /  __ \              | |           | | |
    # | /  \/_ __ ___  __ _| |_ ___    __| | |__
    # | |   | '__/ _ \/ _` | __/ _ \  / _` | '_ \
    # | \__/\ | |  __/ (_| | ||  __/ | (_| | |_) |
    # \_____/_|  \___|\__,_|\__\___|  \__,_|_.__/
    elif arguments["create_db"]:
        db_path = arguments["--db_path"]
        format = arguments["--format"]

        contraction = not arguments["--no-contraction"]

        e = EMSL_dump(db_path=db_path,
                      format=format,
                      contraction=contraction)
        e.new_db()

    #  _
    # /  |  _   _. ._  o ._   _
    # \_ | (/_ (_| | | | | | (_|
    #                         _|

    # Clean up on exit
#    if not(arguments['create_db']) and db_path_changed:
#        os.system("rm -f /dev/shm/%d.db" % (os.getpid()))
