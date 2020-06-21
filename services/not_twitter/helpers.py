from main import UPLOAD_FOLDER
import os


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
    filenames = os.listdir(UPLOAD_FOLDER)
    for fn in filenames:
        try:
            ans.append(File(fn))
        except IndexError:
            pass
    return ans
