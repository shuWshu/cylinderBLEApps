"""
実験用
スクロールアプリケーション
結果をcsvとして出力する
円筒面使用ver
"""

from scrollTask_lib import App
from myMod_draw import *
import threading

# -----パラメータ-----
ID = 0
DIST = 0
MODE = "cylinder"
# -----パラメータ-----

# フリック，ドラッグ処理を追加したクラスの作成
class drawTouchFD(drawTouch):
    def __init__(self, autoDraw, stopKey, drawing, app=None):
        super().__init__(autoDraw, stopKey, drawing)
        self.app = app
    
    def flick(self, dx, dy, x, y):
        # self.app.carFlick(dx, dy, x, y)
        pass

    #  # ドラッグ開始
    # def dragStart(self):
    #     # print("dragStart")
    #     self.app.scroll_start(self.dragLog[0])
    # # ドラッグ中
    # # 座標格納配列を送信
    # def dragging(self):
    #     # print(f"({self.dragLog[-1][0]+self.dragCorrect}, {self.dragLog[-1][1]})")
    #     self.app.dragging(self.dragLog[-1][0])
    # # ドラッグ終了
    # def dragEnd(self):
    #     # print("dragEnd")
    #     self.app.scroll_end()

    def scrolling(self, diff):
        self.app.scrolling(diff*100)

class App_cylinder(App):
    # コンストラクタ
    def __init__(self, ID, DIST, MODE):
        # 継承
        App.__init__(self, ID, DIST, MODE)

        self.drawtouch = drawTouchFD(autoDraw=False, stopKey=False, drawing=False, app=self)
        self.drawtouch.startDraw()
        self.flagEnd = False

        self.SCROLLSTEP = 0.003 # スクロール操作の倍率
        # 処理を別スレッドに移す
        thread = threading.Thread(target=self.updateDrawtouch)
        thread.start()

    def updateDrawtouch(self):
        while not self.flagEnd:
            self.drawtouch.updateDraw() # タッチ位置描画の更新

    # アップデート処理
    def update(self, task):
        return super().update(task)

    # ドラッグ開始時の処理
    def scroll_start(self, startPos):
        self.draggedPos_x = startPos[0] # ドラッグ時の座標保存

    # ドラッグ中の処理
    def dragging(self, dragPos_x):
        draggingPos_x = dragPos_x# 回転補正込みの現在地x
        delta = -(draggingPos_x - self.draggedPos_x)
        self.draggedPos_x = draggingPos_x
        if delta != 0: # 移動していたら
            print(delta)
            self.rotate(delta_y=delta)
        pass

    # 専用処理用の関数
    def scrolling(self, diff):
        correct = 1.0
        self.rotate(delta_y=-diff*correct)

    # ターゲット切り替え時に移動方向の設定を変更
    def set_target(self):
        scrollMode = (-1) * ((self.taskProgress % 2) * 2 - 1) # -1 or 1 を代入
        self.drawtouch.setScrollMode(scrollMode)
        return super().set_target()

    def scroll_end(self):
        pass

    def taskStart(self):
        return super().taskStart()

    def reset(self):
        return super().reset()

    def end(self):
        self.flagEnd = True
        self.drawtouch.stop_program()
        return super().end()

def main():
    app = App_cylinder(ID, DIST, MODE)
    app.run()

if __name__ == "__main__":
    main()