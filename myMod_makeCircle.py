# smallest_enclosing_circle.py から一部引用 (Nayuki氏の実装)
# https://www.nayuki.io/res/smallest-enclosing-circle.py
import math
import random

def make_circle(points):
    # 複製
    shuffled = points[:]
    random.shuffle(shuffled)

    c = None
    for i, p in enumerate(shuffled):
        if c is None or not is_in_circle(c, p):
            c = _make_circle_one_point(shuffled[:i+1], p)
    return c

def _make_circle_one_point(points, p):
    c = (p[0], p[1], 0.0)
    for i, q in enumerate(points):
        if not is_in_circle(c, q):
            if c[2] == 0.0:
                c = make_diameter(p, q)
            else:
                c = _make_circle_two_points(points[:i+1], p, q)
    return c

def _make_circle_two_points(points, p, q):
    circ = make_diameter(p, q)
    left = None
    right = None
    px, py = p
    qx, qy = q

    # For each point not in the two-point circle
    for r in points:
        if is_in_circle(circ, r):
            continue

        # Form a circumcircle and classify it on left or right side
        cross = cross_product(px, py, qx, qy, r[0], r[1])
        c = make_circumcircle(p, q, r)
        if c is None:
            continue
        elif cross > 0.0 and (left is None or cross_product(px, py, qx, qy, c[0], c[1]) > cross_product(px, py, qx, qy, left[0], left[1])):
            left = c
        elif cross < 0.0 and (right is None or cross_product(px, py, qx, qy, c[0], c[1]) < cross_product(px, py, qx, qy, right[0], right[1])):
            right = c

    # Select which circle to return
    if left is None and right is None:
        return circ
    elif left is None:
        return right
    elif right is None:
        return left
    else:
        return left if (left[2] <= right[2]) else right

def make_diameter(a, b):
    cx = (a[0] + b[0]) / 2.0
    cy = (a[1] + b[1]) / 2.0
    r0 = math.dist(a, (cx, cy))
    r1 = math.dist(b, (cx, cy))
    return (cx, cy, max(r0, r1))

def make_circumcircle(a, b, c):
    # Mathematical algorithm from Wikipedia: Circumscribed circle
    ox = (min(a[0], b[0], c[0]) + max(a[0], b[0], c[0])) / 2.0
    oy = (min(a[1], b[1], c[1]) + max(a[1], b[1], c[1])) / 2.0
    ax = a[0] - ox; ay = a[1] - oy
    bx = b[0] - ox; by = b[1] - oy
    cx = c[0] - ox; cy = c[1] - oy
    d = (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by)) * 2
    if d == 0:
        return None
    x = ox + ((ax*ax + ay*ay)*(by - cy) + (bx*bx + by*by)*(cy - ay) + (cx*cx + cy*cy)*(ay - by))/d
    y = oy + ((ax*ax + ay*ay)*(cx - bx) + (bx*bx + by*by)*(ax - cx) + (cx*cx + cy*cy)*(bx - ax))/d
    ra = math.dist((x, y), a)
    rb = math.dist((x, y), b)
    rc = math.dist((x, y), c)
    return (x, y, max(ra, rb, rc))

MULTIPLICATIVE_EPSILON = 1 + 1e-14

def is_in_circle(c, p):
    return c is not None and math.dist(p, (c[0], c[1])) <= c[2] * MULTIPLICATIVE_EPSILON

def cross_product(x1, y1, x2, y2, x3, y3):
    return (x2 - x1)*(y3 - y1) - (y2 - y1)*(x3 - x1)



def main():
    # --- ここから実行例 ---
    points = [(1,2), (2,2), (0,3), (4,5), (5,1), (2.5,2.5), (3,2), (2,3), (1,1), (2,1)]
    desired_r = 3.0

    c = make_circle(points)  # 最小包含円を求める
    if c[2] <= desired_r:
        print("半径{0}の円でカバー可能です".format(desired_r))
    else:
        print("半径{0}ではカバーできません".format(desired_r))