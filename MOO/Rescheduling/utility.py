# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 08:57:47 2021

@author: Q514347
"""

import pandas as pd
from sqlalchemy import create_engine
from args import get_args
args = get_args()

engine = create_engine('postgresql://postgres:popup123@localhost:5432/petri_net')

def get_present_schedule():
    return pd.read_sql("Select * from temp_schedule_log", con=engine)    

def get_unprocessed_schedule(initial_schedule, processed_schedule):
    initial_schedule = initial_schedule.drop(['remaining_pieces', 'finished_pieces', 'pieces'], axis=1)
    unprocessed_schedule = pd.merge(initial_schedule, processed_schedule, how='inner',
                                    on=['prod_name', 'operation'], suffixes=('', '_y'))
    #unprocessed_schedule = unprocessed_schedule.loc[unprocessed_schedule['remaining_pieces'] != 0]
    return unprocessed_schedule

def get_machine_data():
    return pd.read_sql('Select * from machine_info', con=engine)

def get_initial_job_operation_sequence_matrix():
    job_operation_df = pd.read_excel(args.job_operation_info_file_name, sheet_name='Sheet1')
    job_operation_df = job_operation_df.drop(['pieces'], axis=1)
    return job_operation_df

