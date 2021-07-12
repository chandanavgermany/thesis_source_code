# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 08:48:48 2021

@author: Q514347
"""
import pandas as pd
import random
from .utility import get_present_schedule, get_unprocessed_schedule

class RightShiftRescheduling:
    def __init__(self, schedule, halt_duration):
        #halt_duration - in minutes
        self.schedule = schedule
        self.halt_duration = halt_duration
        self.process_log = get_present_schedule()
        
    def reschedule(self):
        unprocessed_schedule = get_unprocessed_schedule(self.schedule, self.process_log)
        unprocessed_schedule = unprocessed_schedule.loc[unprocessed_schedule['remaining_pieces'] != 0]
        time_shift_columns = ['setup_start', 'setup_end', 
                              'runtime_start', 'runtime_end']
       # buffer = random.randint(1, 5)
        for column in time_shift_columns:
            unprocessed_schedule[column] = unprocessed_schedule[column].astype('datetime64[ns]')
            unprocessed_schedule[column] += pd.to_timedelta(self.halt_duration, unit='m')
            
        return unprocessed_schedule