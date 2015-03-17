#  _
# /  |_   _   _ |        _. | o  _| o _|_
# \_ | | (/_ (_ |<   \/ (_| | | (_| |  |_ \/
#                                         /
# Do this After the L special case traitement.

import sys


def check_gamess(str_type):
    """Check is the orbital type is handle by gamess"""

    assert len(str_type) == 1

    if str_type in "S P D".split():
        return True
    elif str_type == "SP":
        raise BaseException
    else:
        return True


def check_NWChem(str_type):
    """Check is the orbital type is handle by gamess"""

    assert len(str_type) == 1

    if str_type in "S P D".split():
        return True
    elif str_type > "I" or str_type in "K L M".split():
        raise BaseException
    else:
        return True


d_check = {"GAMESS-US": check_gamess,
           "NWChem": check_NWChem}


def get_check_function(name_program):
    """
    Tranforme SP special function (create using get_symmetry_function)
    into S and P
    """
    try:
        f = d_check[name_program]
    except KeyError:
        str_ = "You need to add a check funtion for your program {0}"
        print >> sys.stderr, str_.format(name_program)
        print >> sys.stderr, "This one are avalaible {0}".format(d_check.keys())
        sys.exit(1)
    return f
