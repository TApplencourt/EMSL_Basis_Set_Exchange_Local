# -*- coding: utf-8 -*-

import sqlite3
import re
import sys
import os


def checkSQLite3(db_path):
    """Check if the db_path is a good one"""

    from os.path import isfile, getsize

    # Check if db file is readable
    if not os.access(db_path, os.R_OK):
        print >>sys.stderr, "Db file %s is not readable" % (db_path)
        raise IOError

    if not isfile(db_path):
        print >>sys.stderr, "Db file %s is not... a file!" % (db_path)
        raise IOError

    if getsize(db_path) < 100:  # SQLite database file header is 100 bytes
        print >>sys.stderr, "Db file %s is not a SQLite file!" % (db_path)
        raise IOError

    with open(db_path, 'rb') as fd:
        header = fd.read(100)

    if header[:16] != 'SQLite format 3\x00':
        print >>sys.stderr, "Db file %s is not in SQLiteFormat3!" % (db_path)
        raise IOError

    # Check if the file system allows I/O on sqlite3 (lustre)
    # If not, copy on /dev/shm and remove after opening
    try:
        EMSL_local(db_path=db_path).get_list_basis_available()
    except sqlite3.OperationalError:
        print >>sys.stderr, "I/O Error for you file system"
        print >>sys.stderr, "Try some fixe"
        new_db_path = "/dev/shm/%d.db" % (os.getpid())
        os.system("cp %s %s" % (db_path, new_db_path))
        db_path = new_db_path
    else:
        changed = False
        return db_path, changed

    # Try again to check
    try:
        EMSL_local(db_path=db_path).get_list_basis_available()
    except:
        print >>sys.stderr, "Sorry..."
        os.system("rm -f /dev/shm/%d.db" % (os.getpid()))
        raise
    else:
        print >>sys.stderr, "Working !"
        changed = True
        return db_path, changed


def cond_sql_or(table_name, l_value, glob=False):
    """Take a table_name, a list of value and create the sql or combande"""

    opr = "GLOB" if glob else "="

    return [" OR ".join(['{} {} "{}"'.format(table_name,
                                             opr,
                                             val) for val in l_value])]


def string_to_nb_mo(str_type):
    """Take a string and return the nb of orbital"""
    assert len(str_type) == 1

    d = {"S": 1,
         "P": 2,
         "D": 3}

    if str_type in d:
        return 2 * d[str_type] + 1
    # ord("F") = 70 and ord("Z") = 87
    elif 70 <= ord(str_type) <= 87:
        # ord("F") = 70 and l = 4 so ofset if 66
        return 2 * (ord(str_type) - 66) + 1
    else:
        raise BaseException


#  _
# /  |_   _   _ |        _. | o  _| o _|_
# \_ | | (/_ (_ |<   \/ (_| | | (_| |  |_ \/
#                                         /

def check_gamess(str_type):
    """Check is the orbital type is handle by gamess"""

    assert len(str_type) == 1

    if str_type in "S P D".split():
        return True
    elif str_type == "L":
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


#  _       __
# |_ |\/| (_  |    |   _   _  _. |
# |_ |  | __) |_   |_ (_) (_ (_| |
#
class EMSL_local:

    """
    All the method for using the EMSL db localy
    """

    def __init__(self, db_path=None, format=None):
        self.db_path = db_path
        self.p = re.compile(ur'^(\w)\s+\d+\b')
        self.format = format

    def get_list_symetry(self, atom_basis):
        """
        Return the begin and the end of all the type of orbital
        input: atom_basis = [name, ]
        output: [ [type, begin, end], ...]
        """
        # Example
        # [[u'S', 1, 5], [u'L', 5, 9], [u'L', 9, 12], [u'D', 16, 18]]"

        l = []
        for i, line in enumerate(atom_basis):
            m = re.search(self.p, line)
            if m:
                l.append([m.group(1), i])
                try:
                    l[-2].append(i)
                except IndexError:
                    pass

        l[-1].append(i + 1)
        return l

    def get_list_basis_available(self,
                                 elts=[],
                                 basis=[],
                                 average_mo_number=False):
        """
        return all the basis name who contant all the elts
        """
        # If not elts just get the distinct name
        # Else: 1) fetch for geting all the run_id whos satisfy the condition
        #       2) If average_mo_number:
        #            * Get name,descripption,data
        #            * Then parse it
        #          Else Get name,description
        #       3) Parse it

        # ~#~#~#~ #
        # I n i t #
        # ~#~#~#~ #

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # ~#~#~#~#~#~ #
        # F i l t e r #
        # ~#~#~#~#~#~ #

        if basis:
            cmd_filter_basis = " ".join(cond_sql_or("name", basis, glob=True))
        else:
            cmd_filter_basis = "(1)"

        # Not Ets
        if not elts:
            if not average_mo_number:
                cmd = """SELECT DISTINCT name, description
                         FROM basis_tab
                         WHERE {0}"""
            else:
                cmd = """SELECT DISTINCT name, description, data
                         FROM output_tab
                         WHERE {0}"""

            cmd = cmd.format(cmd_filter_basis)

        else:

            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #
            # G e t t i n g _ B a s i s I d #
            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #

            str_ = """SELECT DISTINCT basis_id
                      FROM output_tab
                      WHERE elt=? AND {0}""".format(cmd_filter_basis)

            cmd = " INTERSECT ".join([str_] * len(elts)) + ";"
            c.execute(cmd, elts)

            l_basis_id = [i[0] for i in c.fetchall()]

            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~ #
            # C r e a t e _ t h e _ c m d #
            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~ #

            cmd_filter_basis = " ".join(cond_sql_or("basis_id", l_basis_id))
            cmd_filter_ele = " ".join(cond_sql_or("elt", elts))

            column_to_fech = "name, description"
            if average_mo_number:
                column_to_fech += ", data"

            filter_where = " ({}) AND ({})".format(
                cmd_filter_ele,
                cmd_filter_basis)

            cmd = """SELECT DISTINCT {0}
                     FROM output_tab
                     WHERE {1}
                     ORDER BY name""".format(column_to_fech, filter_where)
        # ~#~#~#~#~ #
        # F e t c h #
        # ~#~#~#~#~ #

        c.execute(cmd)
        info = c.fetchall()

        conn.close()

        # ~#~#~#~#~#~#~ #
        # P a r s i n g #
        # ~#~#~#~#~#~#~ #
        # If average_mo_number is asking

        from collections import OrderedDict
        dict_info = OrderedDict()
        # Description : dict_info[name] = [description, nb_mo, nb_ele]

        if average_mo_number:

            print "WARNING DO NOT SUPPORT L COUNTING"
            print "TREAD L FUNCTION NOT LIKE A SPECIAL ONE"
            for name, description, atom_basis in info:
                nb_mo = 0

                line = atom_basis.split("\n")
                for type_, _, _ in self.get_list_symetry(line):
                    nb_mo += string_to_nb_mo(type_)

                try:
                    dict_info[name][1] += nb_mo
                    dict_info[name][2] += 1.
                except:
                    dict_info[name] = [description, nb_mo, 1.]

        # ~#~#~#~#~#~ #
        # R e t u r n #
        # ~#~#~#~#~#~ #

        if average_mo_number:
            return[[k, v[0], str(v[1] / v[2])] for k, v in dict_info.iteritems()]
        else:
            return [i[:] for i in info]

    def get_list_element_available(self, basis_name):

        # ~#~#~#~ #
        # I n i t #
        # ~#~#~#~ #

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # ~#~#~#~#~#~ #
        # F i l t e r #
        # ~#~#~#~#~#~ #

        str_ = """SELECT DISTINCT elt
                  FROM output_tab
                  WHERE name=:name_us COLLATE NOCASE"""

        # ~#~#~#~#~ #
        # F e t c h #
        # ~#~#~#~#~ #

        c.execute(str_, {"name_us": basis_name})
        conn.close()

        # ~#~#~#~#~#~ #
        # R e t u r n #
        # ~#~#~#~#~#~ #

        return [str(i[0]) for i in c.fetchall()]

    def get_basis(self,
                  basis_name, elts=None,
                  handle_f_format="GAMESS-US", check_format=None):
        """
        Return the data from the basis set
        """

        # ~#~#~#~ #
        # I n i t #
        # ~#~#~#~ #

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # ~#~#~#~#~#~ #
        # F i l t e r #
        # ~#~#~#~#~#~ #

        cmd_filter_ele = " ".join(cond_sql_or("elt", elts)) if elts else "(1)"

        c.execute('''SELECT DISTINCT data from output_tab
                     WHERE name="{0}"
                     AND  {1}'''.format(basis_name, cmd_filter_ele))

        # We need to take i[0] because fetchall return a tuple [(value),...]
        l_atom_basis = [i[0].strip() for i in c.fetchall()]
        conn.close()

        # ~#~#~#~#~#~#~#~ #
        # h a n d l e _ f #
        # ~#~#~#~#~#~#~#~ #
        if handle_f_format:
            from src.parser import handle_f_dict
            try:
                f = handle_f_dict[self.format]
            except KeyError:
                str_ = "You cannot handle f function with {0} format"
                print >> sys.stderr, str_.format(self.format)
                print >> sys.stderr, "Choose in:"
                print >> sys.stderr, handle_f_dict.keys()
                sys.exit(1)
            else:
                l_atom_basis = f(l_atom_basis,self.get_list_symetry)

        # ~#~#~#~#~ #
        # C h e c k #
        # ~#~#~#~#~ #

        d_check = {"GAMESS-US": check_gamess,
                   "NWChem": check_NWChem}

        if check_format:
            try:
                f = d_check[self.format]
            except KeyError:
                str_ = """This format is not handle. Chose one of : {}"""
                print >>sys.stderr, str_.format(format(str(d_check.keys())))
                sys.exit(1)
            else:
                for atom_basis in l_atom_basis:
                    lines = atom_basis.split("\n")
                    for type_, _, _ in self.get_list_symetry(lines):
                        f(type_)

        # ~#~#~#~#~#~ #
        # R e t u r n #
        # ~#~#~#~#~#~ #
        return l_atom_basis
if __name__ == "__main__":

    e = EMSL_local(db_path="EMSL.db")
    l = e.get_list_basis_available()
    for i in l:
        print i

    l = e.get_list_element_available("pc-0")
    print l

    l = e.get_basis("cc-pVTZ", ["H", "He"])
    for i in l:
        print i
