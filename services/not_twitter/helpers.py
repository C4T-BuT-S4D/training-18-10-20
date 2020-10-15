import os
from pathlib import Path

default_upload_folder = './uploads'
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", default_upload_folder)

class File():
    def __init__(self, phisical_filename):
        base = os.path.basename(phisical_filename)
        self.user = base.split('_')[0]
        self.filename = base.split('_')[1]
        self.phisical_filename = os.path.join(UPLOAD_FOLDER, base)
    
    def __str__(self):
        return f"{self.user}: {self.filename}"


def listdir_fileclass(offset, limit):
    ans = []
    print(f"offset {offset}, limit {limit}")
    filenames = sorted(Path(UPLOAD_FOLDER).iterdir(), key=os.path.getmtime)
    for fn in list(reversed(filenames))[offset:offset+limit]:
        try:
            ans.append(File(fn))
        except IndexError:
            pass
    return ans

def listdir_fileclass_by_user(offset, limit, username):
    ans = []
    print(f"offset {offset}, limit {limit}, username {username}")
    filenames = [filename for filename in sorted(Path(UPLOAD_FOLDER).iterdir(), key=os.path.getmtime) if f"{UPLOAD_FOLDER}/{username}_" in str(filename)]
    for fn in list(reversed(filenames))[offset:offset+limit]:
        try:
            ans.append(File(fn))
        except IndexError:
            pass
    return ans