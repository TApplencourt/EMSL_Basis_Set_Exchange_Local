import os
import sys
import re
import time
import sqlite3

from collections import OrderedDict
from src.parser import format_dict


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
            print "You need pip"
            print "(http://pip.readthedocs.org/en/latest/installing.html)"
            sys.exit(1)


class EMSL_dump:

    """
    This call implement all you need for download the EMSL and save it localy
    """

    def __init__(self, db_path=None, format="GAMESS-US", contraction="True"):
        self.db_path = db_path

        if format not in format_dict:
            print >> sys.stderr, "Format {0} doesn't exist. Choose in:".format(format)
            print >> sys.stderr, format_dict.keys()
            sys.exit(1)
        else:
            self.format = format

            if format_dict[self.format]:
                self.parser = format_dict[self.format]
            else:
                print >> sys.stderr, "We have no parser for this format"
                print >> sys.stderr, "Fill free to Fock /pull request"
                print >> sys.stderr, "You just need to add a function like"
                print >> sys.stderr, "'parse_basis_data_gamess_us' to parse you'r format"

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
        return format_dict

    def set_db_path(self, path):
        """Define the database path"""
        self.db_path = path

    def dwl_basis_list_raw(self):
        """Return the source code of the iframe
           who contains the list of the basis set available"""

        print "Download all the name available in EMSL."
        print "It can take some time.",
        sys.stdout.flush()

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

    def basis_list_raw_to_array(self, data_raw):
        """Parse the raw html basis set to create a dict
           will all the information for dowloanding the database :
        Return d[name] = [name, xml_path, description,
                          lits of the elements available]

         Explanation of tuple data from 'tup' by index:

         0 - path to xml file
         1 - basis set name
         2 - categorization: "dftcfit", "dftorb", "dftxfit", "diffuse",
                "ecporb","effective core potential", "orbital", "polarization",
                "rydberg", or "tight"
         3 - parameterized elements by symbol e.g. '[H, He, B, C, N, O, F, Ne]'
         4 - curation status; only 'published' is trustworthy
         5 - boolean: has ECP
         6 - boolean: has spin
         7 - last modified date
         8 - name of primary developer
         9 - name of contributor
        10 - human-readable summary/description of basis set
        """

        d = OrderedDict()

        for line in data_raw.split('\n'):

            if "new basisSet(" in line:
                b = line.find("(")
                e = line.find(");")

                s = line[b + 1:e]

                tup = eval(s)

                xml_path = tup[0]

                # non-published (e.g. rejected) basis sets and ecp should be
                # ignored
                if tup[4] != "published" or "-ecp" in xml_path.lower():
                    continue

                name = tup[1]
                elts = re.sub('[["\ \]]', '', tup[3]).split(',')
                des = re.sub('\s+', ' ', tup[-1])

                d[name] = [name, xml_path, des, elts]

        return d



    #  _____                _
    # /  __ \              | |
    # | /  \/_ __ ___  __ _| |_ ___
    # | |   | '__/ _ \/ _` | __/ _ \
    # | \__/\ | |  __/ (_| | ||  __/
    #  \____/_|  \___|\__,_|\__\___|
    #
    def create_sql(self, dict_basis_list):
        """Create the sql from strach.
            Take the list of basis available data,
            download her, put her in sql"""

        if os.path.isfile(self.db_path):
            print >> sys.stderr, "FAILLURE:"
            print >> sys.stderr, "{0} file alredy exist.".format(self.db_path),
            print >> sys.stderr, "Delete or remove it"
            sys.exit(1)

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

        import Queue
        import threading

        num_worker_threads = 7
        attemps_max = 20

        q_in = Queue.Queue(num_worker_threads)
        q_out = Queue.Queue(num_worker_threads)

        def worker():
            """get a Job from the q_in, do stuff,
               when finish put it in the q_out"""
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
                        basis_data = self.parser(text, name, des, elts,
                                                 self.debug)
                    except:
                        if self.debug:
                            raise
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
            for [name, path_xml, des, elts] in dict_basis_list.itervalues():
                q_in.put([name, path_xml, des, elts])

            return 0

        t = threading.Thread(target=enqueue)
        t.daemon = True
        t.start()

        for i in range(num_worker_threads):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()

        nb_basis = len(dict_basis_list)

        for i in range(nb_basis):
            name, des, basis_data = q_out.get()
            q_out.task_done()

            str_indice = '{:>3}'.format(i + 1)
            str_ = '{0} / {1} | {2}'.format(str_indice, nb_basis, name)

            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #
            # A d d _ t h e _ b a s i s _ n a m e #
            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #
            try:
                cmd = "INSERT INTO basis_tab(name,description) VALUES (?,?)"
                c.execute(cmd, [name, des])
                conn.commit()
            except sqlite3.IntegrityError:
                print str_, "Fail"

            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #
            # A d d _ t h e _ b a s i s _ d a t a #
            # ~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~ #

            id_ = [c.lastrowid]

            try:
                cmd = "INSERT INTO data_tab(basis_id,elt,data) VALUES (?,?,?)"
                c.executemany(cmd, [id_ + k for k in basis_data])
                conn.commit()
            except sqlite3.IntegrityError:
                print str_, "Fail"
            else:
                print str_
        conn.close()

        q_in.join()

    def new_db(self):
        """Create new_db from scratch"""

        _data = self.dwl_basis_list_raw()
        array_basis = self.basis_list_raw_to_array(_data)

        self.create_sql(array_basis)
