import pyodbc
import os
from opentelemetry.instrumentation.dbapi import trace_integration

trace_integration(pyodbc, "Connection", "odbc")

server = os.environ.get('sqlserver')
database = os.environ.get('sqldatabase')
username = os.environ.get('sqlusername')
password = os.environ.get('sqlpassword') 
driver= os.environ.get('sqldriver')

def executeSqlQuery(query=None):
    if not query:
        query = "SELECT TOP 3 name, collation_name FROM sys.databases"
    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchall()
            return str(row)

if __name__ == '__main__':
    executeSqlQuery() 