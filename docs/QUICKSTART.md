# Rubrik Jenkins Live Mount Demo

This project is intended to demo how we can leverage the Rubrik API in order to perform tasks as part of any jenkins build. This demo is specifically aimed at the following:

* Pipeline Build
* Uses Secure Credentials store inside of jenkins
* Runs Native Python 2.7 script
* Uses Rubrik RestAPI to perform test processes

In addition, it supports GitHub integration and SCM Polling to allow for continuous deployment and development (CI/CD)

# Setting up the project

This demo will perform a live mount of the latest snapshot available for the specified MSSQL Database and perform connectivity tests. This will demonstrate the capability of the API within Jenkins.

## Dependencies

* Linux-based OS
* Python 2.7 min.
* Packages installed onto Jenkins Host (RHEL):

```
yum install git
yum install python3
yum install yum-utils
yum groupinstall development
yum install python3-request 
yum install python-dateutil
yum install open-vm-tolls
yum install open-vm-tools
yum install jq
yum install pip
yum install python-pip
yum install python-devel
yum install unixodbc unixodbc-dev
```

* ODBC Drivers installed onto Jenkins Host (RHEL):
Use this URL for other distributions 
https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-2017

```
#RedHat Enterprise Server 7
curl https://packages.microsoft.com/config/rhel/7/prod.repo > /etc/yum.repos.d/mssql-release.repo

exit
sudo yum remove unixODBC-utf16 unixODBC-utf16-devel #to avoid conflicts
sudo ACCEPT_EULA=Y yum install msodbcsql17
# optional: for bcp and sqlcmd
sudo ACCEPT_EULA=Y yum install mssql-tools
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc
# optional: for unixODBC development headers
sudo yum install unixODBC-devel
```

* Github plugin for Jenkins

## Project Credentials

In order to make use of this specific jenkinsfile, setup the project as per steps below:

Before we build the project, we need to add the Rubrik Cluster Credentials:

1. From the Jenkins Homepage browse to 'Credentials'
2. Select the Global Store by selecting Stores scoped to Jenkins 'Global'
3. Inside global credentials, add a new credentials by select 'Add Credentials'
4. Ensure the credentials are set as follows:
    * Kind: Username with Password
    * Scope: Global
    * Username: Rubrik Cluster Username
    * Password: Rubrik Cluster Password
    * ID: RubrikClusterLogon (This must be set to this name as this is referenced in the jenkinsfile)
    * Description(Optional): Add a description that identifies the credentials as Rubrik Cluster details
5. Save the credentials and return to the Jenkins Homepage
6. Inside global credentials, add a new credentials by select 'Add Credentials'
7. Ensure the credentials are set as follows:
    * Kind: Username with Password
    * Scope: Global
    * Username: SQL Server Username
    * Password: SQL Server Password
    * ID: SQLCreds (This must be set to this name as this is referenced in the jenkinsfile)
    * Description(Optional): Add a description that identifies the credentials as SQL Server details
8. Save the credentials and return to the Jenkins Homepage

## Project Pipeline

1. Create a new Pipeline Project within Jenkins - Give it a name e.g. Rubrik-Pipeline-SQL-Live-Mount
2. Tick 'GitHub Project' and provide the project URL
3. Tick 'This Project is parameterized'
4. Add the following parameters:

Type | Name | Default Value | Description
--- | --- | --- | ---
String | RUBRIK_IP | Required - Pre-populate with Floating Rubrik IP | Rubrik Floating Cluster IP Address
String | SQL_HOST | Required - Blank or pre-populate with the SQL Hostname | Provide the SQL Server Hostname
String | SQL_INSTANCE | Required - Blank or pre-populate with the SQL Instance Name | Provide the SQL Server Instance Name
String | SQL_DB_NAME | Required - Blank or pre-poulate with the SQL Database Name | Provide the SQL Database Name within the instance
String | SQL_MOUNT_SUFFIX | Required - Blank or pre-populate with the required identification suffix for this mount | Supply a suffix to identify the SQL Mount

5. Tick 'Trigger Builds Remotely (e.g. from scripts)' and provide the an Auth. Token (This can be alpha-numeric and is generated for this specific project)
6. Within 'Pipeline' ensure definition is set to 'Pipeline script from SCM'
7. Ensure SCM is then set to 'Git' or preferred Code Repository
8. Provide the Repository URL preferably HTTPS e.g. https://github.com/rubrikinc/use-case-jenkins-live-mount.git
9. (Optional) Specify credentials if required for SCM
10. Set Branches to build to the specified branch in this case '*/master'
11. Set script path to jenkinsfile (This is case sensitive, ensure it matches the case of your jenkinsfile in Git)
12. Save the Pipeline

## Build

Now that we have a valid project, we can build the project supplying the parameters, this can be done from within the Jenkins Console from within the Project selecting 'Build with Parameters'
Upon build you will be prompted to supply the above parameters.

## Remote Builds

In order to build this project remotely, we will need to define the URL Parameters that can be passed through within the URL:

1. Create a new user in Jenkins and call it something identifiable e.g. Automation
2. In order to allow "Automation" to trigger the build, the user needs to have the following permissions:

* Overall - Read
* Job - Build
* Job - Read
* Job - Workspace

3. To configure these permissions:
* Click on Manage Jenkins
* Click on Configure Global Security
* Add “Automation” to the list and check off the boxes for the necessary permissions
* Click Save 

4. Return to the Jenkins Home Page, and edit the Jenkins Project
5. Select the project and then click 'Configure'
6. Browse down to the option specified and grab the token specified in the project configuration under 'Trigger Builds Remotely (e.g. from scripts)'

We can now build our URL for Remote Builds, below is an example:

User | User API Token | Build Token
--- | --- | ---
Automation | 5e89cagg1029628jnba380d837880aa10d | iFBDOBhNhaxL4T9ass93HRXun2JF161Z

URL will then be formatted as per below:

http://Automation:Automation API Token@hostname/job/Rubrik-Pipeline-SQL-Live-Mount/buildWithParameters?token=Build Token&SQL_HOST=SQLHOST&SQL_INSTANCE=SQLInstance&SQL_DB_NAME=DBName&SQL_MOUNT_SUFFIX=SUFFIX

We can then use cURL to post this request to Jenkins (Values are examples):

``` curl -H "Content-Type: application/json" -X POST http://Automation:5e89cagg1029628jnba380d837880aa10d@jenkins.rangers.lab/job/Rubrik-Pipeline-SQL-Live-Mount/buildWithParameters?token=iFBDOBhNhaxL4T9ass93HRXun2JF161Z&SQL_HOST=AD-SQL-01&SQL_INSTANCE=AdventureWorks2014&SQL_DB_NAME=Production.Product&SQL_MOUNT_SUFFIX=AD ```