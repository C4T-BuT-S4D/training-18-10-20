import os
from pathlib import Path

default_upload_folder = 'C://workspace/ctf/dev/training-XX-YY-ZZZZ/services/not_twitter/uploads'
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
