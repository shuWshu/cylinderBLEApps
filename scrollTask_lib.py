"""
実験用
スクロールアプリケーション
共通部分ライブラリ
2025/01/09:到達判定を変更（0.2秒以上停止→0.2秒範囲内にとどまる）
2025/01/10:スクロールをデジタル式に変更
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
# from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, GeomNode, NodePath
import time
import csv

from direct.gui.OnscreenText import OnscreenText

# 三角印の描画関数
def draw_arrows(parent, color=(1, 0, 0, 1)):
    triangle0 = draw_triangle(parent=parent, color=color)
    triangle0.setPos(0.4, 0, 0)
    triangle0.setR(triangle0, -90)
    triangle1 = draw_triangle(parent=parent, color=color)
    triangle1.setR(triangle1, 90)
    triangle1.setPos(-0.4, 0, 0)
    pass
def draw_triangle(parent, color=(1, 0, 0, 1)):
    # -- 1) 頂点情報のフォーマットを指定 --
    format_ = GeomVertexFormat.getV3c4()
    # -- 2) 頂点データ (GeomVertexData) を作成 --
    #   UHStatic (変化なし) / UHDynamic (アニメーション等で頻繁に変化) など
    vdata = GeomVertexData("triangle_data", format_, Geom.UHDynamic)
    # -- 3) 頂点座標・カラーを書き込むための Writer を用意 --
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    color_writer = GeomVertexWriter(vdata, "color")
    # -- 4) 三角形の各頂点を定義 (ここでは XZ 平面上に配置) --
    vertex_writer.addData3f(-0.05, 0, -0.05)  # 頂点0
    color_writer.addData4f(color)     # 赤
    vertex_writer.addData3f( 0.05, 0, -0.05)  # 頂点1
    color_writer.addData4f(color)      # 赤
    vertex_writer.addData3f( 0.0, 0,  0.05)  # 頂点2
    color_writer.addData4f(color)      # 赤
    # -- 5) どの頂点を使ってポリゴン(三角形)を構成するか定義 --
    tri = GeomTriangles(Geom.UHStatic)
    tri.addVertices(0, 1, 2)
    tri.closePrimitive()
    # -- 6) Geom オブジェクトに頂点データと三角形情報をまとめる --
    geom = Geom(vdata)
    geom.addPrimitive(tri)
    # -- 7) GeomNode に Geom を追加し、NodePath にしてシーンに配置 --
    geom_node = GeomNode("triangle")
    geom_node.addGeom(geom)

    triangle = parent.attachNewNode(geom_node)
    return triangle

class App(ShowBase):
    # コンストラクタ
    def __init__(self, ID, DIST, MODE):
        # ShowBaseを継承する
        ShowBase.__init__(self)

        self.ID = ID
        self.DIST = DIST # 距離条件
        self.MODE = MODE # 操作条件

        # ファイル名の決定&ファイルを開く処理
        serialNum = 0
        while True:
            self.filename = f"result_scrollTask_{self.ID}_{self.MODE}_{serialNum}.csv"
            try:
                self.file = open(f'results/{self.filename}', 'x') # ファイルそのもの
                self.writer = csv.writer(self.file) # ライター
                break
            except FileExistsError: # ファイルが既に存在している
                serialNum += 1

        self.SCROLLSTEP = 0.005 # スクロール操作の倍率
        self.MAXNUM = 600 # スクロールの長さ
        self.STARTNUM = 300 # 最初の値
        self.TARGETS = [((i+1)%2)*self.DIST+self.STARTNUM for i in range(10)]

        self.scrollDist = 0.0 # スクロール操作で移動した距離の総量
        self.selectNum = self.STARTNUM # 選択中の値
        self.timeStamp = [] # タイムスタンプ格納
        self.startTime = 0 # 開始時間
        self.targetNum = -1 # ターゲットとしている数
        self.taskProgress = -1 # タスク完了数

        self.lastMoveTime = time.perf_counter() # 最後に移動した時間を記録
        self.lastSwitchTime = time.perf_counter() # 最後に目盛りを切り替えた時間を記録
        self.ROTATEFRAME = 3 # 回転に要するフレーム数
        self.rotateCount = 0 # 残りの回転フレーム数
        self.rotateSpeed = 0 # 回転速度

        # ウインドウの設定
        self.properties = WindowProperties()
        self.properties.setTitle('scroll experiment')
        self.properties.setSize(600, 800)
        self.win.requestProperties(self.properties)
        self.setBackgroundColor(0, 0, 0)

        # シーンノードを作成
        self.node_scrollUI = self.aspect2d.attachNewNode(PandaNode('scene_node')) # スクロールUI
        self.node_scrollUImove = self.node_scrollUI.attachNewNode(PandaNode('scene_node')) # スクロールUIの動くとこ
        self.node_fixUI = self.aspect2d.attachNewNode(PandaNode('scene_node'))
        self.node_scrollUI.setPos(-0.5, 0, 0) # 移動
        self.node_scrollUImove.setPos(0, 0, self.STARTNUM*(0.3)) # 移動
        self.node_fixUI.setPos(0.5, 0, 0)

        # スクロール部分の描画
        cm = CardMaker("myCard") # カードの生成機を作成
        cm.setFrame(-0.4, 0.4, -0.145, 0.145)  # 大きさ（左, 右, 下, 上）
        for n in range(self.MAXNUM):
            card_np = self.node_scrollUImove.attachNewNode(cm.generate()) # カードを生成してアタッチ
            card_np.setPos(0, 0, -0.3*n) # 移動
            card_np.setColor(1, 1, 1, 1) # 色の設定
            OnscreenText(
                text=f"{n}",
                pos=(0, -0.3*n-0.05), # 画面中央上あたり (X, Z)
                scale=0.2, # 文字の大きさ
                fg=(0, 0, 0, 1), # 文字色(R, G, B, A)
                parent=self.node_scrollUImove
            ) # 数字の追加

        draw_arrows(parent=self.node_scrollUI)

        OnscreenText(
            text="Target:",
            pos=(0, 0.4),       # 画面中央上あたり (X, Z)
            scale=0.1,         # 文字の大きさ
            fg=(1, 1, 1, 1),    # 文字色(R, G, B, A)
            parent=self.node_fixUI
        )
        self.target = OnscreenText(
            text="000",
            pos=(0, 0),       # 画面中央上あたり (X, Z)
            scale=0.3,         # 文字の大きさ
            fg=(1, 1, 0, 1),    # 文字色(R, G, B, A)
            parent=self.node_fixUI
        )

        # ゲージの描画
        cm.setFrame(0, 0.8, 0, 0.1)
        gaugeBack = self.node_fixUI.attachNewNode(cm.generate()) # ゲージの背景
        gaugeBack.setPos(-0.4, 0, -0.2) # 移動
        gaugeBack.setColor(1, 1, 1, 1) # 色の設定
        gaugeBack.setScale(1, 1, 1)
        self.gauge = self.node_fixUI.attachNewNode(cm.generate()) # ゲージ本体
        self.gauge.setPos(-0.4, 0, -0.2) # 移動
        self.gauge.setColor(0, 1, 0, 1) # 色の設定
        self.gauge.setScale(0, 1, 1)

        # リセット処理
        self.accept("r", self.reset)
        # 停止処理
        self.accept("q", self.end)
        # スタート処理
        self.accept("s", self.taskStart)

        # アップデート処理タスク追加
        self.taskMgr.add(self.update, 'updateTask')      
    
    # アップデート処理
    def update(self, task):
        if self.taskProgress >= 0: # タスク進捗が負ではない
            self.updateReachTarget()
        if self.rotateCount > 0: # 回転中
            self.rotateCount -= 1
            self.rotateDraw(self.rotateSpeed)
        return task.cont
    
    # ターゲットに到達したかを判定する
    # 到達した場合，次のターゲットへの移行処理
    def updateReachTarget(self):
        if self.selectNum == self.targetNum: # ターゲットを選択している
            downtime = time.perf_counter() - self.lastSwitchTime
            self.gauge.setScale(min(downtime, 1.0), 1, 1)
            if downtime > 1: # 1秒以上目盛りを保持している
            # if time.perf_counter() - self.lastMoveTime > 0.2: # 0.2秒以上停止している
                timeNow = time.perf_counter()
                self.timeStamp.append(timeNow) # タイムスタンプ追加
                self.writer.writerow([timeNow-self.startTime, "Selected"]) # ファイル書き込み
                self.taskProgress += 1
                if self.taskProgress == len(self.TARGETS): # タスク終了判定
                    return self.taskEnd(endTime=timeNow)
                self.set_target()
        else:
            self.gauge.setScale(0, 1, 1)
        
    
    # ファイルを開き直す処理
    def fileReopen(self):
        self.file.close() # ファイルを閉じる
        self.file = open(f'results/{self.filename}', 'w') # ファイルを上書きモードで再度開く
        self.writer = csv.writer(self.file) # ライター

    # 次のターゲットに移る処理
    def set_target(self):
        self.targetNum = self.TARGETS[self.taskProgress] # 次のターゲットを取得
        self.target.text = f"{self.targetNum}" # 次のターゲットに表示変更
    
    # スタート処理
    def taskStart(self):
        self.reset() # 位置のリセット
        self.taskProgress = 0 # タスク進捗のリセット
        self.target.fg=(1, 1, 1, 1) # 文字色変更
        self.fileReopen() # 記録ファイルをリセット
        timeNow = time.perf_counter()
        self.timeStamp = [] # タイムスタンプのリセット
        self.timeStamp.append(timeNow) # タイムスタンプ追加
        self.startTime = timeNow # 開始時間を保存 タイムスタンプ追加
        self.writer.writerow([self.startTime-self.startTime, "start"]) # ファイル書き込み
        self.set_target() # ターゲットのセッティング

    # タスク終了時の処理
    def taskEnd(self, endTime):
        self.writer.writerow([endTime-self.startTime, "end"]) # ファイル書き込み
        time_operation = []
        for i, t in enumerate(self.timeStamp[1:]): # 差分の処理
            time_operation.append(round(t - self.timeStamp[i], 2))
            # print(f"{round(t - self.timeStamp[i], 2)}") # 前との差分
        self.taskProgress = -1 # タスク進捗を-1に戻す
        self.target.text = f"END" # 表示変更
        self.target.fg=(1, 0, 0, 1) # 文字色変更

        with open(f"results/result_scrollTask_{self.ID}.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerow([self.MODE, self.DIST]+time_operation)
    
    # 位置のリセット処理
    def reset(self):
        x, y, z = self.node_scrollUImove.getPos()
        self.node_scrollUImove.setPos(x, y, self.STARTNUM*(0.3))
        self.scrollDist = 0.0 # 合計移動距離
        self.rotateCount = 0 # 残りの回転フレーム数
        self.rotateSpeed = 0 # 回転速度

    # ホイール回転を描画
    def rotateDraw(self, delta_y):
        x, y, z = self.node_scrollUImove.getPos()
        self.node_scrollUImove.setPos(x, y, z+delta_y)

    # ホイール関連に関わる処理
    # 外部的には，移動距離を入力するだけで良い
    def rotate(self, delta_y):
        timeNow = time.perf_counter()
        self.writer.writerow([timeNow-self.startTime, delta_y]) # ファイル書き込み
        self.scrollDist += delta_y # 合計移動距離の記録
        selectNum = -round(self.scrollDist * self.SCROLLSTEP / 0.30) + self.STARTNUM # 現在の目盛りの割出
        if self.selectNum != selectNum: # 目盛りが切り替わっていたら
            self.lastSwitchTime = timeNow # 時間を更新
            self.selectNum = selectNum # 選択値の変更

            self.rotateCount = self.ROTATEFRAME # 残りの回転フレーム数の設定
            _, _, z = self.node_scrollUImove.getPos() # 現在のz座標を取得
            rotateTo = (selectNum)*0.3 # 移動先Z座標の割出
            self.rotateSpeed = (rotateTo-z)/self.ROTATEFRAME # 回転速度の設定
        # print(self.selectNum)
        self.lastMoveTime = timeNow # 最終移動時間を更新

    def end(self):
        self.file.close()
        base.userExit()

# app = App(0, 0, 0)
# app.run()