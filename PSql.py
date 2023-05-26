import psycopg2
import os
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

Psycopg2Instrumentor().instrument()
# Update connection string information

host = os.environ.get('pghost')
dbname = os.environ.get('pgdbname')
user = os.environ.get('pguser')
password = os.environ.get('pgpassword')
sslmode = os.environ.get('pgsslmode')


def executePGQuery():
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)
    
    with psycopg2.connect(conn_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute('select * from company;')
            res = cursor.fetchall()
            print(res)
            return str(res)
    


if __name__ == '__main__':
    executePGQuery()

