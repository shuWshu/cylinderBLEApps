"""
モジュールを用いたテストプログラム
"""
from myMod_BLEReader import BLEreader
import time

blereader = BLEreader()
blereader.startBLE()

for i in range(10):
    print(blereader.getTimelineDict())
    time.sleep(1)

blereader.stop_program()