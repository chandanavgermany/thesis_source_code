# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 10:34:05 2021

@author: Q514347
"""
import time
import json
import pandas as pd
import http.client as client
from sqlalchemy import create_engine
from datetime import datetime

engine = create_engine('postgresql://postgres:popup123@localhost:5432/petri_net')

def machine_status(machine_id, status):
    data = {'machine': machine_id, 'status': status}
    c = client.HTTPConnection('localhost', 8080)
    c.request('POST', '/set_machine_status', json.dumps(data))
    print(c.getresponse().read())
    c.close()
    
def production_status(status):
    data = {'production_status': status}
    c = client.HTTPConnection('localhost', 8080)
    c.request('POST', '/set_production_status', json.dumps(data))
    print(c.getresponse().read())
    c.close()

def delete_production_status():
    c = client.HTTPConnection('localhost', 8080)
    c.request('POST', '/delete_production_status')
    print(c.getresponse().read())
    c.close()

def get_product_stock_info(transition_label, place_transition_df, product_name, transition_name):
     path_info = place_transition_df.loc[place_transition_df[transition_name] == transition_label]     
     for index, row in path_info.iterrows():             
         performer_id = row['performer_id']
         if product_name in performer_id:
             print(performer_id)
             return ('place', row['place_label'], performer_id)
     return None

def reset_machine_status():
    machine_df = pd.read_sql('Select * from machine_info', con=engine)
    c = client.HTTPConnection('localhost', 8080)
    c.request('POST', '/clear_machine_data')
    print(c.getresponse().read())
    c.close()
    time.sleep(5)
    machine_df['machine_status'] = machine_df['machine_status'].replace('busy', 'available')
    machine_df.drop(['unique_id'], inplace=True, axis=1)
    machine_df = machine_df.set_index('machine_id')
    machine_df.to_sql('machine_info', engine, if_exists='append')
    
def get_path_for_each_product(schedule, place_transition_df):
    path = dict()
    product_name_list = list(schedule['prod_name'].unique())
    for product in product_name_list:
        path[product] = list()
        individual_prod_schedule = schedule.loc[schedule['prod_name'] == product]
        for index, row in individual_prod_schedule.iterrows():
            path_info = place_transition_df.loc[place_transition_df['performer_id'] == row['machine_name']]
            input_transition = path_info.iloc[0]['input_transition']
            data = get_product_stock_info(input_transition, place_transition_df, product, 'output_transition')
            
            if data is not None and data not in path[product]:
                path[product].append(data)
                
            path[product].append(('transition', input_transition, input_transition))
            path[product].append(('place', path_info.iloc[0]['place_label'], row['machine_name']))
            output_transition = path_info.iloc[0]['output_transition']
            path[product].append(('transition', output_transition, output_transition))
            data = get_product_stock_info(output_transition, place_transition_df, product, 'input_transition')
            
            if data is not None and data not in path[product]:
                path[product].append(data)
    return path

def update_result(makespan, tardiness_cost, stock_cost, stability, schedule_type='initial'):
    result = dict()
    result['makespan'] = makespan
    result['stock_cost'] = stock_cost
    result['tardiness_cost'] = tardiness_cost
    result['stability'] = 0
    result['schedule_type'] = schedule_type
    if stability != 0:
        result['stability'] = 1/stability
    result_df = pd.DataFrame([result])
    result_df.set_index('makespan', inplace=True, drop=True)
    result_df.to_sql('result_log', engine, if_exists='append')
    
def is_process_finished():
    df = pd.read_sql('Select * from temp_schedule_log where remaining_pieces != 0', con=engine)
    if df.empty:
        return True
    return False

def is_production_status_changed():
    df = pd.read_sql('Select * from production_status_value', con=engine)
    if not df.empty:
        status = df.iloc[0]['production_status']
        if status == 'broken' or status == 'repaired':
            return True
    return False
    
def get_final_makespan_cost(start_time):
    makespan = 0
    process_log = pd.read_sql("Select * from product_performance_log where place_type='stock' order by id DESC limit 1", con=engine)
    if not process_log.empty:
        start_time =  datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(process_log.iloc[-1]['left_at'], '%Y-%m-%d %H:%M:%S')
        makespan = (end_time-start_time).total_seconds()
    return makespan/60
        
def get_final_stock_cost():
    process_log = pd.read_sql("Select * from product_performance_log where place_type='stock' order by id", con=engine)
    stock_places = list(process_log['operation_place'].unique())
    stock_cost = 0
    for place in stock_places:
        place_df = process_log.loc[process_log['operation_place'] == place]
        start_time = datetime.strptime(place_df.iloc[0]['started_at'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(place_df.iloc[-1]['left_at'], '%Y-%m-%d %H:%M:%S')
        print(end_time - start_time)
        stock_cost += (end_time - start_time).total_seconds()
    if stock_cost == 0:
        return stock_cost
    return stock_cost/60

def get_final_stock_cost_t():
    process_log = pd.read_sql("Select * from product_performance_log where place_type='stock' order by id", con=engine)
    stock_cost = 0
    for i, row in process_log.iterrows():
        start_time = datetime.strptime(row['started_at'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(row['left_at'], '%Y-%m-%d %H:%M:%S')
        print(end_time - start_time)
        stock_cost += (end_time - start_time).total_seconds()
    if stock_cost == 0:
        return stock_cost
    return stock_cost/60

def get_final_tardiness_cost(old_solution, old_schedule, start_time_var):
    process_log = pd.read_sql("Select * from product_performance_log where place_type !='stock'", con=engine)
    tardiness_cost = 0
    jobs = list(old_schedule['job'].unique())
    for job in jobs:
        job_df = old_schedule.loc[old_schedule['job'] == job]
        tot_operations = job_df.shape[0]
        last_operation_df = process_log.loc[(process_log['job'] == job) & (process_log['operation'] == (tot_operations -1))]
        if not last_operation_df.empty:
            start_time =  datetime.strptime(start_time_var, '%Y-%m-%d %H:%M:%S') 
            end_time = datetime.strptime(last_operation_df.iloc[-1]['left_at'], '%Y-%m-%d %H:%M:%S')
            cost =(end_time - start_time).total_seconds()
            cost = (float(cost)/60) - old_solution.due_date[job]            
            tardiness_cost += cost
    return tardiness_cost

def get_final_stability(old_solution, old_schedule):
    process_log = pd.read_sql("Select * from product_performance_log where place_type !='stock'", con=engine)
    early_start_deviation = 0
    late_start_deviation = 0
    machine_change_cost = 0
    completion_time_deviation_cost = 0
    strftime = "%Y-%m-%d %H:%M:%S"
    jobs = list(old_schedule['job'].unique())
    
    for job in jobs:
        job_df = old_schedule.loc[old_schedule['job'] == job]
        tot_operations = job_df.shape[0]
        for i in range(tot_operations):
            operation_old_schedule_df = job_df.loc[job_df['operation'] == i]
            operation_processed_df = process_log.loc[(process_log['job'] == job) & (process_log['operation'] == i)]
            if not operation_processed_df.empty:
                start_time_old_operation = datetime.strptime(operation_old_schedule_df.iloc[0]['setup_start'], strftime)
                completion_time_old_operation = datetime.strptime(operation_old_schedule_df.iloc[0]['runtime_end'], strftime)        
                start_time_processed = datetime.strptime(operation_processed_df.iloc[0]['started_at'], strftime)
                completion_time_processed = datetime.strptime(operation_processed_df.iloc[-1]['left_at'], strftime)        
                start_time_deviation = (start_time_processed - start_time_old_operation).total_seconds()
        
                if start_time_deviation < 0:
                    early_start_deviation += (abs(start_time_deviation)/60)
                else:
                    late_start_deviation += (start_time_deviation/60)            
                completion_time_deviation_cost += abs((completion_time_processed - completion_time_old_operation).total_seconds())
                
                machine_old_operation = operation_old_schedule_df.iloc[0]['machine']
                machine_new_operation = operation_processed_df.iloc[-1]['machine']
                
                if machine_old_operation != machine_new_operation:
                    machine_change_cost += 100
           
    '''More penalty for ealry start - where complexity will be high, and also if change of machine'''
    stability_cost = 0.3 * early_start_deviation + 0.15 * late_start_deviation + 0.4 * machine_change_cost + 0.15 * completion_time_deviation_cost       
    if stability_cost != 0:
        stability_cost = 1/stability_cost
    return stability_cost


def get_percentage_change_in_param(param_old, param_new):
    return ((param_new-param_old)/param_old)*100

def calculate_dependent_values(start_time, old_solution, old_schedule):
    print('Initial solution Stability: ', 1)
    print('Final production Stability: ', get_final_stability(old_solution, old_schedule))
    
    initial_time = start_time
    final_makespan_cost = get_final_makespan_cost(start_time)
    final_stock_cost = get_final_stock_cost_t()
    final_tardiness_cost = get_final_tardiness_cost(old_solution, old_schedule, initial_time)
    
    print('Final Makespan cost: ', final_makespan_cost)
    print('Final Stock cost: ', final_stock_cost)
    print('Final Tardiness cost: ', final_tardiness_cost)
    
    print('-----------------% change in objective parameters--------------------')
    print('Makespan change: ', get_percentage_change_in_param(old_solution.makespan, final_makespan_cost))
    print('Stock cost change: ', get_percentage_change_in_param(old_solution.stock_cost, final_stock_cost))
    print('Tardiness cost change: ', get_percentage_change_in_param(old_solution.tardiness_cost, final_tardiness_cost))
    
    print('----------------- Overall Production Cost ---------------------------')
    print(final_stock_cost + final_tardiness_cost)