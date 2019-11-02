import sqlite3
import pandas as pd
import xlrd
import datetime
import time
import logging as log
from threading import Thread
import os, sys


class EmptyPlacerholder():
    def __init__(self):
        pass


class DatabaseManager(Thread):

    def __init__(self, file=":memory:", timeout=2, *arg):
        super().__init__()
        self.file = file
        self.timeout = timeout # timeout in seconds

        self.command_stack = []
        self.outvalues = {}

    def execute(self, command, timeout=-99999):
        timeout = self.timeout if timeout == -99999 else timeout
        temp_key = time.time()
        n = temp_key + self.timeout
        local_empty = EmptyPlacerholder()

        self.outvalues[temp_key] = local_empty
        self.command_stack.append((temp_key, command))


        while self.outvalues[temp_key] == local_empty: # waits till command executed
            if time.time() > n: # it took too long
                raise TimeoutError("Timed out while waiting for serialised database interaction.")

        temp_out = self.outvalues[temp_key]
        self.outvalues.pop(temp_key) # clear value from dict

        return temp_out

    def commit(self):
        self.execute(":x:x:commit:x:x:")

    def run(self): # auto colled on Thread start
        self.conn = sqlite3.connect(self.file)
        self.crsr = self.conn.cursor()

        while True:
            for i in self.command_stack:
                try:
                    current = self.command_stack.pop(0)
                    if current[1] == ":x:x:commit:x:x:":
                        self.outvalues[current[0]] = self.conn.commit()
                        log.debug("Commit to db")
                        continue

                    log.debug("{0: <12} {1} {2}".format("Running: ", current[0], current[1].replace("            ", " ").replace("\n", "\n       ")))

                    ee = None

                    try:
                        self.crsr.execute(current[1])
                    except Exception as e:
                        # print("before e.args")
                        # print(e.args)
                        if "UNIQUE constraint failed:" in e.args[0]:
                            log.error("{0: <12} {1}, {2}".format("Record not unique: ",str(e.args[0]), str(current[1])))
                        elif "FOREIGN KEY constraint failed" in e.args[0]:
                            log.error("{0: <12} {1}, {2}".format("Student or event does not exist: ",str(e.args[0]), str(current[1])))
                        else:
                            raise e

                    self.outvalues[current[0]] = self.crsr.fetchall()

                except Exception as e:
                    self.outvalues[current[0]] = e
                    raise e


class connection():
    def __init__(self, database='test.db'):

        path_for_logs = ("db/logs/%s/%s"%(datetime.date.today().year ,datetime.date.today().month))
        try:
            os.makedirs(path_for_logs)
        except:
            pass

        self.log = log.basicConfig(filename='db/logs/%s/%s/%s-%s.log'%(datetime.date.today().year ,datetime.date.today().month, datetime.date.today(), os.path.basename(__file__)[:-3]), level=log.DEBUG, format='%(asctime)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')

        self.c = DatabaseManager(database, timeout=2)
        self.c.start()
        log.info("started db thread")
        self.c.execute("PRAGMA foreign_keys = ON;")
        self.create_db()


    def commit(self):
        try:
            self.c.commit()
        except Exception as e:
            raise e
            log.error("Database: Commit error.")

    def create_db(self):

        sql_command = """CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_last TEXT,
            name_first TEXT,
            gender TEXT,
            year INTEGER,
            house TEXT,
            dob INTEGER,
            student_id INTEGER DEFAULT NULL,
            UNIQUE(student_id));"""
        self.c.execute(sql_command)

        sql_command = """CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            name TEXT,
            track_feild TEXT,
            timed_score_distance INTEGER,
            gender TEXT);"""
        self.c.execute(sql_command)

        sql_command = """CREATE TABLE IF NOT EXISTS results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            event_id INTEGER,
            result REAL DEFAULT NULL,
            UNIQUE(student_id, event_id),
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (event_id) REFERENCES events (id));"""
        self.c.execute(sql_command)

        self.commit()
        log.info("%s: created databases" % __name__)

    def insert_into_results(self, data):
        # sql_command = """CREATE TABLE IF NOT EXISTS results(
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     student_id INTEGER,
        #     event_id INTEGER,
        #     result REAL DEFAULT NULL,
        #     UNIQUE(student_id, event_id));"""
        # print(data)
        self.c.execute("INSERT INTO results VALUES (NULL, %s, %s, %s)"%data)
        self.commit()

    def add_event(self, data):
        self.c.execute("INSERT INTO events VALUES (NULL, \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" %(data))
        log.info("{0: <12} {1}".format("Event added:",str(data)))
        self.commit()

    def get_events(self):
        return self.c.execute("SELECT * FROM events")

    def get_dates(self):
        return self.c.execute("SELECT dob FROM students")

    def add_student(self, data):
        # self.c.execute("INSERT INTO students VALUES (NULL, \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % tuple(data))
        self.c.execute("INSERT INTO students VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)" % tuple(data))

    def data_entry(self):
        # “The real problem is that programmers have spent far too much time worrying about efficiency in the wrong places
        # and at the wrong times; premature optimization is the root of all evil (or at least most of it) in programming.” - Donald Knuth


        read_file = (pd.read_excel('db/Book1.xlsx'))
        df = pd.DataFrame(read_file)

        index = read_file.index

        columns = (list(df.columns.values))
        # added_students = ()
        # passed_students = ()

        for index, row in df.iterrows():

            details = []

            for i in columns:
                if str(row[i]) != "nan":
                    details.append("\"" + str(row[i]) + "\"")
                else:
                    details.append("NULL")
            details = [details[0], details[1], details[2], details[3], details[4], details[6], details[7]]
            # student_details = [x if str(x) != "nan" else "" for x in [details[0], details[1], details[2], details[3], details[4], str(details[6]), details[7]]]
            #
            # if tuple(student_details[:5]) not in [i[1::][:-2:] for i in self.get_participant_info(details[0])]:
            #     added_students = (added_students+(details[1],details[0]))
            #     # self.c.execute("INSERT INTO students VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)", ([x if str(x) != "nan" else "" for x in [details[0], details[1], details[2], details[3], details[4], str(details[6]), details[7]]]))
            self.add_student(details)
            # else:
            #     passed_students = (passed_students+(tuple((details[1],details[0]))))
        #
        # log.info("{0: <12} {1}".format("Did not add:",str(passed_students)))
        # log.info("{0: <12} {1}".format("Added:",str(added_students)))


        self.c.commit()

    def get_participant_info(self, lookup, search_type="first_name"):  # search from names
        search = {
        "db_id" : "id",
        "first_name" : "name_first",
        "name_last" : "name_last",
        "gender" : "gender",
        "year" : "year",
        "house" : "house",
        "dob" : "dob",
        "student_id" : "student_id"
        }

        return self.c.execute("SELECT * FROM students WHERE \"%s\" = \"%s\""%(lookup, search[search_type]))


if __name__ == '__main__':

    try:
        os.remove("test.db")
    except Exception as e:
        print(e)

    c = connection()


    c.data_entry()


    c.add_event(("10am", "test", "track", "timed", "M"))
    c.insert_into_results(("1000", "54", "400"))
    # c.add_age_groups()

    # log.info(c.get_age_groups())
