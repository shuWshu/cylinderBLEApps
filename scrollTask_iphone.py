"""
実験用
スクロールアプリケーション
結果をcsvとして出力する
iphone使用ver
"""

from scrollTask_lib import App
import threading
import asyncio
from bleak import BleakClient
import struct
import numpy as np
import time

# -----パラメータ-----
ID = 0
DIST = 0
MODE = "iphone"
# -----パラメータ-----

# デバイスのUUID
ADDRESS = "31431660-1227-C421-B734-116FD0C31D8E"
# キャラクタリスティックのUUID
CHARACTERISTIC_UUID = "5bc0d364-2f01-33b8-481f-97c39bbd5bdd"

class App_iphone(App):
    # コンストラクタ
    def __init__(self, ID, DIST, MODE):
        # 継承
        App.__init__(self, ID, DIST, MODE)
        # グローバル変数
        self.stop_event = threading.Event()  # 停止フラグ
        self.data_lock = threading.Lock() 

        self.SCROLLSTEP = - 0.3 / 55.0 # スクロール操作の倍率

        self.startBLE()

    # BLEデータ取得時の処理
    # sender:送り元情報 data:データ本体(byte)
    def _notification_handler(self, sender, data):
        dataFloat32 = struct.unpack('<f', data)[0]  # リトルエンディアンで float1つを解釈
        print(dataFloat32)
        self.rotate(delta_y=dataFloat32)

     # ble関連処理
    async def _run_asyncio(self, address):
        async with BleakClient(address) as client:
            await client.start_notify(CHARACTERISTIC_UUID, self._notification_handler) # 指定したキャラクタリスティックのノーティフィケーションを設定
            # await asyncio.sleep(OperateTime) # 一定時間待機（データを受信）
            while not self.stop_event.is_set(): # プログラム停止を認識するとbreak
                await asyncio.sleep(0.1)
            # ノーティフィケーションの停止
            await client.stop_notify(CHARACTERISTIC_UUID)

    # 別スレッドでbleを起動する
    def _run_ble(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_asyncio(ADDRESS))

    def startBLE(self):
        self.thread_ble = threading.Thread(target=self._run_ble) # BLEスレッドの作成
        self.thread_ble.start()

    def end(self):
        self.stop_event.set()  # 停止フラグを立てる
        return super().end()

def main():
    app = App_iphone(ID, DIST, MODE)
    app.run()

if __name__ == "__main__":
    main()