import psycopg2
from psycopg2 import sql
from hashlib import md5
import user_model

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
    
    def check_user(self, user):
        self.cursor.execute('select * from users where login = %s', (user.login, ))
        u = self.cursor.fetchone()
        print(u, user.password_hash)
        if u is None or u[1] != user.password_hash:
            return False
        else:
            return True
    
    def add_user(self, user):
        self.cursor.execute("INSERT INTO users (login, password_hash) VALUES(%s, %s)", (user.login, user.password_hash))
        self.conn.commit()

    def get_all_users(self):
        self.cursor.execute('select * from users')
        u = self.cursor.fetchall()
        return u

