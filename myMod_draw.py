"""
自作モジュール
タッチ位置の描画
諸々の機能
・フリック
・（ドラッグ）
"""
from myMod_BLEReader import *
from myMod_makeCircle import *
import numpy as np
import cv2
import math

class drawTouch():
    def __init__(self, autoDraw=True, stopKey=True):
        self.centroids = [] # タッチ領域の重心を格納
        self.stats = [] # タッチ領域の面積などを格納
        self.arrow = [] # 矢印用の座標保存
        self.timelineMaxCentroids = [] # 最大エリアの座標ログを格納
        self.flagFlick = -1 # フリック直前のフラグ -1:未準備，0:準備中，1~:表示フレーム数として管理
        self.rate = 100 # 拡大倍率
        self.threshold = 100 # しきい値
        self.flagEnd = False # 終了フラグ
        self.flagDrag = False # ドラッグ処理のフラグ
        self.dragLog = [] # ドラッグ中の座標を記録する
        self.dragCorrect = 0 # ドラッグ中における，1回転時のx座標補正

        self.autoDraw = autoDraw # ドロー処理を自動的に行うか
        self.stopKey = stopKey # "q"キーでの停止の有無

        self.blereader = BLEreader()

    def startDraw(self):
        self.blereader.startBLE()
        if self.autoDraw:
            while 1:
                self.updateDraw()
                if cv2.waitKey(1)&0xff == ord("q") and self.stopKey:
                    self._stop_program()
                    break
                elif self.flagEnd:
                    break

    # 描画の更新
    def updateDraw(self):
        canv = np.zeros((rxNum, txNum), np.uint8)  # [rx][tx]での表示値の配列 グレースケール
        timelineDict = self.blereader.getTimelineDict()
        for rx in range(rxNum):
            for tx in range(txNum):
                key = f"{tx},{rx}"
                
                # フィルタリング処理
                vals = []
                i = -1
                while True:
                    if vals and i < -NPOINT: # 値を1つ以上取得できていて，かつ範囲外
                        break
                    if timelineDict[key][i] > 0:
                        vals.append(timelineDict[key][i])
                    i -= 1
                val = max(vals) # 複数の値があるなら最大値を採用
                if val < 250: # 250未満については黒色に変更（わかりづらいため）
                    val = 0
                canv[rx][tx] =  val * 255 / 1023 # 0~1023を0~255に正規化して代入

        canv_near = cv2.resize(canv, (canv.shape[1]*self.rate, canv.shape[0]*self.rate), interpolation=cv2.INTER_NEAREST) # 通常の拡大
        canv_dst = cv2.resize(canv, (canv.shape[1]*self.rate, canv.shape[0]*self.rate), interpolation=cv2.INTER_CUBIC) # バイキュービック補間での画像拡大
        img = canv_dst.copy() # 描画用に画像のコピーを作成
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB) # 画像をカラーに変換

        # 二値化（閾値は第二引数）
        _, canv_binary = cv2.threshold(canv_dst, self.threshold, 255, cv2.THRESH_BINARY)
        # 輪郭を検出
        contours, _ = cv2.findContours(canv_binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # 輪郭を描画
        img = cv2.drawContours(img, contours, -1, (255,0,0), 3)

        # ラベリング処理
        # ラベル数, ラベル番号が振られた配列(入力画像と同じ大きさ), 物体ごとの座標と面積(ピクセル数), 物体ごとの中心座標
        retval, labels, stats, centroids = cv2.connectedComponentsWithStats(canv_binary)

        # グローバル変数のリセット
        self.centroids = []
        self.stats = []
        # 領域の中心座標を描画する
        for i, coord in enumerate(centroids):
            if(math.isnan(coord[0]) or math.isnan(coord[1])):
                continue
            center = (int(coord[0]), int(coord[1]))
            # 領域が黒なら
            if canv_binary[center[1]][center[0]] == 0:
                continue
            self.centroids.append(center)
            self.stats.append(stats[i][4])

        # 最大領域
        if len(self.centroids) == 0: # 領域無し
            self.timelineMaxCentroids.append([]) # タイムラインに追加
        else:
            # 注意!!!直前にやって失敗したら変更
            # maxStatsID = 0
            maxStatsID = self.stats.index(max(self.stats)) # 最大面積の領域を指定→微妙
            for i, coord in enumerate(self.centroids):
                # print(i)
                if i == maxStatsID: # TODO:最も明るい領域を指定するように変更したい
                    img = cv2.circle(img, coord, 10, (0, 0, 255), thickness=-1) 
                    self.timelineMaxCentroids.append(coord) # タイムラインに追加
                else:
                    img = cv2.circle(img, coord, 10, (255, 0, 0), thickness=-1) # 円の描画

        flagCircles = [] # 過去n回目に，値があることを示す
        recentMaxCentroids = self.timelineMaxCentroids[-6:]
        # 移動履歴の描画
        for i, coord in enumerate(reversed(recentMaxCentroids)):
            if not coord: # 値が無い
                flagCircles.append(False)
                continue
            flagCircles.append(True)
            img = cv2.circle(img, coord, 10, (255, 0, 255), thickness=-1) # 円の描画
        
        # 主にフリック処理
        if all(flagCircles[:3]): # 過去3回分の履歴が存在する場合
            r = make_circle(recentMaxCentroids[-3:]) # # 範囲半径の計算→[中心座標x,y,半径r]
            if r[2] < 30:
                if self.flagFlick < 0: # 未準備
                    self.flagFlick = 0 # フリック準備
                    self.arrow.append((int(r[0]), int(r[1]))) # 始点座標の記録
                    # print("flagFlick")
                if self.flagFlick == 0: # 準備済
                    dist = self.calDist(self.arrow[0][0], self.arrow[0][1], r[0], r[1])
                    if dist > 100:
                        self.arrow.append((int(r[0]), int(r[1]))) # 終点座標の記録
                        self.flagFlick = 5 # 描画フレーム数指定
                        
                        if abs(self.arrow[1][0] - self.arrow[0][0]) > txNum * self.rate / 2: # 端処理
                            if self.arrow[1][0] > self.arrow[0][0]: # 小さい方に+2300
                                vecx = self.arrow[1][0] - (self.arrow[0][0] + txNum * self.rate)
                            else:
                                vecx = (self.arrow[1][0] + txNum * self.rate) - self.arrow[0][0]
                        else:
                            vecx = self.arrow[1][0] - self.arrow[0][0]
                        vecy = self.arrow[1][1] - self.arrow[0][1]
                        self.flick(vecx, vecy, self.arrow[0][0], self.arrow[0][1])
                    else:
                        self.arrow[0] = ((int(r[0]), int(r[1]))) # 始点座標の記録し直し
                        # print("flagFlick")
        else:
            self.flagFlick = -1
            self.arrow.clear()

        dragNum = 4
        # 主にドラッグ処理
        if self.flagDrag: # ドラッグ中
            nowPos = self.timelineMaxCentroids[-1]
            if nowPos: # 現在タッチ中なら
                if abs(nowPos[0] - self.dragLog[-1][0]) > txNum * self.rate / 2: # 端処理，現在地と1つ前のx座標の差が全体の半分を超えたなら
                    if nowPos[0] > self.dragLog[-1][0]: 
                        self.dragCorrect -= txNum * self.rate
                    else:
                        self.dragCorrect += txNum * self.rate
                
                self.dragLog.append((nowPos[0], nowPos[1])) # 現在地をログに追加
                self.dragging()
            elif not any(flagCircles[:dragNum]): # 6回分全てログが無いなら
                self.dragLog.clear() # 配列のリセット
                self.dragCorrect = 0 # 補正値のクリア
                self.flagDrag = False # フラグオフ
                self.dragEnd()
        else: # 未ドラッグ
            if all(flagCircles[:dragNum]): # 過去6回分の履歴が存在する場合
                self.dragLog.append(self.timelineMaxCentroids[-1]) # 現在地をログに追加
                self.flagDrag = True # フラグオン
                self.dragStart()


        # 矢印の描画
        if self.flagFlick > 0:
            if abs(self.arrow[1][0] - self.arrow[0][0]) >  txNum * self.rate / 2: # 端処理
                a0x, a0y = self.arrow[0][:]
                a1x, a1y = self.arrow[1][:]
                if a0x > a1x: # 小さい方に+2300, 大きい方に-2300
                    a1x += txNum * self.rate
                    a0x -= txNum * self.rate
                else:
                    a1x -= txNum * self.rate
                    a0x += txNum * self.rate
                cv2.arrowedLine(img, self.arrow[0], [a1x, a1y], (0, 255, 255), thickness=3, shift=0, tipLength=0.1)
                cv2.arrowedLine(img, [a0x, a0y], self.arrow[1], (0, 255, 255), thickness=3, shift=0, tipLength=0.1)
            else:
                cv2.arrowedLine(img, self.arrow[0], self.arrow[1], (0, 255, 0), thickness=3, shift=0, tipLength=0.1)
            self.flagFlick -= 1
            if self.flagFlick == 0:
                self.arrow.clear()
                self.flagFlick = -1

        cv2.imshow("near", canv_near)
        cv2.imshow("img", img) # 最終的な画像

    # 距離の測定
    # 端同士の場合，特殊処理あり
    def calDist(self, ax, ay, bx, by):
        aax, bbx = ax, bx
        if abs(ax - bx) > txNum * self.rate / 2: # 端処理 座標差が半分以上の場合
            if ax > bx:
                bbx += txNum * self.rate
            else:
                aax += txNum * self.rate
        dist = math.sqrt((aax - bbx) ** 2 + (ay - by) ** 2)
        return dist

    # フリック時処理
    # ベクトル値，始点座標値
    def flick(self, dx, dy, x, y):
        # print(f"vec:({dx}, {dy}), pos:({x}, {y})")
        pass

    # ドラッグ開始
    def dragStart(self):
        print("dragStart")
        pass
    # ドラッグ中
    # 座標格納配列を送信
    def dragging(self):
        print(f"({self.dragLog[-1][0]+self.dragCorrect}, {self.dragLog[-1][1]})") # x軸座標は補正値を含める
        pass
    # ドラッグ終了
    def dragEnd(self):
        print("dragEnd")
        pass

    def _stop_program(self):
        self.blereader.stop_program()

    def stop_program(self):
        self._stop_program()
        self.flagEnd = True

def main():
    drawtouch = drawTouch()
    drawtouch.startDraw()

if __name__ == "__main__":
    main()