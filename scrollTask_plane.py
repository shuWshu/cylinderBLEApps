"""
実験用
スクロールアプリケーション
結果をcsvとして出力する
トラックパッド使用ver
"""

import sys, Quartz
from scrollTask_lib import App

# -----パラメータ-----
ID = 0
DIST = 0
MODE = "plane"
# -----パラメータ-----

class App_plane(App):
    # コンストラクタ
    def __init__(self, ID, DIST, MODE):
        # ShowBaseを継承する
        App.__init__(self, ID, DIST, MODE)
        
        self.SCROLLSTEP = 0.004 # スクロール操作の倍率
        
        # ----- スクロールイベントの処理ここから -----
        # システム全体のスクロールイベントを監視
        event_mask = 1 << Quartz.kCGEventScrollWheel
        self.event_tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            event_mask,
            self.scroll_callback,
            None
        )
        if not self.event_tap:
            print("Failed to create event tap.")
            sys.exit(1)
        run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, self.event_tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(),
            run_loop_source,
            Quartz.kCFRunLoopCommonModes
        )
        Quartz.CGEventTapEnable(self.event_tap, True)
        # ----- スクロールイベントの処理ここまで -----     
    
    # スクロール時のコールバック
    # 回転も行う
    def scroll_callback(self, proxy, event_type, event, refcon):
        # トラックパッドまたはマウスホイールのスクロール量を取得
        # delta_x = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGScrollWheelEventPointDeltaAxis2)
        delta_y = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGScrollWheelEventPointDeltaAxis1)
        self.rotate(delta_y)
        
        return event

app = App_plane(ID, DIST, MODE)
app.run()