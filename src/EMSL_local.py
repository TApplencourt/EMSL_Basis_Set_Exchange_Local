# -*- coding: utf-8 -*-

import sqlite3
import re
import sys
import os

from misc.sqlit import connect4git

def checkSQLite3(db_path):
    """Check if the db_path is a good one"""

    from os.path import isfile, getsize

    db_path = os.path.expanduser(db_path)
    db_path = os.path.expandvars(db_path)
    db_path = os.path.abspath(db_path)

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
        EMSL_local(db_path=db_path).list_basis_available()
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
        EMSL_local(db_path=db_path).list_basis_available()
    except:
        print >>sys.stderr, "Sorry..."
        os.system("rm -f /dev/shm/%d.db" % (os.getpid()))
        raise
    else:
        print >>sys.stderr, "Working !"
        changed = True
        return db_path, changed


def cond_sql_or(table_name, l_value, glob=False):
    """Take a table_name, a list of value and create the sql 'or' commande
       for example : (elt = "Na" OR elt = "Mg")"""

    opr = "GLOB" if glob else "="

    l_cmd = ['{0} {1} "{2}"'.format(table_name, opr, val) for val in l_value]

    return "({0})".format(" OR ".join(l_cmd))


def string_to_nb_mo(str_type):
    """Take a string and return the nb of orbital"""

    d = {"S": 3,
         "P": 5,
         "D": 7,
         "SP": 8}

    if str_type in d:
        return d[str_type]
    # ord("F") = 70 and ord("Z") = 87
    elif 70 <= ord(str_type) <= 87:
        # ord("F") = 70 and l = 4 so ofset if 66
        return 2 * (ord(str_type) - 66) + 1
    else:
        raise BaseException

#  _       __
# |_ |\/| (_  |    |   _   _  _. |
# |_ |  | __) |_   |_ (_) (_ (_| |
#
class EMSL_local(object):

    """
    All the method for using the EMSL db localy
    """

    def __init__(self, db_path=None, db_dump_path=None):

#        print db_path
#        print db_dump_path

        if db_path:
            self.conn = sqlite3.connect(db_path)
        if db_dump_path:
            self.conn = connect4git(db_dump_path)

        self.c = self.conn.cursor()

        self.c.execute("SELECT * from format_tab")
        self.format = self.c.fetchone()[0]

    def list_basis_available(self,
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

        # ~#~#~#~#~#~ #
        # F i l t e r #
        # ~#~#~#~#~#~ #

        if basis:
            cmd_filter_basis = cond_sql_or("name", basis, glob=True)
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
            self.c.execute(cmd, elts)

            l_basis_id = [i[0] for i in self.c.fetchall()]

            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~ #
            # C r e a t e _ t h e _ c m d #
            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~ #

            cmd_filter_basis = cond_sql_or("basis_id", l_basis_id)
            cmd_filter_ele = cond_sql_or("elt", elts)

            column_to_fech = "name, description"
            if average_mo_number:
                column_to_fech += ", data"

            filter_where = " ({0}) AND ({1})".format(cmd_filter_ele,
                                                     cmd_filter_basis)

            cmd = """SELECT DISTINCT {0}
                     FROM output_tab
                     WHERE {1}
                     ORDER BY name""".format(column_to_fech, filter_where)
        # ~#~#~#~#~ #
        # F e t c h #
        # ~#~#~#~#~ #

        self.c.execute(cmd)
        info = self.c.fetchall()

        # ~#~#~#~#~#~#~ #
        # P a r s i n g #
        # ~#~#~#~#~#~#~ #
        # If average_mo_number is asking

        from misc.collections import OrderedDict
        dict_info = OrderedDict()
        # Description : dict_info[name] = [description, nb_mo, nb_ele]

        from src.parser_handler import get_symmetry_function
        if average_mo_number:

            f_symmetry = get_symmetry_function(self.format)

            for name, description, atom_basis in info:

                nb_mo = 0

                line = atom_basis.split("\n")

                for type_, _, _ in f_symmetry(line):

                    nb_mo += string_to_nb_mo(type_)
                try:
                    dict_info[name][1] += nb_mo
                    dict_info[name][2] += 1.
                except KeyError:
                    dict_info[name] = [description, nb_mo, 1.]

        # ~#~#~#~#~#~ #
        # R e t u r n #
        # ~#~#~#~#~#~ #

        if average_mo_number:
            return[[k, v[0], str(v[1] / v[2])] for k, v in dict_info.iteritems()]
        else:
            return [i[:] for i in info]

    def get_list_element_available(self, basis_name):

        # ~#~#~#~#~#~ #
        # F i l t e r #
        # ~#~#~#~#~#~ #

        str_ = """SELECT DISTINCT elt
                  FROM output_tab
                  WHERE name=(?) COLLATE NOCASE"""

        # ~#~#~#~#~ #
        # F e t c h #
        # ~#~#~#~#~ #

        self.c.execute(str_, basis_name)

        # ~#~#~#~#~#~ #
        # R e t u r n #
        # ~#~#~#~#~#~ #

        return [str(i[0]) for i in self.c.fetchall()]

    def get_basis(self,
                  basis_name, elts=None,
                  handle_l_format=False, check_format=None):
        """
        Return the data from the basis set
        basis_name : The value of 'name'raw from output_tab in the SQL database
        elts : List of element avalaible in 'elt'raw
        handle_l_format : If you want to use special treatement for SP function
                        (see src.parser_handler.get_handle_l_function)
        check_format : If you want to verify some condition for special program
                       (see src.parser.check_validity)
        """

        # ~#~#~#~#~#~ #
        # F i l t e r #
        # ~#~#~#~#~#~ #

        cmd_filter_ele = cond_sql_or("elt", elts) if elts else "(1)"

        self.c.execute('''SELECT DISTINCT data from output_tab
                     WHERE name LIKE "{0}"
                     AND  ({1})'''.format(basis_name, cmd_filter_ele))

        # We need to take i[0] because fetchall return a tuple [(value),...]
        l_atom_basis = [i[0].strip() for i in self.c.fetchall()]

        # ~#~#~#~#~#~#~#~ #
        # h a n d l e _ f #
        # ~#~#~#~#~#~#~#~ #
        if handle_l_format:
            from src.parser_handler import get_handle_l_function
            f = get_handle_l_function(self.format)
            l_atom_basis = f(l_atom_basis)

        # ~#~#~#~#~ #
        # C h e c k #
        # ~#~#~#~#~ #

        if check_format:

                from src.parser_handler import get_symmetry_function
                from src.parser_handler import get_check_function

                f = get_check_function(check_format)
                f_symmetry = get_symmetry_function(self.format)

                for atom_basis in l_atom_basis:
                    lines = atom_basis.split("\n")
                    for type_, _, _ in f_symmetry(lines):
                        try:
                            f(type_)
                        except AssertionError:
                            print "False. You have somme special function like SP"
                            sys.exit(1)
                        except BaseException:
                            print "Fail !"
                            sys.exit(1)

        # ~#~#~#~#~#~ #
        # R e t u r n #
        # ~#~#~#~#~#~ #
        return l_atom_basis
