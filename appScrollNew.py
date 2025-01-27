"""
スクロールアプリケーション
"""

import pyautogui
from myMod_drawNew import *


class scrollApp(drawCV2):
    def __init__(self):
        super().__init__()

    # 専用処理用の関数
    def scrolling(self, diff):
        pyautogui.scroll(diff * 0.3)

    def flicking(self, diff):
        pyautogui.hotkey("[", "command")
        print("f")


def main():
    app = scrollApp()
    app.startDraw()


if __name__ == "__main__":
    main()
