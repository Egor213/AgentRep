# import numpy as np


# def circle_intersection(center_1: tuple, radius_1, center_2: tuple, radius_2):
#     c1 = np.array(center_1)
#     c2 = np.array(center_2)

#     # Расстояние между центрами окружностей
#     d_vec = c2 - c1
#     d = np.linalg.norm(d_vec)

#     # r2**2 = r1**2 + d**2 - 2 * r1 * d * cos (alpha)
#     # a = r1 * cos (alpha)
#     a = (radius_1**2 - radius_2**2 + d**2) / (2 * d)
    
#     h = np.sqrt(radius_1**2 - a**2)

#     p_mid = c1 + (a / d) * d_vec
    
#     # Единичный вектор перпендикуляра
#     perp = np.array([-d_vec[1], d_vec[0]]) / d
    
#     if h < 1e-10:  # касание
#         return [(float(p_mid[0]), float(p_mid[1]))]
    
#     return [
#         (float(p_mid[0] + h * perp[0]), float(p_mid[1] + h * perp[1])),
#         (float(p_mid[0] - h * perp[0]), float(p_mid[1] - h * perp[1]))
#     ]


import numpy as np
import math
from itertools import combinations

def circle_intersection(c1, r1, c2, r2):
    """Базовое пересечение двух окружностей (как в предыдущих примерах)"""
    x1, y1 = c1
    x2, y2 = c2
    
    d_vec = np.array([x2 - x1, y2 - y1])
    d = np.linalg.norm(d_vec)
    
    if d > r1 + r2 or d < abs(r1 - r2) or (d == 0 and r1 == r2):
        return None
    
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h_sq = r1**2 - a**2
    
    if h_sq < 0:
        if abs(h_sq) < 1e-10:
            h_sq = 0
        else:
            return None
    
    h = math.sqrt(max(0, h_sq))
    
    p_mid_x = x1 + (a / d) * (x2 - x1)
    p_mid_y = y1 + (a / d) * (y2 - y1)
    
    if h == 0:
        return [(p_mid_x, p_mid_y)]
    else:
        perp_x = -(y2 - y1) / d
        perp_y = (x2 - x1) / d
        
        return [
            (p_mid_x + h * perp_x, p_mid_y + h * perp_y),
            (p_mid_x - h * perp_x, p_mid_y - h * perp_y)
        ]

def trilateration_3d(circles):
    """
    Точное определение позиции по 3 окружностям
    circles: список [(x1,y1,r1), (x2,y2,r2), (x3,y3,r3)]
    """
    if len(circles) < 3:
        return None
    
    # Распаковываем данные
    (x1, y1), r1 = circles[0][:2], circles[0][2]
    (x2, y2), r2 = circles[1][:2], circles[1][2]
    (x3, y3), r3 = circles[2][:2], circles[2][2]
    
    # Преобразуем координаты для упрощения
    # Помещаем первую окружность в начало координат
    x2_ = x2 - x1
    y2_ = y2 - y1
    x3_ = x3 - x1
    y3_ = y3 - y1
    
    # Расстояния между центрами
    d = math.sqrt(x2_**2 + y2_**2)
    
    if d == 0:
        return None
    
    # Координаты в новой системе (вдоль оси X)
    ex = (x2_ / d, y2_ / d)
    
    # Проекция третьей точки на ось X
    i = ex[0] * x3_ + ex[1] * y3_
    
    # Перпендикулярная ось
    ey = (x3_ - i * ex[0], y3_ - i * ex[1])
    j = math.sqrt(ey[0]**2 + ey[1]**2)
    
    if j > 0:
        ey = (ey[0] / j, ey[1] / j)
    
    # Расстояние от первой точки до пересечения вдоль оси X
    x = (r1**2 - r2**2 + d**2) / (2 * d)
    
    # Расстояние до точки пересечения по перпендикуляру
    y_sq = r1**2 - x**2
    
    if y_sq < 0:
        if abs(y_sq) < 1e-10:
            y_sq = 0
        else:
            return None
    
    y = math.sqrt(y_sq)
    
    # Координаты в новой системе
    p1_new = (x, y)
    p2_new = (x, -y)
    
    # Переводим обратно в исходную систему
    p1 = (
        x1 + p1_new[0] * ex[0] + p1_new[1] * ey[0],
        y1 + p1_new[0] * ex[1] + p1_new[1] * ey[1]
    )
    
    p2 = (
        x1 + p2_new[0] * ex[0] + p2_new[1] * ey[0],
        y1 + p2_new[0] * ex[1] + p2_new[1] * ey[1]
    )
    
    # Проверяем, какая точка подходит для третьей окружности
    dist1 = math.sqrt((p1[0] - x3)**2 + (p1[1] - y3)**2)
    dist2 = math.sqrt((p2[0] - x3)**2 + (p2[1] - y3)**2)
    
    err1 = abs(dist1 - r3)
    err2 = abs(dist2 - r3)
    
    if err1 < err2 and err1 < 0.1:  # порог погрешности
        return p1
    elif err2 < 0.1:
        return p2
    else:
        return None