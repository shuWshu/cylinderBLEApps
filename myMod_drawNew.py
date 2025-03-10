"""
自作モジュール
新ver用の描画プログラム
機能的には元来のプログラムのReaderとdrawの混合
スクロール機能も搭載
"""

import asyncio
from bleak import BleakClient
import threading
import time
import numpy as np
import cv2
import math
from scipy.signal import convolve2d
import pyautogui

# from make_circle import make_circle

"""固定数"""
txNum = 23
rxNum = 8
UUIDDIV = "44149F07-765B-ABB3-AE31-2262261B8B71" # デバイスid
UUIDCHA = "b70c5e87-fcd8-eec1-bf23-6e98d6b38730" # キャラクタリスティックid

"""クラス定義"""
# BLE用クラス
class BLEreader():
    def __init__(self):
        # グローバル変数
        self.stop_event = threading.Event()  # 停止フラグ
        self.data_lock = threading.Lock()
        self.timestamp = [] # タイムスタンプ
        self.gridDatas = np.zeros((txNum, rxNum), dtype=np.uint8) # 格子点の座標データを格納する
        self.startTime = None
        self.count = 0

    # ハンドラ
    def _notification_handler(self, sender, data):
        if(self.startTime is None):
            self.startTime = time.perf_counter() # 開始時間の記録
        self.endTime = time.perf_counter() # 最後の時間の更新
        self.count += 1 # 取得回数の記録

        length = len(data) # 長さによって送信された情報を区別
        if length == 23: # 格子点のタッチ判定 TODO:配列に格納する処理に変えておく
            output = [""]*8
            for bit_index in range(184):
                # どのバイトか？ bit_index // 8
                # バイト内のどのビットか？ bit_index % 8
                byte_val = data[bit_index // 8]
                bit_val = (byte_val >> (bit_index % 8)) & 0x01
                output[bit_index % 8] += f"{bit_val}"
            for i in range(8):
                print(output[i])
            print()
        elif length == 46: # 格子点のタッチ判定 2bit版
            for tx in range(txNum):
                dataTx = int.from_bytes(data[(tx*2):(tx*2+2)],  "little")
                for rx in range(rxNum):
                    val2bit = (dataTx >> rx*2) & 0x03
                    self.gridDatas[tx][rx] = val2bit
            # # 出力部分
            # for rx in range(rxNum):
            #     for tx in range(txNum):
            #         print(self.gridDatas[tx][rx], end="")
            #     print()
            # print()
        
    # ble関連処理
    async def _run_asyncio(self, address):
        async with BleakClient(address) as client:
            await client.start_notify(UUIDCHA, self._notification_handler)
            # プログラム停止を認識
            while not self.stop_event.is_set():
                await asyncio.sleep(0.1)
            # ノーティフィケーションの停止
            res=await client.stop_notify(UUIDCHA)
            

    # 別スレッドでbleを起動する
    def _run_ble(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_asyncio(UUIDDIV))

    def startBLE(self):
        self.thread_ble = threading.Thread(target=self._run_ble) # BLEスレッドの作成
        self.thread_ble.start()

    # グリッドデータの取得
    def getGridDatas(self):
        return self.gridDatas
    
    def getCount(self):
        return self.count

    # 終了フラグ処理
    def stop_program(self):
        print("stop program")
        self.stop_event.set()  # 停止フラグを立てる
        print(f"BLE FPS: {self.count / (self.endTime - self.startTime)}")

class drawCV2():
    def __init__(self, autoDraw=True, stopKey=True, drawing=True, outMP4=False):
        self.rate = 100 # 拡大倍率
        self.flagEnd = False # 終了フラグ
        self.autoDraw = autoDraw # ドロー処理を自動的に行うか
        self.stopKey = stopKey # "q"キーでの停止などのキー処理の有無
        self.drawing = drawing # 描画結果を画面に出力するか
        self.outMP4 = outMP4 # 動画出力するか
        
        self.canv_prev = None
        self.diff_scroll = 0.0
        self.diff_x = 0.0 # x軸移動値の合計
        self.diff_y = 0.0 # y軸移動値の合計
        self.blecount = 0 # ble側のカウントの記録
        self.flagWrite = False # スクショ機能

        # fps測定用
        self.startTime = None
        self.count = 0

        fps = 30
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter('BLEApps/output.mp4', fourcc, fps, ((txNum+10), rxNum), isColor=False)

        self.blereader = BLEreader()

    # 描画開始と処理
    def startDraw(self):
        self.blereader.startBLE()
        if self.autoDraw:
            while 1:
                self.updateDraw()
                key = cv2.waitKey(1)&0xff
                if key == 27 and self.stopKey: # escでコード停止
                    self.stop_program()
                    break
                elif self.flagEnd:
                    break
                # elif key == ord("w"):
                #     self.flagWrite = True
                # 非描画時に時限ストップさせる関数
                if not self.drawing and self.count > 600:
                    self.stop_program()
                    break

    # 描画の更新
    def updateDraw(self):
        blecount = self.blereader.getCount()
        if self.blecount == blecount: # ble受信が行われていない 過処理防止用
            return
        self.blecount = blecount

        if(self.startTime is None):
            self.startTime = time.perf_counter() # 開始時間の記録
        self.endTime = time.perf_counter() # 最後の時間の更新
        self.count += 1 # 描画回数の記録

        canv = self.blereader.getGridDatas() # グリッドの取得

        # for tx in range(txNum):
        #     for rx in range(rxNum):
        #         if canv[tx][rx] == 1:
        #             flagProx = False
        #             for i in range(3):
        #                 if tx+i-1 < 0 or tx+i-1 >= txNum:
        #                     continue
        #                 for j in range(3):
        #                     if rx+j-1 < 0 or rx+j-1 >= rxNum or i == j == 1:
        #                         continue
        #                     if canv[tx+i-1][rx+j-1] != 0:
        #                         flagProx = True
        #             if not flagProx:
        #                 canv[tx][rx] = 0
        #         elif canv[tx][rx] > 1: # 2以上の場合は周りのマスへ波及する
        #             for i in range(3):
        #                 if tx+i-1 < 0 or tx+i-1 >= txNum:
        #                     continue
        #                 for j in range(3):
        #                     if rx+j-1 < 0 or rx+j-1 >= rxNum or i == j == 1:
        #                         continue
        #                     if canv[tx+i-1][rx+j-1] == 0:
        #                         print("test")
        #                         canv[tx+i-1][rx+j-1] == 1
        # #print(canv)

        canv = canv * 85 # 関数処理
        kernel = [[1/4, 2/4, 1/4],
                  [2/4, 4/4, 2/4],
                  [1/4, 2/4, 1/4]] # 3x3 のフィルタ
        kernel = kernel / np.sum(kernel) 
        # kernel = [[1/3, 1/3, 1/3]] # 横方向（=rx方向）のみの平均フィルタ
        canv = convolve2d(canv, kernel, mode='same', boundary='symm', fillvalue=0) # 畳み込み
        canv = canv.astype(np.uint8) # 整数に戻す

        canv_out = canv[:].T # 描画用のcanv

        canv = np.concatenate([canv, canv])  # 横幅の延長，転置
        canv = canv.T
        canv = np.concatenate([canv, canv]) # 縦幅の延長

        if not self.canv_prev is None: # オプティカルフロー処理
            flow = cv2.calcOpticalFlowFarneback(
                self.canv_prev,          # 前フレーム(グレースケール)
                canv,          # 現フレーム(グレースケール)
                None,               # 出力：光フロー (初期値なし)
                pyr_scale=0.5,      # 各レベルの画像スケール (ピラミッド)
                levels=3,           # ピラミッドのレベル数
                winsize=15,         # 窓サイズ (平均を取る範囲)
                iterations=3,       # 各レベルでの反復回数
                poly_n=5,           # ガウス近似に使う領域サイズ
                poly_sigma=1.2,     # poly_n に対するガウス標準偏差
                flags=0
            )
            sum_x = flow[..., 0].sum() / (txNum*rxNum*4) # x方向移動ベクトルの平均 
            sum_y = flow[..., 1].sum() / len(flow[..., 1])# y方向移動ベクトルの平均 xよりもうまく行っていない
            self.diff_x += sum_x
            self.diff_y += sum_y
            if abs(sum_y) > 5:
                self.sliding(diff=sum_y)
            
            self.scrolling(diff=sum_x)
            print(self.diff_x)
        self.canv_prev = canv[:] # 前のフレームを保存
        
        canv_near = cv2.resize(canv_out, (canv_out.shape[1]*self.rate, canv_out.shape[0]*self.rate), interpolation=cv2.INTER_NEAREST) # 通常の拡大
        #canv_dst = cv2.resize(canv, (canv.shape[1]*self.rate, canv.shape[0]*self.rate), interpolation=cv2.INTER_CUBIC) # バイキュービック補間での画像拡大
        #canv_b = np.zeros_like(canv_near) # 同じ大きさの黒い画像

        threshold = 75 # 2値化の閾値
        _, canv_binary = cv2.threshold(canv_near, threshold, 255, cv2.THRESH_BINARY) # 二値化（閾値は第二引数）
        # ラベル数, ラベル番号が振られた配列(入力画像と同じ大きさ), 物体ごとの座標と面積(ピクセル数), 物体ごとの中心座標
        retval, labels, stats, centroids = cv2.connectedComponentsWithStats(canv_binary) # 塊のラベリング処理

        img = canv_near
        # 領域の中心座標を描画
        for i, coord in enumerate(centroids):
            if(math.isnan(coord[0]) or math.isnan(coord[1])):
                continue
            center = (int(coord[0]), int(coord[1]))
            if canv_binary[center[1]][center[0]] == 0: # 領域が黒なら
                continue
            img = cv2.circle(img, center, 10, (255, 0, 0), thickness=-1)
            #print(center, end="")
        #print()

        if self.drawing: # 描画処理の有無
            cv2.imshow("img", img) # 画像出力
        # if self.flagWrite:
        #     cv2.imwrite('drawNew.jpg', img)
        #     self.flagWrite = False
        # if self.outMP4: # 動画保存
        #     print(self.outMP4)
        #     self.out.write(img)

    def stop_program(self):
        self.blereader.stop_program()
        self.out.release()
        self.flagEnd = True
        print(f"draw FPS: {self.count / (self.endTime - self.startTime)}")

    # -----アプリで呼び出す用の関数-----
    # 円周方向へのスライド操作
    def scrolling(self, diff):
        # print(diff)
        pass
    # 円筒軸方向へのスライド操作
    def sliding(self, diff):
        # print(diff)
        pass
    def flicking(self, diff):
        pass

def main():
    drawtouch = drawCV2(drawing=True,  outMP4=False)
    drawtouch.startDraw()

if __name__ == "__main__":
    main()