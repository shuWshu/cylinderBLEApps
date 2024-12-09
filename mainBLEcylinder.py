"""
円筒とタッチ位置の描画
main3Dと大体同じ
"""
from myMod_BLEReader import BLEreader
import time

blereader = BLEreader()

for i in range(10):
    print(blereader.getTimelineDict())
    time.sleep(1)

blereader.stop_program()

