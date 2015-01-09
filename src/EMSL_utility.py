# -*- coding: utf-8 -*-

import sqlite3
import re
import sys
import os
import time

debug = False


def cond_sql_or(table_name, l_value):

    l = []
    dmy = " OR ".join(['%s = "%s"' % (table_name, i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l


class EMSL_dump:

    def __init__(self, db_path=None, format="GAMESS-US", contraction="True"):
        self.db_path = db_path
        self.format = format
        self.contraction = str(contraction)

        import requests
        self.requests = requests

    def set_db_path(self, path):
        """Define the database path"""
        self.db_path = path

    def dwl_basis_list_raw(self):
        print "Download all the name available in EMSL. It can take some time.",
        sys.stdout.flush()

        """Download the source code of the iframe who contains the list of the basis set available"""

        url = "https://bse.pnl.gov/bse/portal/user/anon/js_peid/11535052407933/panel/Main/template/content"
        if debug:
            import cPickle as pickle
            dbcache = 'db/cache'
            if not os.path.isfile(dbcache):
                page = self.requests.get(url).text
                file = open(dbcache, 'w')
                pickle.dump(page, file)
            else:
                file = open(dbcache, 'r')
                page = pickle.load(file)
            file.close()

        else:
            page = self.requests.get(url).text

        print "Done"
        return page

    def bl_raw_to_array(self, data_raw):
        """Parse the raw html to create a basis set array whith all the info:
        url, name,description"""

        d = {}

        for line in data_raw.split('\n'):
            if "new basisSet(" in line:
                b = line.find("(")
                e = line.find(");")

                s = line[b + 1:e]

                tup = eval(s)
                url = tup[0]
                name = tup[1]

                junkers = re.compile('[[" \]]')
                elts = junkers.sub('', tup[3]).split(',')

                des = tup[-1]

                if "-ecp" in url.lower():
                    continue
                d[name] = [name, url, des, elts]

        """Tric for the unicity of the name"""
        array = [d[key] for key in d]

        array_sort = sorted(array, key=lambda x: x[0])
        print len(array_sort), "basisset will be download"

        return array_sort

    def create_url(self, url, name, elts):
        """Create the adequate url to get the basis data"""

        elts_string = " ".join(elts)

        path = "https://bse.pnl.gov:443/bse/portal/user/anon/js_peid/11535052407933/action/portlets.BasisSetAction/template/courier_content/panel/Main/"
        path += "/eventSubmit_doDownload/true"
        path += "?bsurl=" + url
        path += "&bsname=" + name
        path += "&elts=" + elts_string
        path += "&format=" + self.format
        path += "&minimize=" + self.contraction
        return path

    def basis_data_row_to_array(self, data, name, des, elts):
        """Parse the basis data raw html to get a nice tuple"""

        d = []

        b = data.find("$DATA")
        e = data.find("$END")
        if (b == -1 or data.find("$DATA$END") != -1):
            if debug:
                print data
            raise Exception("WARNING not DATA")
        else:
            data = data[b + 5:e].split('\n\n')
            for (elt, data_elt) in zip(elts, data):

                d.append((name, des, elt, data_elt))

        return d

    def create_sql(self, list_basis_array):
        """Create the sql from the list of basis available data"""

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create table
        c.execute('''CREATE TABLE all_value
                 (name text, description text, elt text, data text)''')

        import Queue
        import threading

        num_worker_threads = 7
        num_try_of_dwl = 2

        q_in = Queue.Queue(num_worker_threads)
        q_out = Queue.Queue(num_worker_threads)

        def worker():
            """get a Job from the q_in, do stuff, when finish put it in the q_out"""
            while True:
                [name, url, des, elts] = q_in.get()
                url = self.create_url(url, name, elts)

                for i in range(num_try_of_dwl):
                    text = self.requests.get(url).text
                    try:
                        basis_data = self.basis_data_row_to_array(
                            text, name, des, elts)
                        break
                    except:
                        time.sleep(0.1)
                        pass

                q_out.put(([name, url, des, elts], basis_data))
                q_in.task_done()

        def enqueue():
            for [name, url, des, elts] in list_basis_array:
                q_in.put(([name, url, des, elts]))

            return 0

        t = threading.Thread(target=enqueue)
        t.daemon = True
        t.start()

        for i in range(num_worker_threads):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()

        nb_basis = len(list_basis_array)

        for i in range(nb_basis):
            [name, url, des, elts], basis_data = q_out.get()

            try:
                c.executemany(
                    "INSERT INTO all_value VALUES (?,?,?,?)", basis_data)
                conn.commit()

                print '{:>3}'.format(i + 1), "/", nb_basis, name
            except:
                print '{:>3}'.format(i + 1), "/", nb_basis, name, "fail",
                print '   ', [url, des, elts]
                raise
        conn.close()

        q_in.join()

    def new_db(self):
        """Create new_db from scratch"""

        _data = self.dwl_basis_list_raw()
        array_basis = self.bl_raw_to_array(_data)
        del _data

        self.create_sql(array_basis)


class EMSL_local:

    def __init__(self, db_path=None):
        self.db_path = db_path

    def get_list_basis_available(self, elts=[]):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if not elts:

            c.execute("SELECT DISTINCT name,description from all_value")
            data = c.fetchall()

        else:
            cmd = [
                "SELECT name,description FROM all_value WHERE elt=?"] * len(elts)
            cmd = " INTERSECT ".join(cmd) + ";"

            c.execute(cmd, elts)
            data = c.fetchall()

        data = [i[:] for i in data]

        conn.close()

        return data

    def get_list_element_available(self, basis_name):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            "SELECT DISTINCT elt from all_value WHERE name=:name_us COLLATE NOCASE", {
                "name_us": basis_name})

        data = c.fetchall()

        data = [str(i[0]) for i in data]

        conn.close()
        return data

    def get_basis(self, basis_name, elts=None, with_l=False):

        def get_list_type(l_line):
            l = []
            for i, line in enumerate(l_line):

                m = re.search(p, line)
                if m:
                    l.append([m.group(1), i])
                    try:
                        l[-2].append(i)
                    except IndexError:
                        pass

            l[-1].append(i + 1)
            return l

        import re

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

        c.execute('''SELECT DISTINCT data from all_value
                   WHERE name="{basis_name}" COLLATE NOCASE
                   {cmd_ele}'''.format(basis_name=basis_name,
                                       cmd_ele=cmd_ele))

        l_data_raw = c.fetchall()
        conn.close()

        # |_|  _. ._   _| |  _    || | ||
        # | | (_| | | (_| | (/_      |_
        #

        p = re.compile(ur'^(\w)\s+\d+\b')

        l_data = []

        for data_raw in l_data_raw:

            basis = data_raw[0].strip()

            l_line_raw = basis.split("\n")

            l_line = [l_line_raw[0]]

            for type_, begin, end in get_list_type(l_line_raw):

                if not(with_l) and type_ in "L":

                    body_s = body_p = []

                    for i_l in l_line_raw[begin + 1:end]:
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


format_dict = \
    {
        "g94": "Gaussian94",
        "gamess-us": "GAMESS-US",
        "gamess-uk": "GAMESS-UK",
        "turbomole": "Turbomole",
        "tx93": "TX93",
        "molpro": "Molpro",
        "molproint": "MolproInt",
        "hondo": "Hondo",
        "supermolecule": "SuperMolecule",
        "molcas": "Molcas",
        "hyperchem": "HyperChem",
        "dalton": "Dalton",
        "demon-ks": "deMon-KS",
        "demon2k": "deMon2k",
        "aces2": "AcesII",
    }

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
