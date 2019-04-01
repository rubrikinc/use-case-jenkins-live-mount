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

print "Connecting to "+sql_host+"\\"+sql_instance+" and DB: "+sql_db_name+"-"+sql_mount_suffix
cnxn = pyodbc.connect("Driver={ODBC Driver 13 for SQL Server};Server="+sql_host+"\\"+sql_instance+",1433;Database="+sql_db_name+"-"+sql_mount_suffix+";UID="+sql_user+";PWD="+sql_pass)

sql_sp = ('CREATE OR ALTER PROC USP_DataMasking (@TBName varchar(50), @ColumnName VARCHAR(200), @ColumnValue VARCHAR(200))'
          'AS'
          'BEGIN'
          'DECLARE @STRSQL VARCHAR(MAX)'
          'SET @STRSQL = CONCAT(\'UPDATE A SET A.\',@ColumnName, \'=\'\'\',@ColumnValue,\'\'\' FROM \',@TBName, \' A\')'
          'EXEC(@STRSQL)'
          'END'
          'GO')

print sql_sp

cursor = cnxn.cursor()

print "Executing SQL Sanitise Commands"
cursor.execute(sql_sp)
cursor.execute('USP_DataMasking \'Person.EmailAddress\', \'EmailAddress\',\'xxxxxx@xxxxxx.com\'')

for row in cursor:
    print('row = %r' % (row,))

cnxn.commit()  # commit all the records