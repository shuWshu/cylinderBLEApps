"""
自作モジュール
新ver用の描画プログラム
機能的には元来のプログラムのReaderとdrawの混合
"""

import asyncio
from bleak import BleakClient
import threading
import time
import numpy as np
import cv2

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
            # 出力部分
            for rx in range(rxNum):
                for tx in range(txNum):
                    print(self.gridDatas[tx][rx], end="")
                print()
            print()
        
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

    # 終了フラグ処理
    def stop_program(self):
        print("stop program")
        self.stop_event.set()  # 停止フラグを立てる
        print(f"BLE FPS: {self.count / (self.endTime - self.startTime)}")

class drawTouch():
    def __init__(self, autoDraw=True, stopKey=True, drawing=True):
        self.rate = 100 # 拡大倍率
        self.flagEnd = False # 終了フラグ
        self.autoDraw = autoDraw # ドロー処理を自動的に行うか
        self.stopKey = stopKey # "q"キーでの停止などのキー処理の有無
        self.drawing = drawing # 描画結果を画面に出力するか
        self.startTime = None
        self.count = 0

        self.blereader = BLEreader()

    # 描画開始と処理
    def startDraw(self):
        self.blereader.startBLE()
        if self.autoDraw:
            while 1:
                self.updateDraw()
                key = cv2.waitKey(1)&0xff
                if key == ord("q") and self.stopKey:
                    self._stop_program()
                    break
                elif self.flagEnd:
                    break

    # 描画の更新
    def updateDraw(self):
        if(self.startTime is None):
            self.startTime = time.perf_counter() # 開始時間の記録
        self.endTime = time.perf_counter() # 最後の時間の更新
        self.count += 1 # 描画回数の記録

        canv = self.blereader.getGridDatas().T * 50
        canv_near = cv2.resize(canv, (canv.shape[1]*self.rate, canv.shape[0]*self.rate), interpolation=cv2.INTER_NEAREST) # 通常の拡大
        if self.drawing: # 描画処理の有無
            cv2.imshow("near", canv_near)
            # cv2.imshow("img", img) # 最終的な画像

    def _stop_program(self):
        self.blereader.stop_program()
        print(f"draw FPS: {self.count / (self.endTime - self.startTime)}")

    # 外部からの呼び出し用
    def stop_program(self):
        self._stop_program()
        self.flagEnd = True

def main():
    drawtouch = drawTouch()
    drawtouch.startDraw()

if __name__ == "__main__":
    main()