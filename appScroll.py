"""
スクロールアプリケーション
"""

import pyautogui
from myMod_draw import *

class rubicApp(drawTouch):
    def __init__(self):
        super().__init__()

    def dragStart(self):
        self.draggingXold = self.dragLog[-1][0]+self.dragCorrect

    def dragging(self):
        draggingXnow = self.dragLog[-1][0]+self.dragCorrect
        difx = (draggingXnow - self.draggingXold) # 1フレーム前との差
        self.draggingXold = draggingXnow
        print(difx)
        # 補正込みのx座標の差
        pyautogui.scroll(difx*0.1)

def main():
    app = rubicApp()
    app.startDraw()

if __name__ == "__main__":
    main()