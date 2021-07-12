# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 09:21:47 2021

@author: Q514347
"""

import math

e = math.exp
avg_break_time = 222
repair_time = 0
idle_time_introduced = 0
probability = 0
repair_duration = 100

for i in range(1000):
    result = e(-(i-repair_time-idle_time_introduced)/avg_break_time)
    probability = 1 - result
    
    if probability > 0.7:
        idle_time_introduced += 1
        repair_time = i
    
        print(i, probability, idle_time_introduced, repair_time)