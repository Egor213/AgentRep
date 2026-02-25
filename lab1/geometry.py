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
