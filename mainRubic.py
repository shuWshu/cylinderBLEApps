"""
ルービックキューブアプリ
以下のサイトの操作法に準拠
https://ruwix.com/online-puzzle-simulators/
"""

import pyautogui
from myMod_draw import *

# ルービックキューブ用フリック
# フリックベクトル，始点座標
def rubicFlick(dx, dy, x, y):
    xArea = x / (txNum * 100)
    yArea = y / (rxNum * 100)
    print(f"{xArea}, {yArea}")
    presskey = []
    if abs(dx) > abs(dy): # 回転フリック
        if yArea < 1.0/3:
            presskey.append("l")
            if dx < 0:
                presskey.append("shift")
        elif yArea < 2.0/3:
            presskey.append("m")
            if dx < 0:
                presskey.append("shift")
        else:
            presskey.append("r")
            if dx > 0: # これだけ逆なので注意
                presskey.append("shift")
    else: # スライドフリック    
        if 0.4 < xArea < 0.6: # 上部でのフリック
            presskey.append("z")
            if dy > 0:
                presskey.append("shift")
        elif 0.15 < xArea < 0.35: # 前面，後面でのフリック
            presskey.append("y")
            if dy < 0:
                presskey.append("shift")
    
    if len(presskey) == 1:
        pyautogui.press(presskey)
    elif len(presskey) == 2:
        pyautogui.hotkey(presskey[1], presskey[0])

class rubicApp(drawTouch):
    def __init__(self):
        super().__init__()
    
    def flick(self, dx, dy, x, y):
        rubicFlick(dx, dy, x, y)

def main():
    app = rubicApp()
    app.startDraw()

if __name__ == "__main__":
    main()