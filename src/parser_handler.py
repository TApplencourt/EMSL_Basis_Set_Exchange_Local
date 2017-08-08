from __future__ import print_function

import os
import sys


def get_dict_ele():
    """Return dict[atom]=[abbreviation]"""
    elt_path = os.path.join(os.path.dirname(sys.argv[0]), "/src/misc/elts_abrev.dat")

    with open(elt_path, "r") as f:
        data = f.readlines()

    dict_ele = dict()
    for i in data:
        l = i.split("-")
        dict_ele[l[1].strip().lower()] = l[2].strip().lower()

    return dict_ele


# ______                         _         _ _      _
# |  ___|                       | |       | (_)    | |
# | |_ _ __ ___  _ __ ___   __ _| |_    __| |_  ___| |_
# |  _| '__/ _ \| '_ ` _ \ / _` | __|  / _` | |/ __| __|
# | | | | | (_) | | | | | | (_| | |_  | (_| | | (__| |_
# \_| |_|  \___/|_| |_| |_|\__,_|\__|  \__,_|_|\___|\__|
#
from src.parser.nwchem import check_NWChem, parse_basis_data_nwchem
from src.parser.gamess_us import (check_gamess, handle_l_gamess_us,
                                  l_symmetry_gamess_us,
                                  parse_basis_data_gamess_us)
from src.parser.gaussian94 import parse_basis_data_gaussian94

parser_dict = {
    "Gaussian94": parse_basis_data_gaussian94,
    "GAMESS-US": parse_basis_data_gamess_us,
    "NWChem": parse_basis_data_nwchem,
    "GAMESS-UK": None,
    "Turbomole": None,
    "TX93": None,
    "Molpro": None,
    "MolproInt": None,
    "Hondo": None,
    "SuperMolecule": None,
    "Molcas": None,
    "HyperChem": None,
    "Dalton": None,
    "deMon-KS": None,
    "deMon2k": None,
    "AcesII": None
}


def check_format(format):
    try:
        parser_dict[format]
    except KeyError:
        str_ = ["This format ({}) is not available in EMSL".format(format),
                "EMSL provide this list : {}".format(list(parser_dict.keys()))]
        print("\n".join(str_), file=sys.stderr)
        sys.exit(1)
    else:
        return format


def get_parser_function(format):
    if not parser_dict[format]:
        list_parser = [k for k, v in parser_dict.items() if v]

        str_ = ["We have no parser for this format {}".format(format),
                "We only support {}".format(list_parser),
                "Fill free to Fock /pull request",
                "You just need to add a function like this one:",
                "'src.pars.gamess_us.parse_basis_data_gamess_us'"]
        print("\n".join(str_), file=sys.stderr)
        sys.exit(1)
    else:
        return parser_dict[format]


#  _____                                _                    _ _      _
# /  ___|                              | |                  | (_)    | |
# \ `--. _   _ _ __ ___  _ __ ___   ___| |_ _ __ _   _    __| |_  ___| |_
#  `--. \ | | | '_ ` _ \| '_ ` _ \ / _ \ __| '__| | | |  / _` | |/ __| __|
# /\__/ / |_| | | | | | | | | | | |  __/ |_| |  | |_| | | (_| | | (__| |_
# \____/ \__, |_| |_| |_|_| |_| |_|\___|\__|_|   \__, |  \__,_|_|\___|\__|
#         __/ |                                   __/ |
#        |___/                                   |___/

"""
Return the begin and the end of all the type of orbital
input: atom_basis = [name, S 1, 12 0.12 12212, ...]
output: [ [type, begin, end], ...]
"""
symmetry_dict = {"GAMESS-US": l_symmetry_gamess_us}


def get_symmetry_function(format):
    """
    Return the begin and the end of all the type of orbital
    input: atom_basis = [name, S 1, 12 0.12 12212, ...]
    output: [ [type, begin, end], ...]
    """
    try:
        f = symmetry_dict[format]
    except KeyError:
        print("You need to add a function in symmetry_dict", file=sys.stderr)
        print("for your format ({})".format(format), file=sys.stderr)
        sys.exit(1)
    else:
        return f

#  _   _                 _ _        _ _ _    _ _  ______ _      _
# | | | |               | | |      ( | ) |  ( | ) |  _  (_)    | |
# | |_| | __ _ _ __   __| | | ___   V V| |   V V  | | | |_  ___| |_
# |  _  |/ _` | '_ \ / _` | |/ _ \     | |        | | | | |/ __| __|
# | | | | (_| | | | | (_| | |  __/     | |____    | |/ /| | (__| |_
# \_| |_/\__,_|_| |_|\__,_|_|\___|     \_____/    |___/ |_|\___|\__|

"""
Transform SP special function (create using get_symmetry_function) into S and P
"""
handle_l_dict = {"GAMESS-US": handle_l_gamess_us}


def get_handle_l_function(format):
    """
    Transform SP special function (create using get_symmetry_function)
    into S and P
    """
    try:
        return handle_l_dict[format]
    except KeyError:
        print("You need to add a function in handle_l_dict", file=sys.stderr)
        print("for your format ({})".format(format), file=sys.stderr)
        sys.exit(1)


#  _   _       _ _     _       _   _
# | | | |     | (_)   | |     | | (_)
# | | | | __ _| |_  __| | __ _| |_ _  ___  _ __
# | | | |/ _` | | |/ _` |/ _` | __| |/ _ \| '_ \
# \ \_/ / (_| | | | (_| | (_| | |_| | (_) | | | |
#  \___/ \__,_|_|_|\__,_|\__,_|\__|_|\___/|_| |_|
#
d_check = {"GAMESS-US": check_gamess,
           "NWChem": check_NWChem}


def get_check_function(name_program):
    """
    Transform SP special function (create using get_symmetry_function)
    into S and P
    """

    try:
        return d_check[name_program]
    except KeyError:
        str_ = "You need to add a check function for your program {}"
        print(str_.format(name_program), file=sys.stderr)
        print("This one are available {}".format(
            list(d_check.keys())), file=sys.stderr)
        sys.exit(1)
