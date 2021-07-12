# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 08:37:31 2021

@author: Q514347
"""
import json
import http.client as client

def get_stock_data(stock_id):
    c = client.HTTPConnection('localhost', 8080)
    c.request('GET', '/stock/'+ stock_id)
    result = c.getresponse().read()
    c.close()
    data_string = result.decode('utf-8')
    data_dict = json.loads(data_string)
    return data_dict['result'][0]


def update_stock(stock_id, level):
    data = {'stock_id': stock_id, 'level': str(level)}
    c = client.HTTPConnection('localhost', 8080)
    c.request('POST', '/set_stock_level', json.dumps(data))
    c.close()
    return True

class Stock:
    def __init__(self, stock_id, stock_type, max_level, current_level=0, stock_product=None):
        self.stock_id = stock_id
        self.stock_type = stock_type
        self.max_level = max_level
        self.current_level = current_level
        self.stock_product = stock_product
        
    def deposit_stock(self, level):
        try:
# =============================================================================
#            self.current_level = self.get_stock_level()
#             if (self.current_level + level) > self.max_level:
#                 raise Exception("Stock max limit breach")
#             else: 
# =============================================================================
            self.current_level += level
            if update_stock(self.stock_id, self.current_level):
                return True
        except Exception as e:
            print(str(self.stock_id) + " " + str(e))
            return False
            
    def withdraw_stock(self, level):
        try: 
# =============================================================================
#             if (self.current_level - level) < 0:
#                 raise Exception("Stock min limit breach")
#             else:
# =============================================================================
            self.current_level -= level
            update_stock(self.stock_id, self.current_level)
            return True, 'enough stock'
        except Exception as e:
            print(str(self.stock_id) + " " + str(e))       
            return False, 'not enough stock'
            
        
    def get_stock_level(self):
        #return self.current_level
        return get_stock_data(self.stock_id)[4]
        
    def get_stock_type(self):
        return self.get_stock_type
    
    def as_dict(self):
        return {'stock_id': self.stock_id, 'stock_type': self.stock_type, 'max_level': self.max_level, 
                'current_level': self.current_level, 'stock_product': self.stock_product}
    
    
class StockSet:
    def __init__(self):
        self.stocks = []
    
    def addStock(self, stock):
        self.stocks.append(stock)
    
    def removeStock(self, stock):
        self.stocks.remove(stock)
        
    def get_stock_by_id(self, stock_id):
        for obj in self.stocks:
            if obj.stock_id == stock_id:
                return obj
        return None


# =============================================================================
# a = Stock(1, 'intermediate', 100, stock_product="A")
# b = StockSet()
# b.addStock(a)
# print(b.get_stock_by_id(1).stock_product)
# =============================================================================
