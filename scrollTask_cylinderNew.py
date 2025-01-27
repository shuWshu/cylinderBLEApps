"""
実験用
スクロールアプリケーション
結果をcsvとして出力する
円筒面使用ver

新スクリプトを使用
"""

from scrollTask_lib import App
from myMod_drawNew import *
import threading

# -----パラメータ-----
ID = 0
DIST = 0
MODE = "cylinder"
# -----パラメータ-----

# フリック，ドラッグ処理を追加したクラスの作成
class drawCV2_drag(drawCV2):
    def __init__(self, app=None):
        super().__init__(autoDraw=False, stopKey=False, drawing=False)
        self.app = app

    def scrolling(self, diff):
        self.app.scrolling(diff)

class App_cylinder(App):
    # コンストラクタ
    def __init__(self, ID, DIST, MODE):
        # 継承
        App.__init__(self, ID, DIST, MODE)

        self.drawCV2 = drawCV2_drag(app=self)
        self.drawCV2.startDraw()
        self.flagEnd = False

        self.SCROLLSTEP = 0.003 # スクロール操作の倍率
        # 処理を別スレッドに移す
        thread = threading.Thread(target=self.updateDrawtouch)
        thread.start()

    def updateDrawtouch(self):
        while not self.flagEnd:
            self.drawCV2.updateDraw() # タッチ位置描画の更新

    # アップデート処理
    def update(self, task):
        return super().update(task)

    # 専用処理用の関数
    def scrolling(self, diff):
        correct = 0.01
        print(diff)
        self.rotate(delta_y=-diff*correct)

    def end(self):
        self.flagEnd = True
        self.drawCV2.stop_program()
        return super().end()

def main():
    app = App_cylinder(ID, DIST, MODE)
    app.run()

if __name__ == "__main__":
    main()