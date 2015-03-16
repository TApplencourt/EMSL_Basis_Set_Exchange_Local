import sys
import os


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


import re

symmetry_regex = re.compile(ur'^(\w)\s+\d+\b')


def l_symmetry_gamess_us(atom_basis):
    """
    Return the begin and the end of all the type of orbital
    input: atom_basis = [name, S 1, 12 0.12 12212, ...]
    output: [ [type, begin, end], ...]
    """
    # Example
    # [[u'S', 1, 5], [u'L', 5, 9], [u'L', 9, 12], [u'D', 16, 18]]"

    l = []
    for i, line in enumerate(atom_basis):
        m = re.search(symmetry_regex, line)
        if m:
            # Cause of L !
            read_symmetry = m.group(1)

            # L is real L or special SP
            # Just check the number of exponant
            if read_symmetry == "L" and len(atom_basis[i + 1].split()) == 4:
                real_symmetry = "SP"
            else:
                real_symmetry = read_symmetry

            l.append([real_symmetry, i])
            try:
                l[-2].append(i)
            except IndexError:
                pass

    l[-1].append(i + 1)
    return l


def handle_l_gamess_us(l_atom_basis):
    """
    Read l_atom_basis and change the SP in L and P
    """

    l_data = []
    for atom_basis in l_atom_basis:

        # Split the data in line
        l_line_raw = atom_basis.split("\n")
        l_line = [l_line_raw[0]]
        # l_line_raw[0] containt the name of the Atom

        for symmetry, begin, end in l_symmetry_gamess_us(l_line_raw):

            if symmetry == "SP":

                body_s = []
                body_p = []

                for i_l in l_line_raw[begin + 1:end]:

                    # one L =>  S & P
                    a = i_l.split()

                    common = "{:>3}".format(a[0])
                    common += "{:>15.7f}".format(float(a[1]))

                    tail_s = common + "{:>23.7f}".format(float(a[2]))
                    body_s.append(tail_s)

                    tail_p = common + "{:>23.7f}".format(float(a[3]))
                    body_p.append(tail_p)

                l_line += [l_line_raw[begin].replace("L", "S")]
                l_line += body_s

                l_line += [l_line_raw[begin].replace("L", "P")]
                l_line += body_p
            else:
                l_line += l_line_raw[begin:end]

        l_data.append("\n".join(l_line))

    return l_data

# ______                         _         _ _      _
# |  ___|                       | |       | (_)    | |
# | |_ _ __ ___  _ __ ___   __ _| |_    __| |_  ___| |_
# |  _| '__/ _ \| '_ ` _ \ / _` | __|  / _` | |/ __| __|
# | | | | | (_) | | | | | | (_| | |_  | (_| | | (__| |_
# \_| |_|  \___/|_| |_| |_|\__,_|\__|  \__,_|_|\___|\__|
#

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
               "AcesII": None}

#  _____                                _                    _ _      _
# /  ___|                              | |                  | (_)    | |
# \ `--. _   _ _ __ ___  _ __ ___   ___| |_ _ __ _   _    __| |_  ___| |_
#  `--. \ | | | '_ ` _ \| '_ ` _ \ / _ \ __| '__| | | |  / _` | |/ __| __|
# /\__/ / |_| | | | | | | | | | | |  __/ |_| |  | |_| | | (_| | | (__| |_
# \____/ \__, |_| |_| |_|_| |_| |_|\___|\__|_|   \__, |  \__,_|_|\___|\__|
#         __/ |                                   __/ |
#        |___/                                   |___/

symmetry_dict = {"GAMESS-US": l_symmetry_gamess_us}


def get_symemetry_function(format):
            try:
                l_symmetry = symmetry_dict[format]
            except KeyError:
                print >> sys.stderr, "You need to add a function in symmetry_dict"
                print >> sys.stderr, "for your format ({0})".format(format)
                sys.exit(1)
            return l_symmetry

#  _   _                 _ _        _ _ _    _ _  ______ _      _
# | | | |               | | |      ( | ) |  ( | ) |  _  (_)    | |
# | |_| | __ _ _ __   __| | | ___   V V| |   V V  | | | |_  ___| |_
# |  _  |/ _` | '_ \ / _` | |/ _ \     | |        | | | | |/ __| __|
# | | | | (_| | | | | (_| | |  __/     | |____    | |/ /| | (__| |_
# \_| |_/\__,_|_| |_|\__,_|_|\___|     \_____/    |___/ |_|\___|\__|

handle_l_dict = {"GAMESS-US": handle_l_gamess_us}
