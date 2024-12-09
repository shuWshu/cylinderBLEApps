"""
円筒とタッチ位置の描画
main3Dと大体同じ
"""

from direct.showbase.ShowBase import ShowBase
from myMod_draw import *
import time
from panda3d.core import *

"""円筒描画処理"""
# 円筒描画のプログラム
def create_cylinder(num_segments=32, radius=1.0, height=2.0):
    format = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData('cylinder', format, Geom.UHStatic)
    vdata.setNumRows(num_segments * 2 + 2) # 上下面中心点を含める

    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')

    # 側面頂点(上下面周)
    for i in range(num_segments):
        angle = 2 * math.pi * i / num_segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        # 上面頂点
        vertex.addData3(x, y, height/2)
        normal.addData3(x, y, 0)
        # 下面頂点
        vertex.addData3(x, y, -height/2)
        normal.addData3(x, y, 0)

    top_center_index = num_segments * 2
    vertex.addData3(0, 0, height/2)
    normal.addData3(0, 0, 1)
    bottom_center_index = num_segments * 2 + 1
    vertex.addData3(0, 0, -height/2)
    normal.addData3(0, 0, -1)

    # 三角形生成
    tris = GeomLinestrips(Geom.UHStatic) # 一時的に変更しないように注意
    # 実際はLinestripsではなくTrianglesを側面用に作るため再設定が必要
    # 以下は前回と同様
    tris = GeomTriangles(Geom.UHStatic)

    # 側面
    for i in range(num_segments):
        top1 = i*2
        bot1 = i*2+1
        top2 = ((i+1)*2) % (num_segments*2)
        bot2 = ((i+1)*2+1) % (num_segments*2)
        tris.addVertices(top1, bot1, top2)
        tris.addVertices(bot1, bot2, top2)

    # 上面蓋
    for i in range(num_segments):
        top_current = i*2
        top_next = ((i+1)*2) % (num_segments*2)
        tris.addVertices(top_center_index, top_current, top_next)

    # 下面蓋
    for i in range(num_segments):
        bot_current = i*2+1
        bot_next = ((i+1)*2+1) % (num_segments*2)
        tris.addVertices(bottom_center_index, bot_next, bot_current)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode('cylinder')
    node.addGeom(geom)
    return NodePath(node)

# 底面の辺描画
def create_bottom_line(num_segments=32, radius=1.0, z=-1.0):
    # 円周ライン用の頂点データ
    format = GeomVertexFormat.getV3()
    vdata = GeomVertexData('line', format, Geom.UHStatic)
    vdata.setNumRows(num_segments)
    vertex = GeomVertexWriter(vdata, 'vertex')

    # 頂点の追加（円周上）
    for i in range(num_segments):
        angle = 2 * math.pi * i / num_segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertex.addData3(x, y, z)

    # Linestripsで円を閉じる
    line = GeomLinestrips(Geom.UHStatic)
    for i in range(num_segments):
        line.addVertex(i)
    line.addVertex(0) # 最初の点に戻ることでループを閉じる

    line.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(line)
    node = GeomNode('bottom_line')
    node.addGeom(geom)

    line_nodepath = NodePath(node)
    # 線を太くしたい場合
    # render modeを使う
    line_nodepath.setRenderModeThickness(2)
    line_nodepath.setColor(1, 0, 0, 1)  # 赤色線
    return line_nodepath

# 上底と下底に線がある円筒の作成
# num_segments, radius, z
def  create_cylinder_lines(num_segments=32, radius=1.0, height=4.0):
    cylinder = create_cylinder(num_segments, radius, height)
    bottom_line = create_bottom_line(num_segments, radius, -height/2)
    top_line = create_bottom_line(num_segments, radius, height/2)
    return cylinder, bottom_line, top_line

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
        self.properties.setSize(400, 800)
        self.win.requestProperties(self.properties)
        self.setBackgroundColor(0, 0, 0)

        # カメラ設定
        self.disableMouse() # カメラ操作を禁止
        # カメラ回転用のパラメータ
        self.angle = 0.0           # 現在の角度
        self.radius = 12.0         # 公転半径
        self.height = 4.0          # 高さ
        self.center = (0, 0, 0)   # カメラの中心位置
        self.camera.setPos(0, -self.radius, self.height) # カメラ位置
        self.camera.lookAt(self.center) # カメラ焦点

        self.cylinder_conf = {
            "num_segments": 32,
            "radius": 2.0,
            "height": 6.0,
        }

        # 円筒の配置
        self.node_cylinder = self.render.attachNewNode(PandaNode('scene_node')) # 円筒用ノードの追加
        self.cylinder, self.bottom_line, self.top_line = create_cylinder_lines(self.cylinder_conf["num_segments"], self.cylinder_conf["radius"], self.cylinder_conf["height"])
        self.cylinder.reparentTo(self.node_cylinder)
        self.bottom_line.reparentTo(self.node_cylinder)
        self.top_line.reparentTo(self.node_cylinder)
        self.cylinder.setTransparency(TransparencyAttrib.MAlpha) # 透明描画モード
        self.cylinder.setColor(0, 0, 1, 0.5) # 色の設定
        self.node_cylinder.setPos(self.center) # モデルを中心へ移動

        # 球配置用のノード追加
        self.node_balls = self.render.attachNewNode(PandaNode('scene_node'))

        # キー入力状態の保存
        self.keyMap = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'w': False,
            'a': False,
            's': False,
            'd': False,
        }

        # acceptでキーを押したとき/離したときにキーフラグ更新
        self.accept('arrow_up', self.setKey, ['up', True])
        self.accept('arrow_up-up', self.setKey, ['up', False])
        self.accept('arrow_down', self.setKey, ['down', True])
        self.accept('arrow_down-up', self.setKey, ['down', False])
        self.accept('arrow_left', self.setKey, ['left', True])
        self.accept('arrow_left-up', self.setKey, ['left', False])
        self.accept('arrow_right', self.setKey, ['right', True])
        self.accept('arrow_right-up', self.setKey, ['right', False])

        self.accept("q", self.end)

        # タスク追加
        self.taskMgr.add(self.update, 'updateTask')      

        self.drawtouch = drawTouch(autoDraw=False, stopKey=False)
        self.drawtouch.startDraw()

     # キー状態をセット
    def setKey(self, key, value):
        self.keyMap[key] = value
    
    # 球を配置
    def add_ball(self, coords):
        self.node_balls.removeNode()  # 球が配置されていたノードを削除
        self.node_balls = self.render.attachNewNode(PandaNode('scene_node')) # ノードを再作成
        # ノードに球を配置
        for x, y, z in coords:
            sphere = self.loader.loadModel("models/smiley")  # スフィア状モデルを読み込み
            sphere.reparentTo(self.node_balls)  # シーンにアタッチ
            sphere.setScale(0.3)  # 大きさ変更
            sphere.setPos(x, y, z)  # 位置調整

    """アップデート処理"""
    def update(self, task):
        self.update_move_camera(task)
        self.updateBalls()
        self.drawtouch.updateDraw()
        return task.cont
    
    # キー状態によってカメラを移動
    def update_move_camera(self, task):
        speed = 0.1
        dx, dy = 0, 0
        if self.keyMap['up']:
            dy += speed
        if self.keyMap['down']:
            dy -= speed
        if self.keyMap['left']:
            dx -= speed
        if self.keyMap['right']:
            dx += speed
            
        if dx != 0 or dy != 0:
            pos = self.camera.getPos()
            self.camera.setPos(pos + (dx, dy, 0))
        return task.cont
    
    # ボール描画の更新
    def updateBalls(self):
        centroids = self.drawtouch.centroids
        coords_balls = []
        for coord in centroids:
            theta = 2 * math.pi * coord[0] / (txNum * 100)
            x = self.cylinder_conf["radius"] * math.cos(theta)
            y = self.cylinder_conf["radius"] * math.sin(theta)
            z = -(coord[1] * self.cylinder_conf["height"] / (rxNum * 100) - self.cylinder_conf["height"] / 2)
            coords_balls.append([x, y, z])
        self.add_ball(coords_balls)

    def end(self):
        self.drawtouch.stop_program()
        base.userExit()

"""メイン関数"""
def main():    
    app = App()
    app.run()

if __name__ == '__main__':
    main()