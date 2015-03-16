import sys


def get_dict_ele():
    """Return dict[atom]=[abreviation]"""
    elt_path = os.path.dirname(sys.argv[0]) + "/src/elts_abrev.dat"

    with open(elt_path, "r") as f:
        data = f.readlines()

    dict_ele = dict()
    for i in data:
        l = i.split("-")
        dict_ele[l[1].strip().lower()] = l[2].strip().lower()

    return dict_ele


# ______
# | ___ \
# | |_/ /_ _ _ __ ___  ___ _ __
# |  __/ _` | '__/ __|/ _ \ '__|
# | | | (_| | |  \__ \  __/ |
# \_|  \__,_|_|  |___/\___|_|
#

#  __
# /__  _. ._ _   _   _  _        _
# \_| (_| | | | (/_ _> _>   |_| _>
#
def parse_basis_data_gamess_us(data, name, des, elts, debug=False):
        """Parse the basis data raw html of gamess-us to get a nice tuple
           Return [name, description, [[ele, data_ele],...]]"""
        basis_data = []

        b = data.find("$DATA")
        e = data.find("$END")
        if (b == -1 or data.find("$DATA$END") != -1):
            if debug:
                print data
            raise Exception("WARNING not DATA")
        else:
            dict_replace = {"PHOSPHOROUS": "PHOSPHORUS",
                            "D+": "E+",
                            "D-": "E-"}

            for k, v in dict_replace.iteritems():
                data = data.replace(k, v)

            data = data[b + 5:e - 1].split('\n\n')

            dict_ele = get_dict_ele()

            for (elt, data_elt) in zip(elts, data):

                elt_long_th = dict_ele[elt.lower()]
                elt_long_exp = data_elt.split()[0].lower()

                if "$" in data_elt:
                    if debug:
                        print "Eror",
                    raise Exception("WARNING bad split")

                if elt_long_th == elt_long_exp:
                    basis_data.append([elt, data_elt.strip()])
                else:
                    if debug:
                        print "th", elt_long_th
                        print "exp", elt_long_exp
                        print "abv", elt
                    raise Exception("WARNING not a good ELEMENT")

        return [name, des, basis_data]

import os

format_dict = {"Gaussian94": None,
               "GAMESS-US": parse_basis_data_gamess_us,
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
               "AcesII": None,
               }
