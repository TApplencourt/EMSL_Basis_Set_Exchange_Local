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

    opr = "GLOB" if glob else "="

    l = []
    dmy = " OR ".join(['%s %s "%s"' % (table_name, opr, i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l


def string_to_nb_mo(str_l):

    assert len(str_l) == 1

    d = {"S": 3,
         "P": 5,
         "D": 7,
         "F": 9,
         "L": 8}

    if str_l in d:
        return d[str_l]
    # ord("G") = 72 and ord("Z") = 87
    elif 72 <= ord(str_l) <= 87:
        # orf("G") = 72 and l = 4 so ofset if 68
        return 2 * (ord(str_l) - 68) + 1
    else:
        raise BaseException


class EMSL_local:
    """
    All the method for using the EMSL db localy
    """

    import re

    def __init__(self, db_path=None):
        self.db_path = db_path
        self.p = re.compile(ur'^(\w)\s+\d+\b')

    def get_list_type(self, atom_basis):
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
        # If not elts just get the disctinct name
        # Else: 1) fetch for geting the run_id available
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

        # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #
        # G e t i n g   B a s i s _ i d #
        # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #

        if basis:
            cmd_basis = " ".join(cond_sql_or("name", basis, glob=True))
        else:
            cmd_basis = "(1)"

        if not elts:

            if not average_mo_number:
                cmd = """SELECT DISTINCT name, description
                         FROM basis_tab
                         WHERE {0}"""
            else:
                cmd = """SELECT DISTINCT name, description, data
                         FROM output_tab
                         WHERE {0}"""

            cmd = cmd.format(cmd_basis)

        else:
            str_ = """SELECT DISTINCT basis_id
                      FROM output_tab
                      WHERE elt=? AND {0}""".format(cmd_basis)

            cmd = " INTERSECT ".join([str_] * len(elts)) + ";"
            c.execute(cmd, elts)

            dump = [i[0] for i in c.fetchall()]
            cmd_basis = " ".join(cond_sql_or("basis_id", dump))
            cmd_ele = " ".join(cond_sql_or("elt", elts))

            cmd = """SELECT DISTINCT {0}
                     FROM output_tab
                     WHERE {1}
                     ORDER BY name"""

            if average_mo_number:
                column = "name, description, data"
            else:
                column = "name, description"

            filter_ = cmd_ele + " AND " + cmd_basis

            cmd = cmd.format(column, filter_)

        c.execute(cmd)
        info = c.fetchall()

        conn.close()

        # ~#~#~#~#~#~#~ #
        # P a r s i n g #
        # ~#~#~#~#~#~#~ #

        from collections import OrderedDict
        dict_info = OrderedDict()
        # Description : dict_info[name] = [description, nb_mo, nb_ele]

        if average_mo_number:
            for name, description, data in info:
                nb_mo = 0
                for line in data.split("\n")[1:]:
                    str_l = line.split()[0]
                    try:
                        nb_mo += string_to_nb_mo(str_l)
                    except BaseException:
                        pass

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

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        str_ = "SELECT DISTINCT elt from output_tab WHERE name=:name_us COLLATE NOCASE"
        c.execute(str_, {"name_us": basis_name})

        data = c.fetchall()

        data = [str(i[0]) for i in data]

        conn.close()
        return data

    def get_basis(self, basis_name, elts=None, with_l=False):
        """
        Return the data from the basis set
        """

        #  __            _
        # /__  _ _|_   _|_ ._ _  ._ _     _  _. |
        # \_| (/_ |_    |  | (_) | | |   _> (_| |
        #                                     |
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if elts:
            cmd_ele = "AND " + " ".join(cond_sql_or("elt", elts))
        else:
            cmd_ele = ""

        c.execute('''SELECT DISTINCT data from output_tab
                   WHERE name="{basis_name}" COLLATE NOCASE
                   {cmd_ele}'''.format(basis_name=basis_name,
                                       cmd_ele=cmd_ele))

        l_data_raw = c.fetchall()
        conn.close()

        # |_|  _. ._   _| |  _    || | ||
        # | | (_| | | (_| | (/_      |_
        #

        l_data = []

        for data_raw in l_data_raw:

            basis = data_raw[0].strip()

            l_line_raw = basis.split("\n")

            # l_line_raw[0] containt the name of the Atom
            l_line = [l_line_raw[0]]

            for symmetry, begin, end in self.get_list_type(l_line_raw):

                if not(with_l) and symmetry in "L":

                    body_s = []
                    body_p = []

                    for i_l in l_line_raw[begin + 1:end]:

                        # one L =>  S & P
                        a = i_l.split()

                        common = "{:>3}".format(a[0])
                        common += "{:>15.7f}".format(float(a[1]))

                        tail_s = common + "{:>23.7f}".format(float(a[2]))
                        body_s.append(tail_s)

                        # Is only a whan only 3 elements, coef for p == coef for s
                        try:
                            tail_p = common + "{:>23.7f}".format(float(a[3]))
                        except IndexError:
                            tail_p = tail_s
                        finally:
                            body_p.append(tail_p)

                    l_line += [l_line_raw[begin].replace("L", "S")]
                    l_line += body_s

                    l_line += [l_line_raw[begin].replace("L", "P")]
                    l_line += body_p
                else:
                    l_line += l_line_raw[begin:end]

            l_data.append("\n".join(l_line))

        return l_data

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
