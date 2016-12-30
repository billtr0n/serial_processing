import os
import sqlite3
import processing.settings as settings

def create_new_database( database_file, data ):
    # set up database
    table_name = 'simulation'
    field_names = data.keys()

    conn = sqlite3.connect( database_file ) 
    c = conn.cursor()

    # create new table
    c.execute('CREATE TABLE %s' % table_name)

    # add fields in fieldnames
    for field in field_names:
        c.execute('ALTER TABLE %s ADD COLUMN %s TEXT' % ( table_name, field ) )

    conn.commit()
    return conn, c

def connect_to_database( database_file, data ):
    con = sqlite3.connect( database_file )
    cur = con.cursor()

    # check if db schema is like data
    db_cols = _get_column_names( cur )
    data_cols = data.keys()
    if sorted(data_cols) == sorted(db_cols):
        pass
    
def _get_column_names( cur, table_name='simulation' ):
    cur.execute('PRAGMA TABLE_INFO(%s)' % table_name)
    names = [s[1] for s in cur.fetchall()]
    return names
