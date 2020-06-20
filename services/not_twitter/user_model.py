from hashlib import md5

class User:
    def __init__(self, login, password):
        self.login = login
        self.password_hash = md5(password).digest()
        self.temp_cookie = md5(f"{login}{password}shtosh")
    
    def validate_username(self, username):
        pass