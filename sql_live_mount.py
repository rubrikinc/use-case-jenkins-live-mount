#!/usr/bin/python
import json
import base64
import requests
import datetime
import time
import os
import dateutil.parser as dp
import argparse
import urllib3

DEBUG = False
no_cert_warnings = True

# Suppress self-signed certificate warnings
if no_cert_warnings:
    from urllib3.exceptions import InsecureRequestWarning
    urllib3.disable_warnings(InsecureRequestWarning)

# Setup Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-ip", "--rubrik_ip",help="Provide any floating IP address from the rubrik cluster",required=True)
parser.add_argument("-u", "--username",help="Provide a username for the rubrik cluster",required=True)
parser.add_argument("-p", "--password",help="Provide the password for the specified rubrik cluster username",required=True)
parser.add_argument("-s", "--sql_host",help="Provide the name of the SQL Host protected by Rubrik",required=True)
parser.add_argument("-i", "--sql_instance",help="Provide the name of the SQL Instance protected by Rubrik",required=True)
parser.add_argument("-d", "--sql_db",help="Provide the name of the SQL Database protected by Rubrik",required=True)
parser.add_argument("-x", "--suffix",help="Provide an identifiable suffix for the SQL live mount",required=True)
args = parser.parse_args()

# define Rubrik connection details from Arguments Variables
rubrik_ip = args.rubrik_ip
rubrik_user = args.username
rubrik_pass = args.password

# define SQL Server host/DB info from Arguments Variables (Using Paramterized Build)
sql_host = args.sql_host
sql_instance = args.sql_instance
sql_db_name = args.sql_db
sql_mount_prefix = args.suffix

def main():
    # Display variables if deubg is enabled
    if(DEBUG == True):
        print('DEBUG: Rubrik IP: ' + rubrik_ip + ' SQL Host: ' + sql_host + ' SQL Instance: ' + sql_instance + ' SQL DB Name: ' + sql_db_name + ' SQL Mount Name: ' + sql_mount_prefix)
    sql_mounted_db_name = sql_db_name + '-' + sql_mount_prefix
    token = connectRubrik(rubrik_ip, rubrik_user, rubrik_pass)
    host_id = getRubrikHostIdByName(sql_host,rubrik_ip,token)
    instance_id = getRubrikSqlInstanceIdByName(host_id,sql_instance,rubrik_ip,token)
    sql_db_id = getRubrikSqlDbIdByName(instance_id,sql_db_name,rubrik_ip,token)
    sql_db_instance_id = getRubrikSqlDbInstanceIdByName(instance_id,sql_db_name,rubrik_ip,token)
    snapshot_timestamp = GetMSSQLLatestSnapshot(sql_db_id,rubrik_ip,token)
    sql_snapshot_timestamp = ConvertISOtoEPOCH(snapshot_timestamp)
    live_mount_id = liveMountRubrikSqlDb(sql_snapshot_timestamp,sql_db_id,sql_db_instance_id,sql_mounted_db_name,rubrik_ip,token)
    live_mount_status = live_mount_id['status']
    print('Request ID is: '+live_mount_id['id'])

    while live_mount_status not in ['SUCCEEDED', 'FAILED']:
        time.sleep(10)
        live_mount_status = LiveMountStatus(live_mount_id['id'],rubrik_ip,token)
        print('Status of Job is: ' + live_mount_status)

    print ('Host ID: ' + host_id + ' Instance ID: ' + instance_id + ' SQL ID: ' + sql_db_id + ' Snapshot Timestamp: ' + snapshot_timestamp + ' Converted Timestamp: ' +sql_snapshot_timestamp)
    if live_mount_status == 'FAILED':
        return 1
    else:
        return 0

def connectRubrik(rubrik_ip, rubrik_user, rubrik_pass):
    uri = 'https://'+rubrik_ip+'/api/v1/session'
    b64auth = "Basic "+ base64.b64encode(rubrik_user+":"+rubrik_pass)
    headers = {'Content-Type':'application/json', 'Authorization':b64auth}
    payload = '{"username":"'+rubrik_user+'","password":"'+rubrik_pass+'"}'
    r = requests.post(uri, headers=headers, verify=False, data=payload)
    if r.status_code == 422:
        raise ValueError("Something went wrong authenticating with the Rubrik cluster")
    token = str(json.loads(r.text)["token"])
    return ("Bearer "+token)

def getRubrikHostIdByName(host_name,rubrik_ip,token):
    uri = 'https://'+rubrik_ip+'/api/v1/host?primary_cluster_id=local&hostname='+host_name
    headers = {'Content-Type':'application/json', 'Authorization':token}
    r = requests.get(uri, headers=headers, verify=False)
    query_object = json.loads(r.text)
    for host in query_object['data']:
        if host['hostname'] == host_name:
            return host['id']
    return 0

def getRubrikSqlInstanceIdByName(host_id,instance_name,rubrik_ip,token):
    uri = 'https://'+rubrik_ip+'/api/v1/mssql/instance?primary_cluster_id=local&root_id='+str(host_id)
    headers = {'Content-Type':'application/json', 'Authorization':token}
    r = requests.get(uri, headers=headers, verify=False)
    query_object = json.loads(r.text)
    for instance in query_object['data']:
        if instance['name'] == instance_name:
            return instance['id']
    return 0

def getRubrikSqlDbIdByName(instance_id,db_name,rubrik_ip,token):
    uri = 'https://'+rubrik_ip+'/api/v1/mssql/db?primary_cluster_id=local&instance_id='+str(instance_id)
    headers = {'Content-Type':'application/json', 'Authorization':token}
    r = requests.get(uri, headers=headers, verify=False)
    query_object = json.loads(r.text)
    for sqldb in query_object['data']:
        if sqldb['name'] == db_name:
            return sqldb['id']
    return 0

def getRubrikSqlDbInstanceIdByName(instance_id,db_name,rubrik_ip,token):
    uri = 'https://'+rubrik_ip+'/api/v1/mssql/db?primary_cluster_id=local&instance_id='+instance_id
    headers = {'Content-Type':'application/json', 'Authorization':token}
    r = requests.get(uri, headers=headers, verify=False)
    query_object = json.loads(r.text)
    for sqldb in query_object['data']:
        if sqldb['name'] == db_name:
            return sqldb['instanceId']
    return 0

def GetMSSQLLatestSnapshot(sql_db_id,rubrik_ip,token):
    x = 0
    uri = 'https://'+rubrik_ip+'/api/v1/mssql/db/'+sql_db_id+'/snapshot?primary_cluster_id=local'
    headers = {'Content-Type':'application/json', 'Authorization':token, 'Accept':'application/json'}
    r = requests.get(uri, headers=headers, verify=False)
    query_object = json.loads(r.text)
    max_objects = query_object['total']
    for snapshot in query_object['data']:
        x += 1
        if x == max_objects:
            snapshot_date = snapshot['date']
    return snapshot_date

def liveMountRubrikSqlDb(sql_snapshot_timestamp,sql_db_id,sql_db_instance_id,sql_mounted_db_name,rubrik_ip,token):
    sql_db_id = sql_db_id.replace(":","%3A")
    uri = 'https://'+rubrik_ip+'/api/v1/mssql/db/'+sql_db_id+'/mount'
    headers = {'Content-Type':'application/json', 'Authorization':token, 'Accept':'application/json'}
    payload = '{"recoveryPoint":{"timestampMs":'+ sql_snapshot_timestamp +'000},"targetInstanceId":"' +str(sql_db_instance_id)+ '","mountedDatabaseName":"'+str(sql_mounted_db_name)+'"}'
    r = requests.post(uri, data=payload, headers=headers, verify=False)
    if r.status_code != 202:
        print ('SQL Mount Failed - HTTP Error Code: ' + r.status_code)
        raise ValueError("Something went wrong mounting the SQL Live Mount.")
    return json.loads(r.text)

def LiveMountStatus(live_mount_id,rubrik_ip,token):
    live_mount_id = live_mount_id.replace(":","%3A")
    uri = 'https://'+rubrik_ip+'/api/v1/mssql/request/'+live_mount_id
    headers = {'Content-Type':'application/json', 'Authorization':token, 'Accept':'application/json'}
    r = requests.get(uri, headers=headers, verify=False)
    if r.status_code != 200:
        raise ValueError("Something went wrong...")
    return json.loads(r.text)['status']

def ConvertISOtoEPOCH(snapshot_timestamp):
    parsed_time = dp.parse(snapshot_timestamp)
    time_in_mseconds = parsed_time.strftime('%s')
    return time_in_mseconds

# Start program
if __name__ == "__main__":
   main()