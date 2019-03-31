#!/usr/bin/python
import pyodbc
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--sql_host",help="Provide the name of the SQL Host protected by Rubrik",required=True)
parser.add_argument("-i", "--sql_instance",help="Provide the name of the SQL Instance protected by Rubrik",required=True)
parser.add_argument("-d", "--sql_db",help="Provide the name of the SQL Database protected by Rubrik",required=True)
parser.add_argument("-x", "--suffix",help="Provide an identifiable suffix for the SQL live mount",required=True)
parser.add_argument("-u", "--username",help="Provide the SQL Username",required=True)
parser.add_argument("-p", "--password",help="Provide the SQL Password",required=True)
args = parser.parse_args()

sql_host = args.sql_host
sql_instance = args.sql_instance
sql_db_name = args.sql_db
sql_mount_suffix = args.suffix
sql_user = args.username
sql_pass = args.password

cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      "Server="+sql_host+"\\"+sql_instance+";"
                      "Database="+sql_db_name+"-"+sql_mount_suffix+";"
                      "UID="+sql_user+";"
                      "PWD="+sql_pass+";")
cursor = cnxn.cursor()
cursor.execute('SELECT * FROM Person.Person')

for row in cursor:
    print('row = %r' % (row,))