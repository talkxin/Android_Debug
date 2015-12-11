# 用于计算xy坐标与下一个点的偏差值用于计算采集的精度
import math
import re
x1 = 1121.76
y1 = 2225.54
x2 = 252.84
y2 = 1172.16
# 计算坐标偏差值
pol = format(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2), '.2f') 
print(pol)
