# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pyodbc
from farseer.kind.knd import Application, Phenomenon, ObjectType, One

servername = "S0DSQL0171O"
databasename = "ID_GC_ANA"
username = "SQL_ID_GC_ANA_O"
password = "rgEjoUTP0XwJj4qBIev6"
driver='/home/vcap/deps/0/apt/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.8.so.1.1' #this is where the driver is installed in the Cloud Foundry 'container'
connstr = "DRIVER=%s;SERVER=%s.cbsp.nl,50001;DATABASE=%s;UID=%s;PWD=%s;" % (driver, servername, databasename,username,password)

def execute(sql):
    conn = pyodbc.connect(connstr)
    cursor = conn.cursor()
    s = sql.rstrip('\n').split('\n\n')
    for e in s:
        cursor.execute(e)
    result = cursor.fetchmany(20)
    conn.commit()
    cursor.close()
    return result

def present(e):
    d = []
    for r in e:
        d.append(tuple(map(str, r)))
    fields = '\t'.join('{: <%ds}' % max(map(len, cat)) for cat in zip(*d))
    disp(d, fields)
    
def disp(x, fields):
    print('\n'.join(fields.format(*el) for el in x))

def columntitles(term, cols):
    if isinstance(term, Application):
        if term.op.name == 'selection':
            columntitles(term.args[0].type, cols)
        elif term.op.name == 'range':
            columntitles(term.args[0].type.args[1], cols)
        else:
            for arg in term.args:
                columntitles(arg, cols)
    elif isinstance(term, Phenomenon) or isinstance(term, One):
        cols.append(term.name)
    elif isinstance(term, ObjectType):
        cols.append(term.name + "-id")

    