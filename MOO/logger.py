# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 16:40:55 2021

@author: q514347
"""


import time
from datetime import datetime as dt

# In[1]:
def writeLogFile(logfile, message):
    t_start = time.time()
    time_stamp = dt.fromtimestamp(t_start).strftime('%Y-%m-%d %H:%M:%S')

    try:                  
        logfile = open('Data/' + logfile,"a")
        logfile.writelines(time_stamp +' - ' + message + "\n")
    except Exception as e:
        print(str(e))
    finally:
        #logfile.close()
        pass
    return     