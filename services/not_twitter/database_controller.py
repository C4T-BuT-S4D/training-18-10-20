import psycopg2
from psycopg2 import sql

class DatabaseClient:
    def __init__(self):
        pass

    def __enter__(self):
        self.conn = psycopg2.connect(dbname='postgres', user='postgres',
                                     password='postgres', host='postgres')
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.conn.close()
    
    def test(self):
        values = ['test', 'test']
        insert = sql.SQL('insert into users (login, password_hash) values {}').format(sql.SQL(',').join(map(sql.Literal, values)))
        self.cursor.execute(insert)
        self.cursor.execute("select * from users;")
        records = self.cursor.fetchall()
        return records