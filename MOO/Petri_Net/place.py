# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 15:16:57 2021

@author: q514347
"""

class Place:
    def __init__(self, place_id, place_label, place_type, place_performer=None, tokens=0, place_status="available"):
        #place_type - initial, machine, stock
        self.place_id = place_id
        self.place_label = place_label
        self.place_type = place_type
        self.place_performer = place_performer
        self.tokens = tokens
        self.place_status = place_status
        
    def getId(self):
        return self.place_id
        
    def getLabel(self):
        return self.place_label
    
    def getTokens(self):
        return self.tokens
    
    def getPerformer(self):
        return self.place_performer    
    
    def getPlaceStatus(self):
        if self.place_type == "machine":
            return self.place_performer.get_machine_status()
        elif self.place_type == "stock":
            return self.place_performer.get_stock_status()
        else:
            return self.place_status
    
    def pop_token(self):
        self.tokens -= 1
    
    def push_token(self):
        self.tokens += 1