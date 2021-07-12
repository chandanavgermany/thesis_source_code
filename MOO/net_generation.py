# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 16:01:32 2021

@author: q514347
"""
import json
import pandas as pd
import http.client as client
from sqlalchemy import create_engine
from Petri_Net.machines import Machine, MachineSet
from Petri_Net.stocks import Stock, StockSet
from Petri_Net.petri_net import get_petri_net_model

engine = create_engine('postgresql://postgres:popup123@localhost:5432/petri_net')

def clear_machine_stock_data():
    c = client.HTTPConnection('localhost', 8080)
    c.request('POST', '/clear_machine_stock_data/')
    result = c.getresponse().read()
    c.close()
    data_string = result.decode('utf-8')
    data_dict = json.loads(data_string)
    print(data_dict['result'])
    
def add_machine_data_to_db(machine_df):
    machine_df = machine_df.set_index('machine_id')
    machine_df = machine_df.drop(['old_takt_time'], axis=1)
    machine_df.to_sql('machine_info', engine, if_exists='append')
    
def add_stock_data_to_db(stock_df):
    stock_df = stock_df.set_index('stock_id')
    stock_df.to_sql('stock_info', engine, if_exists='append')    
    
def generate_machine_set(machine_df):
    machine_df['machine_id'] = 'M' + machine_df['machine_id'].astype(str)
    add_machine_data_to_db(machine_df)
    machine_set = MachineSet()
    for index, row in machine_df.iterrows():
        machine_obj = Machine(row['machine_id'], row['takt_time'], row['machine_status'])
        machine_set.addMachine(machine_obj)
    return machine_set

def generate_stock_set(stock_df):
    #stock_df['stock_id'] = 'S' + stock_df['stock_id'].astype(str)
    add_stock_data_to_db(stock_df)
    stockset = StockSet()
    for index, row in stock_df.iterrows():
        stock_obj = Stock(row['stock_id'], row['stock_type'], row['max_level'], 
                          row['current_level'], row['stock_product'])
        stockset.addStock(stock_obj)
    return stockset

def place_performer_transitions(petri_net):
    place_performer = petri_net.place_performer_ids
    in_transition = petri_net.input_transition_place_pairs
    out_transition = petri_net.output_transition_place_pairs
    for item in place_performer:
        place = item['place_label']
        for i in in_transition:
            if place in i['input_place_list']:
                item['output_transition'] = i['transition_label']
                break
        for j in out_transition:
            if place in j['output_place_list']:
                item['input_transition'] = j['transition_label']
                break   
    return pd.DataFrame(place_performer)

def get_petri_net(pnml_file):
    clear_machine_stock_data()
    machine_df = pd.read_excel("Data/machine.xlsx", sheet_name="Sheet1")
    stock_df = pd.read_excel("Data/stock.xlsx", sheet_name="Sheet1")
    machine_set = generate_machine_set(machine_df)
    stock_set = generate_stock_set(stock_df)
    petri_net = get_petri_net_model(pnml_file, machine_set, stock_set)
    place_transition_df = place_performer_transitions(petri_net=petri_net)
    return petri_net, place_transition_df
      
    