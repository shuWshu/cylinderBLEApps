"""
運転アプリケーション
"""

from direct.showbase.ShowBase import ShowBase
from myMod_draw import *
import time
from panda3d.core import *

# フリック処理を追加したクラスの作成
class drawTouchCar(drawTouch):
    def __init__(self, autoDraw, stopKey, app=None):
        super().__init__(autoDraw, stopKey)
        self.app = app
    
    def flick(self, dx, dy, x, y):
        self.app.carFlick(dx, dy, x, y)

"""アプリ"""
# メインクラス
class App(ShowBase):
    # コンストラクタ
    def __init__(self):
        # ShowBaseを継承する
        ShowBase.__init__(self)

        # ウインドウの設定
        self.properties = WindowProperties()
        self.properties.setTitle('Showbase sample')
        self.properties.setSize(1200, 800)
        self.win.requestProperties(self.properties)
        self.setBackgroundColor(0, 0, 0)

        # 車の情報保持変数
        self.carSpeed = 0
        self.carAng = 0 # 角度（正面が0）

        # カメラ設定
        self.disableMouse() # カメラ操作を禁止
        # カメラ回転用のパラメータ
        self.camera.setPos(0, -30, 10) # 初期カメラ位置
        self.camera.lookAt(0, 0, 0.5) # カメラ焦点

        width = 100
        # 地面の配置
        self.node_ground = self.render.attachNewNode(PandaNode('scene_node')) # 地面用ノードの追加
        self.ground = self.loader.loadModel('models/misc/rgbCube')
        self.ground.setPos(0, 0, -0.25)
        self.ground.reparentTo(self.node_ground)
        self.ground.setScale(width, width, 0.5)
        self.ground.setColor(0.5, 0.5, 0.5) # 色の設定

        # 地面に線を引く
        for axis in range(2):
            for i in range(11):
                lines = LineSegs() # LineSegsオブジェクトを作成
                lines.setColor(1, 1, 1, 1)  # 線の色設定(R,G,B,A)
                if axis == 0:
                    lines.moveTo(i*width/10-(width)/2, -width/2, 0.02) # 開始点へ移動
                    lines.drawTo(i*width/10-(width)/2, width/2, 0.02) # 終了点へ線を引く
                elif axis == 1:
                    lines.moveTo(-width/2, i*width/10-(width-10)/2-5,  0.02) # 開始点へ移動
                    lines.drawTo(width/2, i*width/10-(width-10)/2-5,  0.02) # 終了点へ線を引く
                lineNode = lines.create()
                self.render.attachNewNode(lineNode) # シーンにアタッチ

        # 車の配置
        self.node_car = self.render.attachNewNode(PandaNode('scene_node')) # 地面用ノードの追加
        self.car = self.loader.loadModel('models/misc/rgbCube')
        self.car.reparentTo(self.node_car)
        self.car.setScale(1, 3, 1)
        self.car.setPos(0, 0, 0.5)
        self.car.setHpr(self.carAng, 0, 0) # 角度変更

        self.accept("q", self.end)

        self.accept("r", self.resetCar)

        # タスク追加
        self.taskMgr.add(self.update, 'updateTask')      

        self.drawtouch = drawTouchCar(autoDraw=False, stopKey=False, app=self)
        self.drawtouch.startDraw()

    # フリックによる操縦
    def carFlick(self, dx, dy, x, y):
        xArea = x / (txNum * 100)
        yArea = y / (rxNum * 100)
        if abs(dx) > abs(dy): # 回転フリック
            if yArea < 1.0/2: # 速度操作
                # TODO:速度変化度合いをフリック距離で決めても良いかも
                if dx > 0:
                    self.carSpeed += 0.2 # 加速
                else:
                    self.carSpeed -= 0.2 # 減速
            else: # 回転
                if dx < 0: 
                    self.carAng -= 30 # 右折
                else:
                    self.carAng += 30 # 左折
    
    def resetCar(self):
        self.carSpeed = 0
        self.carAng = 0
        self.car.setPos(0, 0, 0.5) # 位置更新
        self.car.setHpr(0, 0, 0) # 角度変更

     # キー状態をセット
    def setKey(self, key, value):
        self.keyMap[key] = value
    
    """アップデート処理"""
    def update(self, task):
        self.updateCamera()
        self.updateCar()
        self.drawtouch.updateDraw() # タッチ位置描画の更新
        return task.cont
    
    # オブジェクトに追従するカメラ
    def updateCamera(self):
        carPos = self.car.getPos()
        px, py, pz = [cam + car for cam, car in zip([0, -30, 10], carPos)]
        self.camera.setPos(px, py, pz)
        self.camera.lookAt(carPos)

    def updateCar(self):
        pos = self.car.getPos()
        dx = math.sin(math.pi*self.carAng/180) * self.carSpeed
        dy = math.cos(math.pi*self.carAng/180) * self.carSpeed
        self.car.setPos(pos + (dx, dy, 0)) # 位置更新
        self.car.setHpr(-self.carAng, 0, 0) # 角度変更
        print(f"speed:{self.carSpeed}, angle:{self.carAng}, pos:{pos}")
        

    def end(self):
        self.drawtouch.stop_program()
        base.userExit()

"""メイン関数"""
def main():    
    app = App()
    app.run()

if __name__ == '__main__':
    main()