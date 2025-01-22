"""
スクロールアプリケーション
"""

import pyautogui
from myMod_draw import *


class rubicApp(drawTouch):
    def __init__(self):
        super().__init__()
        self.scrollMode = -1 # スクロール方向

    def dragStart(self):
        self.draggingXold = self.dragLog[-1][0] + self.dragCorrect
        self.draggingYold = self.dragLog[-1][1]

    def dragging(self):
        draggingXnow = self.dragLog[-1][0] + self.dragCorrect
        difx = draggingXnow - self.draggingXold  # 1フレーム前との差
        self.draggingXold = draggingXnow
        self.draggingYold = self.dragLog[-1][1]
        # print(difx)
        # 補正込みのx座標の差
        # pyautogui.scroll(difx * 0.05)

    # 専用処理用の関数
    def scrolling(self, diff):
        print(diff)
        pyautogui.scroll(diff*2)

def main():
    app = rubicApp()
    app.startDraw()


if __name__ == "__main__":
    main()
