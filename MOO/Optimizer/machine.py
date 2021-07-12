# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 11:19:11 2021

@author: Q514347
"""

class Machine:
    def __init__(self, machine_name, runtime, status):
        self.machine_name = machine_name
        self.runtime = runtime
        self.status = status
    
    def get_status(self):
        return self.status
    
    def set_status(self, status):
        self.status = status