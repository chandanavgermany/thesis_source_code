# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 10:11:38 2021

@author: q514347
"""
import os
import time
import pandas as pd
import multiprocessing as mp

from sqlalchemy import create_engine
from args import get_args
from datetime import datetime
from nsga_2 import nsga
from algorithms import main
from simulation_utility import *
from net_generation import get_petri_net
from scheduler_date_time_based import Schedule
from Rescheduling.partial_rescheduling import PartialRescheduling
from Rescheduling.complete_rescheduling import CompleteRescheduling
from Rescheduling.right_shift_scheduling import RightShiftRescheduling

engine = create_engine('postgresql://postgres:popup123@localhost:5432/petri_net')


def run_process(schedule, place_transition_df):
    """
    function to start the production based on given schedule by creating process for each job
    
    Parameters
    -----------------------
    schedule : dataframe of schedule
    place_transition_df : encoded place transition df from Petri net model

    Returns
    ----------------
    Flag to notify whether process interrupted or succefully finished
    
    """
    
    path = get_path_for_each_product(schedule, place_transition_df)
    product_names = list(schedule['prod_name'].unique())
    schedule_agent_list = []
    for product in product_names:
        individual_prod_schedule = schedule.loc[schedule['prod_name'] == product]
        if not individual_prod_schedule.empty:
            schedule_agent_list.append(Schedule(petri_net, individual_prod_schedule, path[product], product, job=individual_prod_schedule.iloc[0]['job']))        
    process_interruption_event = mp.Event()
    child_results_queue = mp.Queue()
    process = [mp.Process(target=agent.start, args=[process_interruption_event, child_results_queue]) for agent in schedule_agent_list]

    ############################################# Schedule Start  ###########################################
    for p in process:
        p.start()
        print("Child process started with process id = " + str(p.pid))
        
    for p in process:
        p.join()
    
    if process_interruption_event.wait():
        print('Execution stopped')  
        if is_process_finished():
            return False
        else:
            return True


if __name__ == "__main__":   
    
    """
    Main block of execution
    """
    
    # delte existing production status logs from database
    delete_production_status()
    
    ############### Get args######################
    args = get_args() # get predefined arguments
    
    
    # Petri Net model creation
    petri_net, place_transition_df = get_petri_net(args.petri_net_file) 
   
    # Objective function parameters
    objective_params = {'makespan': 0.6, 'stock_cost': 0.2, 'tardiness_cost': 0.2, 'stability': 0}
    machine_df = pd.read_excel(args.machine_info_file_name, sheet_name='Sheet1')
    job_operation_df = pd.read_excel(args.job_operation_info_file_name, sheet_name='Sheet1')
    
    # Get optimized solution
    if args.alg == 'hybrid':
        schedule, best_solution = main(machine_df, job_operation_df, objective_params, preschedule_idle=False) 
        if args.schedule_type != 'normal':
            schedule_i = schedule.copy()
            schedule, t = main(machine_df, job_operation_df, objective_params, preschedule_idle=True)
    else:
        schedule, best_solution = nsga(machine_df, job_operation_df, 
                                       objective_params, preschedule_idle=False)     
        if args.schedule_type != 'normal':
            schedule_i = schedule.copy()
            schedule, t = nsga(machine_df, job_operation_df, objective_params, preschedule_idle=True)




    schedule.runtime_duration = schedule.runtime_duration.dt.total_seconds().round()
    demand = job_operation_df.copy()
    demand.drop(['required_machines', 'sequence'], axis=1, inplace=True)
    schedule = pd.merge(schedule, machine_df, left_on=['machine'], right_on=['machine_id'], how='inner')
    schedule = pd.merge(schedule, demand, left_on=['prod_name', 'operation', 'job'], right_on=['prod_name', 'operation', 'job'], how='inner')
    schedule = schedule.sort_values(by=['prod_name','operation'])
    schedule['machine_name'] = 'M' + schedule['machine'].astype(str)
    schedule['finished_pieces'] = 0
    schedule['remaining_pieces'] = schedule['pieces']
    
    schedule_log = schedule[['prod_name', 'operation', 'pieces', 'finished_pieces', 'remaining_pieces']]
    schedule_log.index.names = ['id']
    schedule_log.to_sql('temp_schedule_log', engine, if_exists='append')        
    
    initial_schedule = schedule.copy()
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    

    ############################## Main process execution block ############################################
    while True:
        if run_process(schedule, place_transition_df):
            print('Process Terminated !!')
            print('Rescheduling ......')
            delete_production_status()
            reset_machine_status()
            time.sleep(5)
            if args.reschedule_method == 'right_shift':
                new_schedule = RightShiftRescheduling(schedule, 3).reschedule()
            elif args.reschedule_method == 'partial':
                new_schedule = PartialRescheduling(initial_schedule, 'MB', args=args).reschedule()
            else:
                new_schedule = CompleteRescheduling(initial_schedule, 'MB', objective_params=objective_params, args=args).reschedule()
            schedule = new_schedule
            print(new_schedule['setup_start'])
        else:
            break
    
    old_schedule = initial_schedule.copy()
    if args.schedule_type != 'normal':
        old_schedule = schedule_i.copy()
        
        
    # Production cost and stability estimation   
    calculate_dependent_values(start_time, best_solution, old_schedule)
    os.system("pause")