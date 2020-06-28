import os
from pathlib import Path

default_upload_folder = 'C://workspace/ctf/dev/training-XX-YY-ZZZZ/services/not_twitter/uploads'
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", default_upload_folder)
MAX_FILE_COUNT_IN_LISTING = 1024

class File():
    def __init__(self, phisical_filename):
        base = os.path.basename(phisical_filename)
        self.user = base.split('_')[0]
        self.filename = base.split('_')[1]
        self.phisical_filename = os.path.join(UPLOAD_FOLDER, base)
    
    def __str__(self):
        return f"{self.user}: {self.filename}"


def listdir_fileclass():
    ans = []
    filenames = sorted(Path(UPLOAD_FOLDER).iterdir(), key=os.path.getmtime)
    for fn in reversed(filenames):
        try:
            ans.append(File(fn))
        except IndexError:
            pass
    return ans
