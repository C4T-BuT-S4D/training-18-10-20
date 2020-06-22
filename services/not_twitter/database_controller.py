import psycopg2
from psycopg2 import sql

class DatabaseClient:
    def __init__(self):
        pass

    def __enter__(self):
        self.conn = psycopg2.connect(dbname='postgres', user='postgres',
                                     password='postgres', host='postgres', port = 5432)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.conn.close()
    
    def test(self):
        values = ['test', 'test']
        insert = sql.SQL("INSERT INTO users VALUES ('test', 'test')")
        self.cursor.execute(insert)
        self.cursor.execute("select * from users;")
        records = self.cursor.fetchall()
        return str(records)
