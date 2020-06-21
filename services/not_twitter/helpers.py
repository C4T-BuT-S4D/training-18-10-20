from main import UPLOAD_FOLDER
import os, time, arrow
import os.path
from pathlib import Path

ROUND_MINUTES_COUNT = 1
RONDS_COUNT = 5

class File():
    def __init__(self, phisical_filename):
        self.user = phisical_filename.split('_')[0]
        self.filename = phisical_filename.split('_')[1]


def get_only_new_files():
    ans = []
    #https://stackoverflow.com/questions/12485666/python-deleting-all-files-in-a-folder-older-than-x-days
    criticalTime = arrow.now().shift(minutes=+RONDS_COUNT*ROUND_MINUTES_COUNT)
    for item in Path(UPLOAD_FOLDER).glob('*'):
        if item.is_file():
            print (str(item.absolute()))
            itemTime = arrow.get(item.stat().st_mtime)
            print(itemTime, criticalTime)
            if itemTime > criticalTime:
                print("old")
            else:
                try:
                    base = os.path.basename(str(item))
                    ans.append(File(base))
                except IndexError:
                    pass
    return ans
