# -*- coding: utf-8 -*-

import sqlite3
import re
import sys
import os

debug = True


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
        print "Dwl the basis list info",
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

        d = []

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

                d.append([name, url, des, elts])

        d_sort = sorted(d, key=lambda x: x[0])
        return d_sort

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
            print data
            raise StandardError("WARNING not DATA")
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
        q_in = Queue.Queue(num_worker_threads)
        q_out = Queue.Queue(num_worker_threads)

        basis_raw = {}

        def worker():
            while True:
                [name, url, des, elts] = q_in.get()
                url = self.create_url(url, name, elts)
                q_out.put(
                    ([name, url, des, elts], self.requests.get(url).text))
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

        for i in range(len(list_basis_array)):
            [name, url, des, elts], basis_raw = q_out.get()
            try:
                basis_data = self.basis_data_row_to_array(
                    basis_raw, name, des, elts)
                c.executemany(
                    "INSERT INTO all_value VALUES (?,?,?,?)", basis_data)
                conn.commit()
                print i, name
            except:
                print name, url, des, elts
                pass
        conn.close()
        q_in.join()
        q_out.join()

    def new_db(self):
        """Create new_db from scratch"""

        _data = self.dwl_basis_list_raw()
        array_basis = self.bl_raw_to_array(_data)
        del _data

        self.create_sql(array_basis)


class EMSL_local:

    def __init__(self, db_path=None):
        self.db_path = db_path

    def get_list_basis_available(self):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT DISTINCT name from all_value")
        data = c.fetchall()

        data = [i[0] for i in data]

        conn.close()
        return data

    def get_list_element_available(self, basis_name):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT DISTINCT elt from all_value WHERE name=:name_us COLLATE NOCASE",
                  {"name_us": basis_name})

        data = c.fetchall()

        data = [str(i[0]) for i in data]

        conn.close()
        return data

    def get_basis(self, basis_name, elts):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        d = []

        for elt in elts:
            c.execute("SELECT DISTINCT data from all_value WHERE name=:name_cur COLLATE NOCASE AND elt=:elt_cur COLLATE NOCASE",
                      {"name_cur": basis_name,
                       "elt_cur": elt})

            data = c.fetchone()
            d.append(data[0])

        conn.close()
        return d

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
