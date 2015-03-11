import os
import sys
import re
import time
import sqlite3


def install_with_pip(name):

    ins = False
    d = {'y': True,
         'n': False}

    while True:
        choice = raw_input('Do you want to install it ? [Y/N]')
        try:
            ins = d[choice.lower()]
            break
        except:
            print "not a valid choice"

    if ins:
        try:
            import pip
            pip.main(['install', name])
        except:
            print "You need pip, (http://pip.readthedocs.org/en/latest/installing.html)"
            sys.exit(1)


class EMSL_dump:
    """
    This call implement all you need for download the EMSL and save it localy
    """

    format_dict = {"g94": "Gaussian94",
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
                   "aces2": "AcesII"
                   }

    def __init__(self, db_path=None, format="GAMESS-US", contraction="True"):
        self.db_path = db_path
        self.format = format
        self.contraction = str(contraction)
        self.debug = True

        try:
            import requests
        except:
            print "You need the requests package"
            install_with_pip("requests")
        finally:
            self.requests = requests

    def get_list_format(self):
        """List all the format available in EMSL"""
        return self.format_dict

    def set_db_path(self, path):
        """Define the database path"""
        self.db_path = path

    def get_dict_ele(self):
        """A dict of element"""
        elt_path = os.path.dirname(sys.argv[0]) + "/src/elts_abrev.dat"

        with open(elt_path, "r") as f:
            data = f.readlines()

        dict_ele = dict()
        for i in data:
            l = i.split("-")
            dict_ele[l[1].strip().lower()] = l[2].strip().lower()
        return dict_ele

    def dwl_basis_list_raw(self):
        print "Download all the name available in EMSL. It can take some time.",
        sys.stdout.flush()

        """Download the source code of the iframe who contains the list of the basis set available"""

        url = "https://bse.pnl.gov/bse/portal/user/anon/js_peid/11535052407933/panel/Main/template/content"
        if self.debug:
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
                xml_path = tup[0]
                name = tup[1]

                elts = re.sub('[["\ \]]', '', tup[3]).split(',')

                des = re.sub('\s+', ' ', tup[-1])

                if "-ecp" in xml_path.lower():
                    continue
                d[name] = [name, xml_path, des, elts]

        """Tric for the unicity of the name"""
        array = [d[key] for key in d]

        array_sort = sorted(array, key=lambda x: x[0])
        print len(array_sort), "basisset will be download"

        return array_sort

    def basis_data_row_to_array(self, data, name, des, elts):
        """Parse the basis data raw html to get a nice tuple"""

        d = []

        b = data.find("$DATA")
        e = data.find("$END")
        if (b == -1 or data.find("$DATA$END") != -1):
            if self.debug:
                print data
            raise Exception("WARNING not DATA")
        else:
            data = data.replace("PHOSPHOROUS", "PHOSPHORUS")
            data = data.replace("D+", "E+")
            data = data.replace("D-", "E-")

            data = data[b + 5:e - 1].split('\n\n')

            dict_ele = self.get_dict_ele()

            for (elt, data_elt) in zip(elts, data):

                elt_long_th = dict_ele[elt.lower()]
                elt_long_exp = data_elt.split()[0].lower()

                if "$" in data_elt:
                    if self.debug:
                        print "Eror",
                    raise Exception("WARNING bad split")

                if elt_long_th == elt_long_exp:
                    d.append([elt, data_elt.strip()])
                else:
                    if self.debug:
                        print "th", elt_long_th
                        print "exp", elt_long_exp
                        print "abv", elt
                    raise Exception("WARNING not good ELEMENT")

        return [name, des, d]

    def create_sql(self, list_basis_array):
        """Create the sql from the list of basis available data"""

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''CREATE TABLE basis_tab(
                            basis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name text,
                         description text,
                                UNIQUE(name)
                  );''')

        c.execute('''CREATE TABLE data_tab(
                           basis_id INTEGER,
                                elt TEXT,
                               data TEXT,
                    FOREIGN KEY(basis_id)
                    REFERENCES basis_tab(basis_id)
                    );''')

        c.execute(''' CREATE VIEW output_tab AS
                        SELECT basis_id,
                               name,
                               description,
                               elt,
                               data
                        FROM   basis_tab
                NATURAL JOIN   data_tab
                    ''')

        conn.commit()

        import Queue
        import threading

        num_worker_threads = 7
        attemps_max = 20

        q_in = Queue.Queue(num_worker_threads)
        q_out = Queue.Queue(num_worker_threads)

        def worker():
            """get a Job from the q_in, do stuff, when finish put it in the q_out"""
            while True:
                name, path_xml, des, elts = q_in.get()

                url = "https://bse.pnl.gov:443/bse/portal/user/anon/js_peid/11535052407933/action/portlets.BasisSetAction/template/courier_content/panel/Main/"
                url += "/eventSubmit_doDownload/true"

                params = {'bsurl': path_xml, 'bsname': name,
                          'elts': " ".join(elts),
                          'format': self.format,
                          'minimize': self.contraction}

                attemps = 0
                while attemps < attemps_max:
                    text = self.requests.get(url, params=params).text
                    try:
                        basis_data = self.basis_data_row_to_array(
                            text, name, des, elts)
                    except:
                        time.sleep(0.1)
                        attemps += 1
                    else:
                        break

                try:
                    q_out.put(basis_data)
                except:
                    if self.debug:
                        print "Fail on q_out.put", basis_data
                    raise
                else:
                    q_in.task_done()


        def enqueue():
            for [name, path_xml, des, elts] in list_basis_array:
                q_in.put([name, path_xml, des, elts])

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
            name, des, d = q_out.get()
            q_out.task_done()

            try:
                c.execute(
                    "INSERT INTO basis_tab(name,description) VALUES (?,?)", [
                        name, des])
                conn.commit()
            except sqlite3.IntegrityError:
                print '{:>3}'.format(i + 1), "/", nb_basis, name, "fail"

            id_ = c.lastrowid
            try:
                c.executemany(
                    "INSERT INTO data_tab VALUES (?,?,?)", [
                        [id_] + k for k in d])
                conn.commit()

                print '{:>3}'.format(i + 1), "/", nb_basis, name

            except:
                print '{:>3}'.format(i + 1), "/", nb_basis, name, "fail"
                raise

        conn.close()

        q_in.join()

    def new_db(self):
        """Create new_db from scratch"""

        _data = self.dwl_basis_list_raw()
        array_basis = self.bl_raw_to_array(_data)
        del _data

        self.create_sql(array_basis)
