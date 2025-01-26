import cv2
import numpy as np
import math

# 対象の動画ファイルパス
video_path = "/Users/tamurashun/python/touchSence/BLEApps/output.mp4"

# VideoCapture で動画ファイルを読み込む
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

# Shi-Tomasi コーナー検出（初期特徴点）パラメータ
feature_params = dict(maxCorners=100,       # 最大取得コーナー数
                      qualityLevel=0.3,     # コーナーとして採用する閾値(0～1)
                      minDistance=7,        # 特徴点間の最小距離
                      blockSize=7)

# Lucas-Kanade 法（Pyramidal）のパラメータ
lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# 最初のフレームを取得
ret, old_frame = cap.read()
if not ret:
    print("Error: Could not read the first frame.")
    cap.release()
    exit()

# グレースケール変換
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)

# Shi-Tomasi で特徴点を取得
p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)

# 描画用のマスクを作成（線を描く用）
mask = np.zeros_like(old_frame)
count = 0

while True:
    count += 1
    ret, frame = cap.read()
    if not ret:
        # 動画が終了した場合など
        print("End of video or cannot read frame.")
        break

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 特徴点が無い (None or 空) 場合は再検出
    if p0 is None or len(p0) == 0:
        p0 = cv2.goodFeaturesToTrack(frame_gray, mask=None, **feature_params)
        if p0 is None or len(p0) == 0:
            continue

    # Lucas-Kanade でオプティカルフローを計算（p0 → p1 の移動）
    # p0: 前フレームの特徴点, old_gray: 前フレーム, frame_gray: 現フレーム
    p1, st, err = cv2.calcOpticalFlowPyrLK(
        old_gray, frame_gray, p0, None, **lk_params
    )

    # 追跡に成功した点だけを選別
    good_new = p1[st == 1]
    good_old = p0[st == 1]

    # ---------------------------------------------
    # 向きを含めた合計ベクトル (sum_x, sum_y) を算出
    # ---------------------------------------------
    sum_x = 0.0
    sum_y = 0.0

    for new_pt, old_pt in zip(good_new, good_old):
        x_new, y_new = new_pt.ravel()
        x_old, y_old = old_pt.ravel()
        sum_x += (x_new - x_old)
        sum_y += (y_new - y_old)

    # 合計ベクトルの大きさと向き
    magnitude = math.sqrt(sum_x**2 + sum_y**2)
    angle = math.degrees(math.atan2(sum_y, sum_x))  # 度数で表示

    # print(f"[Frame {count}] 合計ベクトル = ({sum_x:.2f}, {sum_y:.2f}), "
    #       f"大きさ = {magnitude:.2f}, 向き = {angle:.2f} degrees")

    print(sum_x)

    # それぞれの対応点をライン＆円で描画
    for new, old in zip(good_new, good_old):
        x_new, y_new = new.ravel()
        x_old, y_old = old.ravel()

        # 座標を整数にキャスト
        x_new, y_new, x_old, y_old = int(x_new), int(y_new), int(x_old), int(y_old)
        
        if (x_new - x_old)**2 - (y_new - y_old)**2 < 10:
            continue

        # マスクに線を描く
        cv2.line(mask, (x_new, y_new), (x_old, y_old), (0, 255, 0), 2)
        # 現フレームに円を描く
        cv2.circle(frame, (x_new, y_new), 5, (0, 0, 255), -1)

    # 現フレームとマスクを合成
    img = cv2.add(frame, mask)

    cv2.imshow('Lucas-Kanade Optical Flow (Video)', img)

    # キー入力待ち(30ms)
    key = cv2.waitKey(30) & 0xFF
    # 'Esc'キー(27)が押されたら終了
    if key == 27:
        break

    # 次回計算のため、フレームを更新
    old_gray = frame_gray.copy()
    p0 = good_new.reshape(-1, 1, 2)

# 後処理
cap.release()
cv2.destroyAllWindows()
