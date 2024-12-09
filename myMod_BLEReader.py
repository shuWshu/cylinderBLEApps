"""
自作モジュール
BLE用のクラス
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
# from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, GeomNode, NodePath
import asyncio
from bleak import BleakClient
import time
import threading
from collections import deque

# from make_circle import make_circle

"""固定数"""
txNum = 23
rxNum = 8
NPOINT = 5
DEQUESIZE = 100
# デバイスのMACアドレスまたはUUID
ADDRESS = '44149F07-765B-ABB3-AE31-2262261B8B71' # Nano ESP32用
# キャラクタリスティックのUUIDリスト（Arduinoコードで設定したUUIDに対応）
CHARACTERISTIC_UUIDS = [
    "b70c5e87-fcd8-eec1-bf23-6e98d6b38730",
    "b70c5e87-fcd8-eec1-bf23-6e98d6b38731",
    "b70c5e87-fcd8-eec1-bf23-6e98d6b38732",
    "b70c5e87-fcd8-eec1-bf23-6e98d6b38733",
    "b70c5e87-fcd8-eec1-bf23-6e98d6b38734"
]

"""クラス定義"""
# BLE用クラス
class BLEreader():
    def __init__(self):
        # グローバル変数
        self.stop_event = threading.Event()  # 停止フラグ
        self.data_lock = threading.Lock()
        self.timestamp = [] # タイムスタンプ
        self.timelineDict = {} # 各座標における測定値リストを格納  

        # timelineDict初期化
        for rx in range(rxNum):
            for tx in range(txNum):
                key = f"{tx},{rx}"
                self.timelineDict[key] = deque([500 for _ in range(NPOINT)], DEQUESIZE) # エラー対策で1埋め配列を作る
        self.timelineDict["acX"] = deque([1 for _ in range(NPOINT)], DEQUESIZE)
        self.timelineDict["acY"] = deque([1 for _ in range(NPOINT)], DEQUESIZE)
        self.timelineDict["acZ"] = deque([1 for _ in range(NPOINT)], DEQUESIZE)
        self.timelineDict["angX"] = deque([1 for _ in range(NPOINT)], DEQUESIZE)
        self.timelineDict["angY"] = deque([1 for _ in range(NPOINT)], DEQUESIZE)
        self.timelineDict["angZ"] = deque([1 for _ in range(NPOINT)], DEQUESIZE)

    # BLEデータ取得時の処理
    # sender:送り元情報 data:データ本体(byte)
    def _notification_handler(self, sender, data):
        dataStr = str(data.decode())
        # print(dataStr)
        self.timestamp.append(time.perf_counter())
        dataRows = dataStr.split(":")
        self._updateTimeline(dataRows) # タイムラインの更新

    # ble関連処理
    async def _run_asyncio(self, address):
        async with BleakClient(address) as client:
            # 指定したキャラクタリスティックのノーティフィケーションを設定
            for uuid in CHARACTERISTIC_UUIDS:
                await client.start_notify(uuid, self._notification_handler)
            # # 一定時間待機（データを受信）
            # await asyncio.sleep(OperateTime)
            # プログラム停止を認識
            while not self.stop_event.is_set():
                await asyncio.sleep(0.1)
            # ノーティフィケーションの停止
            for uuid in CHARACTERISTIC_UUIDS:
                await client.stop_notify(uuid)

    # 別スレッドでbleを起動する
    def _run_ble(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_asyncio(ADDRESS))

    # データ格納配列の更新
    def _updateTimeline(self, dataRows):
        with self.data_lock:
            for dataRow in dataRows:
                if dataRow:
                    if dataRow[0] != "_":
                        datas = dataRow.split(",")
                        datas = [int(d) for d in datas]
                        for rx, val in enumerate(datas[1:]):
                            tx = datas[0]
                            key = f"{tx},{rx}"
                            self.timelineDict[key].append(val)
                    elif dataRow[0] == "_": # 加速度センサ値
                        datas = dataRow.split("_")
                        self.timelineDict["acX"].append(datas[1])
                        self.timelineDict["acY"].append(datas[2])
                        self.timelineDict["acZ"].append(datas[3])
                        self.timelineDict["angX"].append(datas[4])
                        self.timelineDict["angY"].append(datas[5])
                        self.timelineDict["angZ"].append(datas[6])
                        # print(datas[1:])

    def startBLE(self):
        self.thread_ble = threading.Thread(target=self._run_ble) # BLEスレッドの作成
        self.thread_ble.start()

    # タイムラインの取得
    def getTimelineDict(self):
        return self.timelineDict

    # 終了フラグ処理
    def stop_program(self):
        print("stop program")
        self.stop_event.set()  # 停止フラグを立てる