#!/usr/bin/python3


import psycopg2
import os
import sys


DATABASE_NAME='dds_assignment'
RATINGS_TABLE_NAME='ratings'
RANGE_TABLE_PREFIX='range_part'
RROBIN_TABLE_PREFIX='rrobin_part'
RANGE_QUERY_OUTPUT_FILE='RangeQueryOut.txt'
PONT_QUERY_OUTPUT_FILE='PointQueryOut.txt'
RANGE_RATINGS_METADATA_TABLE ='rangeratingsmetadata'
RROBIN_RATINGS_METADATA_TABLE='roundrobinratingsmetadata'

# Donot close the connection inside this file i.e. do not perform openconnection.close()

def checkpartitioncount(cursor, prefix):
    cursor.execute(
        "SELECT COUNT(table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '{0}%';".format(
            prefix))
    return int(cursor.fetchone()[0])

def RangeQueryRange(ratingMinValue, ratingMaxValue, openconnection):
    with openconnection.cursor() as cur:
        partition_count = checkpartitioncount(cur, RANGE_TABLE_PREFIX)
        interval = partition_count/5.0
        l = 0
        partitions = []
        for i in range(0,partition_count):
            if l > ratingMaxValue:
                break
            if (l <= ratingMinValue <= (l+interval)) or ratingMinValue<=l:
                partitions.append(i)

            l += interval
    return partitions

def ExecuteRangeQueryRange(partition_nums, ratingMinValue, ratingMaxValue, openconnection):
    results = []
    with openconnection.cursor() as cur:
        for num in partition_nums:
            SQL_SELECT = '''
             SELECT userid, movieid, rating
             FROM {tablename}
             WHERE rating <= {max} AND rating >= {min} 
             '''.format(tablename=RANGE_TABLE_PREFIX+str(num), max=ratingMaxValue, min=ratingMinValue)
            cur.execute(SQL_SELECT)
            rows = cur.fetchall()
            for row in rows:
                new_row = [RANGE_TABLE_PREFIX + str(num)]
                row = [i for i in row]
                row = new_row+row
                results.append(row)
    return results

def ExecuteRangeQueryRR(ratingMinValue, ratingMaxValue, openconnection):
    with openconnection.cursor() as cur:
        partition_num = checkpartitioncount(cur, RROBIN_TABLE_PREFIX)
        results = []
        for num in range(0, partition_num):
            SQL_SELECT = '''
                         SELECT userid, movieid, rating
                         FROM {tablename}
                         WHERE rating <= {max} AND rating >= {min} 
                         '''.format(tablename=RROBIN_TABLE_PREFIX + str(num), max=ratingMaxValue, min=ratingMinValue)
            cur.execute(SQL_SELECT)
            rows = cur.fetchall()
            for row in rows:
                new_row = [RROBIN_TABLE_PREFIX + str(num)]
                row = [i for i in row]
                row = new_row + row
                results.append(row)
        return results


def RangeQuery(ratingsTableName, ratingMinValue, ratingMaxValue, openconnection):
    partitions = RangeQueryRange(ratingMinValue, ratingMaxValue, openconnection)
    results = ExecuteRangeQueryRange(partitions, ratingMinValue, ratingMaxValue, openconnection)
    results += ExecuteRangeQueryRR(ratingMinValue, ratingMaxValue, openconnection)
    writeToFile(RANGE_QUERY_OUTPUT_FILE, results)


def ExecutePointQueryRange(ratingValue, openconnection):
    with openconnection.cursor() as cur:
        results = []
        partition_count = checkpartitioncount(cur, RANGE_TABLE_PREFIX)
        interval = partition_count / 5.0
        l = 0
        partition_name = ""
        for i in range(0, partition_count):
            if l <= ratingValue <= (l + interval) :
                partition_name = RANGE_TABLE_PREFIX+str(i)
                break

            l += interval

        SQL_SELECT = '''
        SELECT userid, movieid, rating
        FROM {tablename}
        WHERE rating = {ratVal} 
        '''.format(tablename=partition_name, ratVal = ratingValue)
        cur.execute(SQL_SELECT)
        rows = cur.fetchall()
        for row in rows:
            new_row = [partition_name]
            row = [i for i in row]
            row = new_row + row
            results.append(row)
    return results

def ExecutePointQueryRR(ratingValue, openconnection):
    with openconnection.cursor() as cur:
        partition_num = checkpartitioncount(cur, RROBIN_TABLE_PREFIX)
        results = []
        for num in range(0, partition_num):
            SQL_SELECT = '''
                         SELECT userid, movieid, rating
                         FROM {tablename}
                         WHERE rating = {ratVal} 
                         '''.format(tablename=RROBIN_TABLE_PREFIX + str(num), ratVal=ratingValue)
            cur.execute(SQL_SELECT)
            rows = cur.fetchall()
            for row in rows:
                new_row = [RROBIN_TABLE_PREFIX + str(num)]
                row = [i for i in row]
                row = new_row + row
                results.append(row)
        return results


def PointQuery(ratingsTableName, ratingValue, openconnection):

    results = ExecutePointQueryRange(ratingValue, openconnection)
    results += ExecutePointQueryRR(ratingValue, openconnection)
    writeToFile(PONT_QUERY_OUTPUT_FILE, results)
                


def writeToFile(filename, rows):
    f = open(filename, 'w')
    for line in rows:
        f.write(','.join(str(s) for s in line))
        f.write('\n')
    f.close()