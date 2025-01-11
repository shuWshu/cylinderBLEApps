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
import json
from collections import deque

thresholdsDictFileName = "BLEApps/thresholdsDict.json"

class drawTouch():
    def __init__(self, autoDraw=True, stopKey=True, drawing=True):
        self.centroids = [] # タッチ領域の重心を格納
        self.stats = [] # タッチ領域の面積などを格納
        self.arrow = [] # 矢印用の座標保存
        self.timelineMaxCentroids = [] # 最大エリアの座標ログを格納
        self.flagFlick = -1 # フリック直前のフラグ -1:未準備，0:準備中，1~:表示フレーム数として管理
        self.rate = 100 # 拡大倍率
        self.threshold = 50 # しきい値
        self.flagEnd = False # 終了フラグ
        self.flagDrag = False # ドラッグ処理のフラグ
        self.dragLog = [] # ドラッグ中の座標を記録する
        self.dragCorrect = 0 # ドラッグ中における，1回転時のx座標補正

        self.deltaxLog = deque([0 for _ in range(5)], 5) # 変化量(変化した時限定)を5つ格納できるキュー

        # キャリブレーション関連
        with open("BLEApps/thresholdsDict.json") as f:
            thresholdsJson = json.load(f)
        self.thresholdsDict = thresholdsJson # 各座標におけるキャリブレーション情報を格納する
        print(self.thresholdsDict)
        self.frameCalibration = 0 # キャリブレーション残りフレーム
        self.flagCalibrated = True # キャリブレーション済みフラグ

        self.autoDraw = autoDraw # ドロー処理を自動的に行うか
        self.stopKey = stopKey # "q"キーでの停止などのキー処理の有無
        self.drawing = drawing # 描画結果を画面に出力するか

        self.blereader = BLEreader()

    def startDraw(self):
        self.blereader.startBLE()
        if self.autoDraw:
            while 1:
                self.updateDraw()
                if cv2.waitKey(1)&0xff == ord("q") and self.stopKey:
                    self._stop_program()
                    break
                elif cv2.waitKey(1)&0xff == ord("c") and self.stopKey:
                    self.calibrationStart()
                elif self.flagEnd:
                    break

    # 描画の更新
    def updateDraw(self):
        canv = np.zeros((rxNum, txNum), np.uint8)  # [rx][tx]での表示値の配列 グレースケール
        timelineDict = self.blereader.getTimelineDict()

        if self.frameCalibration > 0:
            self._calibtation(timelineDict=timelineDict)

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

                # 補正処理
                if self.flagCalibrated: # キャリブレーション済なら
                    valRate = val / self.thresholdsDict[key] # 閾値に対する割合を出す
                    if valRate < 1: # レート1未満=未タッチ
                        val = 0
                    else: 
                        val = min(1023 * (valRate-1) / 2, 1023) # (割合-1)を0~1023に割り当てる．一旦最大倍率3倍
                else:
                    if val < 250: # 250未満については黒色に変更（わかりづらいため）
                        val = 0
                if rx < 3:
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
        idmax = np.unravel_index(np.argmax(canv), canv.shape) # canv内の最大値インデックスを取得→一番明るい座標
        val = canv[idmax[0]][idmax[1]]
        if val < self.threshold: # 領域無し
            self.timelineMaxCentroids.append([]) # タイムラインに追加
        else:
            # maxStatsID = self.stats.index(max(self.stats)) # 最大面積の領域を指定→微妙
            coordMax = (int((idmax[1]+0.5)*self.rate), int((idmax[0]+0.5)*self.rate)) # 最も明るい点について
            img = cv2.circle(img, coordMax, 10, (0, 0, 255), thickness=-1)  # 最も明るい点が割り当てられる座標に描画
            self.timelineMaxCentroids.append(coordMax) # タイムラインに追加

            for _, coord in enumerate(self.centroids):
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
                nowPos = [nowPos[0]+self.dragCorrect, nowPos[1]]
                deltax = nowPos[0]-self.dragLog[-1][0] # 測定値を用いて差分ベクトルを計算
                if deltax != 0: # 差分があるなら
                    deltaLogSign = [np.sign(i) for i in self.deltaxLog] # 正のベクトルを+1，負のベクトルを-1として変換
                    if sum(deltaLogSign) * deltax < 0 and abs(deltax) >= 600: # ベクトルの傾向とdeltaxの符号が一致するか 不一致の場合かつ600以上戻っている場合，端処理を行う
                        if nowPos[0] > self.dragLog[-1][0]: 
                            self.dragCorrect -= (txNum-1) * self.rate # 1週の座標合計値は2200であることが判明
                            nowPos[0] -= (txNum-1) * self.rate
                        else:
                            self.dragCorrect += (txNum-1) * self.rate
                            nowPos[0] += (txNum-1) * self.rate
                    elif abs(nowPos[0] - self.dragLog[-1][0]) > txNum * self.rate / 2: # 端処理，現在地と1つ前のx座標の差が全体の半分を超えたなら
                        if nowPos[0] > self.dragLog[-1][0]: 
                            self.dragCorrect -= (txNum-1) * self.rate # 1週の座標合計値は2200であることが判明
                            nowPos[0] -= (txNum-1) * self.rate
                        else:
                            self.dragCorrect += (txNum-1) * self.rate
                            nowPos[0] += (txNum-1) * self.rate
                
                self.dragLog.append((nowPos[0], nowPos[1])) # 現在地をログに追加
                deltax = self.dragLog[-1][0]-self.dragLog[-2][0]
                if deltax != 0:
                    self.deltaxLog.append(deltax)

                self.dragging()
            elif not any(flagCircles[:dragNum]): # dragNum回分全てログが無いなら
                self.dragLog.clear() # 配列のリセット
                self.dragCorrect = 0 # 補正値のクリア
                self.deltaxLog = deque([0 for _ in range(5)], 5) # 差分ログのクリア
                self.flagDrag = False # フラグオフ
                self.dragEnd()
        else: # 未ドラッグ
            if all(flagCircles[:dragNum]): # 過去dragNum回分の履歴が存在する場合
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

        # 測定値のみを参照してドラッグ処理
        self.dragCheckFromCanv(canv, img)

        if self.drawing: # 描画処理の有無
            cv2.imshow("near", canv_near)
            cv2.imshow("img", img) # 最終的な画像

    # 各マスの測定値からのみでドラッグ判定を行う処理
    def dragCheckFromCanv(self, canv, img): 
        return
        idmax = np.unravel_index(np.argmax(canv), canv.shape) # canv内の最大値インデックスを取得
        val = canv[idmax[0]][idmax[1]]
        if val > 100:
            self.countNotTouch = 0
            self.countTouch += 1
            print(f"{idmax[1]}: {val}") # y座標
            coord = (int((idmax[1]+0.5)*self.rate), int((idmax[0]+0.5)*self.rate))
            img = cv2.circle(img, coord, 30, (0, 0, 255), thickness=-1) # 円の描画
        else:
            self.countNotTouch += 1
            self.countTouch = 1
        
        # TODO:あとでコンストラクタへ移動
        self.xLog = deque([1 for _ in range(3)], 3) # yの値を3つ格納できるキュー
        self.deltaxLog = deque([0], 3) # y変化値(変化した時限定)を3つ格納できるキュー
        self.countNotTouch = 0 # タッチしていないフレームを数える タッチ時0
        self.countTouch = 0 # タッチ状態のフレーム数を数える 非タッチ時0
        self.flagDragCanv = False

        posx = idmax[1] # x座標ID値
        deltax = posx-self.xLog[-1] # x座標変化値
        if self.flagDragCanv: # ドラッグ中なら
            if self.countTouch > 0: # タッチしている
                # ADD:回転判定
                self.xLog.append(posx) # 現座標格納
                if deltax != 0: # 変化しているなら
                    # ADD:変化値の送信
                    self.deltaxLog.append(deltax) # 変化値格納
            elif self.countNotTouch == 6: # ドラッグ終了判定 非タッチ6フレーム
                self.flagDragCanv =  False # ドラッグ終了
        else:
            if self.countNotTouch > 3: # ドラッグ開始判定 タッチ4フレーム
                self.xLog.append(posx) # 現座標(ドラッグ開始時座標)格納
                self.deltaxLog = deque([0], 3) # 変化値はリセット
                self.flagDragCanv =  True # ドラッグ開始

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
        # print(f"({self.dragLog[-1]})") # ドラッグ中座標の出力
        deltax = self.dragLog[-1][0]-self.dragLog[-2][0]
        if deltax != 0:
            print(f"{deltax}({self.dragLog[-1][0]})") # x座標の変化値
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

    # キャリブレーション開始時処理
    def calibrationStart(self):
        print("calibrationStart")
        self.frameCalibration = 180 # キャリブレーション時間の設定
        self.thresholdsDict = {} # 配列のリセット
        self.flagCalibrated = False # キャリブレーション済フラグ
        for rx in range(rxNum):
            for tx in range(txNum):
                key = f"{tx},{rx}"
                self.thresholdsDict[key] = [] # 各値に空配列を代入

    # キャリブレーション
    def _calibtation(self, timelineDict):     
        print("calibration...")   
        for rx in range(rxNum):
            for tx in range(txNum):
                key = f"{tx},{rx}"
                self.thresholdsDict[key].append(timelineDict[key][-1]) # 情報を配列に追加
        self.frameCalibration -= 1

        # キャリブレーション終了時処理
        if self.frameCalibration == 0:
            self._calibtationEnd()

    # キャリブレーション終了時処理
    def _calibtationEnd(self):
        print("calibrationEnd")
        for rx in range(rxNum):
            for tx in range(txNum):
                key = f"{tx},{rx}"
                maxVal = max(self.thresholdsDict[key]) # 配列内最大値を取って，配列に代入
                self.thresholdsDict[key] = maxVal # 代入
        self.flagCalibrated = True # キャリブレーション済フラグ
        with open("BLEApps/thresholdsDict.json", 'w') as f:
            json.dump(self.thresholdsDict, f, indent=2) # json形式で保存
        print(self.thresholdsDict)

def main():
    drawtouch = drawTouch()
    drawtouch.startDraw()

if __name__ == "__main__":
    main()