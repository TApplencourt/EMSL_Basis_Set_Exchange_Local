#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    import sqlite3
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)


#
#  _____         _  _  _
# /  ___|       | |(_)| |
# \ `--.   __ _ | | _ | |_
#  `--. \ / _` || || || __|
# /\__/ /| (_| || || || |_
# \____/  \__, ||_||_| \__|
#            | |
#            |_|
# You cannot Diff / Merge sqlite binary file. But you can dump it into
# a plain text file with contain the list of command needed to recreate
# the db_file.
#   (`sqlite3 db_file .dump > dump_file` For a example of dump file, see below
#    in the main section)
#
# This dump_file can be added to your git.
#
# This module ensure the coherencies between the db_file and the dump_file

class ConnectionForGit(sqlite3.Connection):

    """
    A sqlite3 connection for Git. It will always dumps the db when needed.
        (`sqlite3 db_file .dump > dump_file`)
    so now you can add dump_path to your git and work with the db like always.
    The main idea is:
        - When you create a sqlite3 connection: create or update the .db file
        - When you commit: update the .dump file
    /!\ If you create a table, you -maybe- need to make a dummy commit
            for update the dump
    """

    def __init__(self, db_path, dump_path, *args, **kwargs):
        super(ConnectionForGit, self).__init__(db_path, *args, **kwargs)
        self.db_path = db_path
        self.dump_path = dump_path

    def commit(self):
        '''
        0/ Update the DB if needed
             (aka if the dump is more recent than the db)
        1/ Commit in the DB
        2/ Dump the DB
             (`sqlite3 db_file .dump > dump_file`)
        '''
        try:
            ConnectionForGit.dump_to_sqlite(self.dump_path, self.db_path)
            sqlite3.Connection.commit(self)
        except sqlite3.Error:
            raise
        else:
            ConnectionForGit.sqlite_to_dump(self.db_path, self.dump_path)

    @staticmethod
    def isSQLite3(filename):
        """
        Verify is filename is a SQLite3 format db
        """
        from os.path import isfile, getsize

        if not isfile(filename):
            return False
        # SQLite database file header is 100 bytes
        if getsize(filename) < 100:
            return False

        with open(filename, 'rb') as fd:
            header = fd.read(100)

        if header[:16] == 'SQLite format 3\x00':
            return True
        else:
            return False

    @staticmethod
    def dump_to_sqlite(dump_path, db_path):
        """
        Take a dump and populate the db if the dump is the most recent
        0/ If no .dump file touch it
        1/ If no .db  file populate it
        2/ Check the date a modify accordingly
        """
        if not os.path.isfile(dump_path):
            os.system('touch {0}'.format(dump_path))
        if not os.path.isfile(db_path):
            os.system("sqlite3 {0} < {1}".format(db_path, dump_path))
        else:
            dump_time = os.path.getmtime(dump_path)
            db_time = os.path.getmtime(db_path)
            if dump_time > db_time:
                os.system("rm {0}".format(db_path))
                os.system("sqlite3 {0} < {1}".format(db_path, dump_path))

    @staticmethod
    def sqlite_to_dump(db_path, dump_path):
        """
        Take a db and dump it if the db is the most recent
        """

        if not ConnectionForGit.isSQLite3(db_path):
            raise sqlite3.Error

        dump_time = os.path.getmtime(dump_path)
        db_time = os.path.getmtime(db_path)
        if db_time > dump_time:
            os.system("sqlite3 {0} .dump > {1}".format(db_path, dump_path))
            os.system("touch {0}".format(db_path))


def connect4git(dump_path, db_path=None, *args, **kwargs):
    '''
    dump_path :  Is the sqlite dump file you will monitor with git.
    db_path   :  Is the <<dummy>> sqlite3 file.

    0/ Update and create the db if needed
            (aka if the dump is more recent than the db)
    1/ Return a connection the db (a ConnectionForGit instance)
    '''

    if not db_path:
        db_path = "{0}.db".format(os.path.splitext(dump_path)[0])

    try:
        ConnectionForGit.dump_to_sqlite(dump_path, db_path)
    except:
        raise
    else:
        return ConnectionForGit(db_path, dump_path, *args, **kwargs)


# ___  ___      _
# |  \/  |     (_)
# | .  . | __ _ _ _ __
# | |\/| |/ _` | | '_ \
# | |  | | (_| | | | | |
# \_|  |_/\__,_|_|_| |_|
#
if __name__ == "__main__":
    # From the famous http://zetcode.com/db/sqlitepythontutorial/

    # It will create a test.dump and a test.db
    # You can git add the test.dump and do your work like always in the db.
    con = connect4git('test.dump')

    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE Cars(Id INT, Name TEXT, Price INT)")
        cur.execute("INSERT INTO Cars VALUES(1,'Audi',52642)")
        cur.execute("INSERT INTO Cars VALUES(2,'Mercedes',57127)")
        cur.execute("INSERT INTO Cars VALUES(3,'Skoda',9000)")
        cur.execute("INSERT INTO Cars VALUES(4,'Volvo',29000)")
        cur.execute("INSERT INTO Cars VALUES(5,'Bentley',350000)")
        cur.execute("INSERT INTO Cars VALUES(6,'Citroen',21000)")
        cur.execute("INSERT INTO Cars VALUES(7,'Hummer',41400)")
        cur.execute("INSERT INTO Cars VALUES(8,'Volkswagen',21600)")

    #  Test.db :
    #
    #  PRAGMA foreign_keys=OFF;
    #  BEGIN TRANSACTION;
    #  CREATE TABLE Cars(Id INT, Name TEXT, Price INT);
    #  INSERT INTO "Cars" VALUES(1,'Audi',52642);
    #  INSERT INTO "Cars" VALUES(2,'Mercedes',57127);
    #  INSERT INTO "Cars" VALUES(3,'Skoda',9000);
    #  INSERT INTO "Cars" VALUES(4,'Volvo',29000);
    #  INSERT INTO "Cars" VALUES(5,'Bentley',350000);
    #  INSERT INTO "Cars" VALUES(6,'Citroen',21000);
    #  INSERT INTO "Cars" VALUES(7,'Hummer',41400);
    #  INSERT INTO "Cars" VALUES(8,'Volkswagen',21600);
    #  COMMIT;
