# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 10:37:07 2021

@author: Q514347
"""
import pandas as pd
from nsga_2 import nsga
from algorithms import main
from .utility import get_present_schedule, get_machine_data, get_unprocessed_schedule, get_initial_job_operation_sequence_matrix

class CompleteRescheduling:
    def __init__(self, schedule, disruption_event_type, broken_machine=None, objective_params=None, args=None):
        self.schedule = schedule
        self.disruption_event_type = disruption_event_type
        self.broken_machine = broken_machine
        self.process_log = get_present_schedule()
        self.objective_params = objective_params
        self.args = args
        
    def reschedule(self):
        machine_df = get_machine_data()
        machine_df['machine_id'] = machine_df['machine_id'].replace({'M':''}, regex=True)
        machine_df['machine_id'] = machine_df['machine_id'].astype(int)
        unprocessed_job_operation_df = get_unprocessed_schedule(self.schedule, self.process_log)
        initial_job_operation_df = get_initial_job_operation_sequence_matrix()
        
        unprocessed_job_operation_df = pd.merge(unprocessed_job_operation_df, 
                                                initial_job_operation_df,
                                                how='inner',
                                                on=['prod_name', 'operation', 'job'])
        
        unprocessed_job_operation_df['pieces'] = unprocessed_job_operation_df['remaining_pieces']           
        unprocessed_job_operation_df = unprocessed_job_operation_df.sort_values(by=['prod_name', 'operation'])
        unprocessed_job_operation_df = unprocessed_job_operation_df.drop(['machine', 'setup_start', 'setup_end',
                                                                          'runtime_start', 'runtime_end', 
                                                                          'machine_name','runtime_duration'],
                                                                            axis=1)
        if self.args.alg == 'hybrid':
            new_schedule, best_solution = main(machine_df, unprocessed_job_operation_df, self.objective_params, reschedule=True)
        else:
            new_schedule, best_solution = nsga(machine_df, unprocessed_job_operation_df, self.objective_params, reschedule=True)

        new_schedule = pd.merge(unprocessed_job_operation_df, 
                                                new_schedule,
                                                how='inner',
                                                on=['prod_name', 'operation', 'job'])
        new_schedule = new_schedule.loc[new_schedule['remaining_pieces'] != 0]
        new_schedule.runtime_duration = new_schedule.runtime_duration.dt.total_seconds().round()
        new_schedule['machine_name'] = 'M' + new_schedule['machine'].astype(str)
        return new_schedule