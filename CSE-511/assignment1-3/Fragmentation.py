#!/usr/bin/python3
#
# Interface for the assignement
#

import psycopg2

RANGE_TABLE_PREFIX = 'range_part'
RROBIN_TABLE_PREFIX = 'rrobin_part'


def getOpenConnection(user='postgres', password='1234', dbname='postgres'):
    return psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='localhost' password='" + password + "'")


def checkpartitioncount(cursor, prefix):
    cursor.execute(
        "SELECT COUNT(table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '{0}%';".format(
            prefix))
    return int(cursor.fetchone()[0])


def loadRatings(ratingstablename, ratingsfilepath, openconnection):
    f = open(ratingsfilepath, 'r')
    with openconnection.cursor() as cur:
        SQL_CREATE = '''
                CREATE TABLE {table_name}(
                userid integer,
                movieid integer,
                rating numeric,
                UNIQUE (userid, movieid)
                );
        '''.format(table_name=ratingstablename)
        cur.execute(SQL_CREATE)
        for values in f:
            values = values.split("::")
            SQL_INSERT = 'INSERT INTO ' + ratingstablename + ' VALUES(%s, %s, %s)'
            DATA = [int(values[0]), int(values[1]), float(values[2])]
            cur.execute(SQL_INSERT, DATA)
    cur.close()


def rangePartition(ratingstablename, numberofpartitions, openconnection):
    interval = 5.0 / numberofpartitions
    lbound = interval

    with openconnection.cursor() as cur:
        # creating first partition i.e. partition 0
        SQL_RANGE_SELECT = 'SELECT * FROM {tname} WHERE rating >= 0.0 AND rating <= {bound}'.format(
            tname=ratingstablename, bound=interval)
        cur.execute(SQL_RANGE_SELECT)
        partition = cur.fetchall()

        SQL_CREATE_PARTITION = '''
         CREATE TABLE {table_name}(
                userid integer,
                movieid integer,
                rating numeric,
                UNIQUE (userid, movieid)
                );
        '''.format(table_name=RANGE_TABLE_PREFIX + '0')
        cur.execute(SQL_CREATE_PARTITION)

        SQL_INSERT_PARTITION = '''
        INSERT INTO {table_name} VALUES(%s, %s, %s)
        '''.format(table_name=RANGE_TABLE_PREFIX + '0')
        for row in partition:
            cur.execute(SQL_INSERT_PARTITION, [int(row[0]), int(row[1]), float(row[2])])

        # creating 1 to numberofpartitions-1
        for num in range(1, numberofpartitions):

            SQL_RANGE_SELECT = 'SELECT * FROM {tname} WHERE rating > {lower} AND rating <= {upper}'.format(
                tname=ratingstablename, lower=lbound, upper=lbound + interval)
            cur.execute(SQL_RANGE_SELECT)
            partition = cur.fetchall()

            SQL_CREATE_PARTITION = '''
                    CREATE TABLE {table_name}(
                           userid integer,
                           movieid integer,
                           rating numeric,
                           UNIQUE (userid, movieid)
                           );
                   '''.format(table_name=RANGE_TABLE_PREFIX + str(num))
            cur.execute(SQL_CREATE_PARTITION)

            SQL_INSERT_PARTITION = '''
                   INSERT INTO {table_name} VALUES(%s, %s, %s)
                   '''.format(table_name=RANGE_TABLE_PREFIX + str(num))
            for row in partition:
                cur.execute(SQL_INSERT_PARTITION, [int(row[0]), int(row[1]), float(row[2])])

            lbound += interval
    cur.close()


def roundRobinPartition(ratingstablename, numberofpartitions, openconnection):
    with openconnection.cursor() as cur:
        # get number of rows
        SQL_NUM_ROWS = 'SELECT COUNT(userid) FROM {tablename}'.format(tablename=ratingstablename)
        cur.execute(SQL_NUM_ROWS)
        num_rows = int(cur.fetchone()[0])

        for num in range(1, numberofpartitions + 1):
            # get round-robin rows
            SQL_RR_SELECTION = '''
               SELECT * FROM ( 
                    SELECT userid, movieid, rating, ROW_NUMBER () OVER (
                            ORDER BY userid
                        )
                    FROM {tablename} 
               )
               WHERE row_number % {offset} = {part_num} % {offset}
               
            '''.format(tablename=ratingstablename, offset=numberofpartitions, part_num=num)
            cur.execute(SQL_RR_SELECTION)
            partition = cur.fetchall()

            # create round-robin partition table
            SQL_CREATE_PARTITION = '''
                                CREATE TABLE {table_name}(
                                       userid integer,
                                       movieid integer,
                                       rating numeric,
                                       UNIQUE (userid, movieid)
                                       );
                               '''.format(table_name=RROBIN_TABLE_PREFIX + str(num - 1))
            cur.execute(SQL_CREATE_PARTITION)

            # insert into partition
            SQL_INSERT_PARTITION = '''
                              INSERT INTO {table_name} VALUES(%s, %s, %s)
                              '''.format(table_name=RROBIN_TABLE_PREFIX + str(num - 1))
            for row in partition:
                data = [int(row[0]), int(row[1]), float(row[2])]
                cur.execute(SQL_INSERT_PARTITION, [int(row[0]), int(row[1]), float(row[2])])

    cur.close()


def roundrobininsert(ratingstablename, userid, itemid, rating, openconnection):
    with openconnection.cursor() as cur:
        RROBING_PARTITION_NUM = checkpartitioncount(cur, RROBIN_TABLE_PREFIX)

        SQL_INSERT = 'INSERT INTO ' + ratingstablename + ' VALUES (%s, %s, %s) '
        cur.execute(SQL_INSERT, [int(userid), int(itemid), float(rating)])
        SQL_COUNT = 'SELECT COUNT(userid) FROM {tablename}'.format(tablename=ratingstablename)
        cur.execute(SQL_COUNT)
        partition_count = (int(cur.fetchone()[0]) % RROBING_PARTITION_NUM) - 1

        SQL_INSERT = 'INSERT INTO {tablename} VALUES (%s, %s, %s)'.format(
            tablename=RROBIN_TABLE_PREFIX + str(partition_count))
        cur.execute(SQL_INSERT, [int(userid), int(itemid), float(rating)])

    cur.close()
    pass


def rangeinsert(ratingstablename, userid, itemid, rating, openconnection):
    with openconnection.cursor() as cur:
        RANGE_PARTITION_NUM = checkpartitioncount(cur, RANGE_TABLE_PREFIX)
        interval = 5.0 / RANGE_PARTITION_NUM
        num = int((rating / interval) - 1)

        SQL_INSERT = 'INSERT INTO ' + ratingstablename + ' VALUES (%s, %s, %s)'
        cur.execute(SQL_INSERT, [int(userid), int(itemid), float(rating)])

        SQL_INSERT = 'INSERT INTO {tablename} VALUES (%s, %s, %s)'.format(tablename=RANGE_TABLE_PREFIX+str(num))
        cur.execute(SQL_INSERT, [int(userid), int(itemid), float(rating)])

    cur.close()


def createDB(dbname='dds_assignment'):
    """
    We create a DB by connecting to the default user and database of Postgres
    The function first checks if an existing database exists for a given name, else creates it.
    :return:None
    """
    # Connect to the default database
    con = getOpenConnection(dbname='postgres')
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()

    # Check if an existing database with the same name exists
    cur.execute('SELECT COUNT(*) FROM pg_catalog.pg_database WHERE datname=\'%s\'' % (dbname,))
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute('CREATE DATABASE %s' % (dbname,))  # Create the database
    else:
        print('A database named {0} already exists'.format(dbname))

    # Clean up
    cur.close()
    con.close()


def deletepartitionsandexit(openconnection):
    cur = openconnection.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    l = []
    for row in cur:
        l.append(row[0])
    for tablename in l:
        cur.execute("drop table if exists {0} CASCADE".format(tablename))

    cur.close()


def deleteTables(ratingstablename, openconnection):
    try:
        cursor = openconnection.cursor()
        if ratingstablename.upper() == 'ALL':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            for table_name in tables:
                cursor.execute('DROP TABLE %s CASCADE' % (table_name[0]))
        else:
            cursor.execute('DROP TABLE %s CASCADE' % (ratingstablename))
        openconnection.commit()
    except psycopg2.DatabaseError as e:
        if openconnection:
            openconnection.rollback()
        print('Error %s' % e)
    except IOError as e:
        if openconnection:
            openconnection.rollback()
        print('Error %s' % e)
    finally:
        if cursor:
            cursor.close()
