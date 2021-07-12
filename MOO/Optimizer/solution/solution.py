#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 08:45:00 2020

@author: chandan
"""

import datetime
import numpy as np
import pandas as pd

from .utility import get_idle_time_for_machine_breakdown
from ..exception import IncompleteSolutionException
from ._schedule_creator import create_schedule_xlsx_file, create_gantt_chart


class OperationHandler:
    def __init__(self, job_id, operation_id, machine, wait, setup, runtime, start_time, buffer_time):
        """    
       constructor of Operation Handler class
        
        Paramters
        --------------------------
        job_id : id of a specific job
        operation_id : id of a operation belongs to job 'job_id'
        machine : machine assigned to process operation 'operation_id'
        wait : wait time for an operation
        setup : setup time for a machine based on operation 'operation_id' (not considered)
        runtime : process time of an operation 'operation_id'
        start_time : process stat time of an operation 'operation_id'
        buffer_time : buffer time for a machine (only for robust pro-active scheduling method)
        
    
        Returns
        ---------------
        result : None
        """  
        

        self.job_id = job_id
        self.operation_id = operation_id
        self.machine = machine
        self.wait = wait
        self.setup = setup
        self.runtime = runtime
        self.buffer_time_start = None
        self.buffer_time_end = None
        
        if buffer_time != 0:
            self.buffer_time_start = start_time
            self.buffer_time_end = start_time +  datetime.timedelta(minutes=buffer_time)
            self.setup_start_time = self.buffer_time_end
        else:
            self.setup_start_time = start_time
            
        self.setup_end_time = self.setup_start_time + datetime.timedelta(minutes=setup)
        self.runtime_end_time = self.setup_end_time + datetime.timedelta(minutes=runtime)

    def __repr__(self):
        return f"job_id={self.job_id}, operation_id={self.operation_id}, machine={self.machine}, " \
               f"wait={self.wait}, setup={self.setup}, runtime={self.runtime}\n"


class Solution:
    def __init__(self, data, operation_2d_array, dict_to_obj=False, makespan=0, 
                 stock_cost=0, machine_makespans=None, tardiness_cost=0, 
                 due_date=None, stability=0, reschedule=None, preschedule_idle=0,
                 job_operation_runtime_matrix=None, operations=None):
        
        """    
       constructor of Solution  class
        
        Paramters
        --------------------------
        data : data object contains information of demand, jobs, machines
        operation_2d_array : 2d array of operations
        dict_to_obj : Flag to convert dictionary -> object
        makespan : makespan cost of solution (schedule)
        stock_cost : stock cost of solution
        machine_makespans : dictionary of machine makespan information
        tardiness_cost : tardiness cost of solution
        due_date : due date dictionary of jobs
        stability : stability cost of solution
        reschedule : reschedule flag 
        preschedule_idle : flag for preschedule_idle flag (robust pro-active schedule)
        job_operation_runtime_matrix : job operation runtime matrix (dataframe)
        operations : list of all operations 
    
        Returns
        ---------------
        result : None
        """  
        
        
        
        if not dict_to_obj:
            if operation_2d_array.shape[0] != data.total_number_of_operations:
                raise IncompleteSolutionException(f"Incomplete Solution of size {operation_2d_array.shape[0]}. "
                                                  f"Should be {data.total_number_of_operations}")
                       
            self.operation_2d_array = operation_2d_array
            self.data = data
            self.job_operation_runtime_matrix = None
            
            self.operations, self.job_operation_runtime_matrix, self.machine_makespans = self.decode_chromosome_representation(preschedule_idle=preschedule_idle)
            
            self.makespan = max(self.machine_makespans)  # calculating makespan cost of the solution
            
            self.stock_cost = self.get_stock_cost()
            self.due_date = self.get_due_date()
            self.tardiness_cost = self.get_tardiness_cost()
            
            
            self.start_datetime = None
            self.stability = 0
            self.initial_schedule_df = None
            
            if reschedule == 1:             
                self.initial_schedule_df = pd.read_hdf('Schedule_output/schedule_df.h5', key='schedule')  # retrieving old schedule information 
                self.stability = self.get_stability_cost()
                
        else:
            self.makespan = makespan
            self.stock_cost = stock_cost
            self.data = data
            self.machine_makespans = machine_makespans
            self.operation_2d_array = operation_2d_array
            self.job_operation_runtime_matrix = job_operation_runtime_matrix
            self.due_date = due_date
            self.tardiness_cost = tardiness_cost
            self.stability = stability
            self.operations = operations
            
        
    def as_dict(self):
        return {'makespan': self.makespan, 'stock_cost': self.stock_cost, 'operation_2d_array': self.operation_2d_array, 
                'machine_makespans': self.machine_makespans, 'data': self.data,
                'due_date':self.due_date, 'tardiness_cost': self.tardiness_cost,
                'stability': self.stability, 'job_operation_runtime_matrix': self.job_operation_runtime_matrix,
                'operations': self.operations}


    def __eq__(self, other_solution):
        return np.array_equal(self.operation_2d_array, other_solution.operation_2d_array)


    def __ne__(self, other_solution):
        return not self == other_solution

    def __lt__(self, other_solution):
        if self.makespan < other_solution.makespan:
            return True
        elif self.makespan > other_solution.makespan:
            return False
        else:
            self_machine_makespans_sorted = sorted(list(self.machine_makespans), reverse=True)
            other_machine_makespans_sorted = sorted(list(other_solution.machine_makespans), reverse=True)
            for i in range(len(self_machine_makespans_sorted)):
                if self_machine_makespans_sorted[i] < other_machine_makespans_sorted[i]:
                    return True
                elif self_machine_makespans_sorted[i] > other_machine_makespans_sorted[i]:
                    return False
        return False


    def __le__(self, other_solution):
        return not self > other_solution

    def __gt__(self, other_solution):
        if self.makespan > other_solution.makespan:
            return True
        elif self.makespan < other_solution.makespan:
            return False
        else:
            self_machine_makespans_sorted = sorted(list(self.machine_makespans), reverse=True)
            other_machine_makespans_sorted = sorted(list(other_solution.machine_makespans), reverse=True)
            for i in range(len(self_machine_makespans_sorted)):
                if self_machine_makespans_sorted[i] > other_machine_makespans_sorted[i]:
                    return True
                elif self_machine_makespans_sorted[i] < other_machine_makespans_sorted[i]:
                    return False
        return False


    def __ge__(self, other_solution):
        return not self < other_solution


    def __str__(self):
        return f"makespan = {self.makespan}\n" \
               f"machine_makespans = {list(self.machine_makespans)}\n" \
               f"operation_list =\n" \
               f"{self.operation_2d_array}\n" \
               f"job_runtime_matrix =\n" \
               f"{ self.job_operation_runtime_matrix}"\
               f"Tradiness cost =\n" \
               f"{ self.tardiness_cost}" \
               f"Due date cost =\n" \
               f"{ self.due_date}" \
               f"Stability cost =\n" \
               f"{ self.stability}" 

    def __getstate__(self):
        self.machine_makespans = np.asarray(self.machine_makespans) 
        return {'operation_2d_array': self.operation_2d_array,
                'machine_makespans': self.machine_makespans,
                'makespan': self.makespan,
                'data': self.data,
                'stock_cost': self.stock_cost,
                'due_date': self.due_date,
                'tardiness_cost': self.tardiness_cost,
                'stability': self.stability,
                'job_operation_runtime_matrix': self.job_operation_runtime_matrix,
                'operations': self.operations}


    def __setstate__(self, state):
        self.operation_2d_array = state['operation_2d_array']
        self.machine_makespans = state['machine_makespans']
        self.makespan = state['makespan']
        self.data = state['data']
        self.stock_cost = state['stock_cost']
        self.tardiness_cost = state['tardiness_cost']
        self.due_date = state['due_date']
        self.stability = state['stability']
        self.job_operation_runtime_matrix = state['job_operation_runtime_matrix']
        self.operations = state['operations']




    def decode_chromosome_representation(self, start_date=datetime.date.today(), start_time=datetime.time(hour=datetime.datetime.now().hour, minute=(datetime.datetime.now().minute + 2)%60),
                                       end_time=datetime.time(hour=18,  minute=00), continuous=False, machines=None,
                                       preschedule_idle=0):
       
        """    
        Used to decode the chromosome representation into time-framed schedule
        
        Paramters
        --------------------------
        self :  class instance
        start_date : starting date
        start_time : starting time of the schedule  (not 0 as mentioned in the algorithm, but actual time 'hh:mm:ss')
        end_time : end time of the schedule for the current day (mainly for production not as completion time of the whole schedule)
        continuous : flag which defines whether schedule is continuous or shift basis
        machines : list of machines
        preschedule_idle : flag to introduce buffer time (robust pro-active schedule)
        
    
        Returns
        ---------------
        result : decoded operations data
        job_operation_runtime_matrix : dataframe of job operation runtime matrix
        machine_makespans_memory : dictionary of machine makespan data
        """  
        
        result = []
        job_operation_runtime_matrix = list()
        num_jobs = self.data.total_number_of_jobs
        num_machines = self.data.total_number_of_machines
        
        self.start_datetime = datetime.datetime(year=start_date.year, month=start_date.month, day=start_date.day,
                                           hour=start_time.hour, minute=start_time.minute, second=start_time.second)
        
        machine_datetime_dict = {machine_id: self.start_datetime for machine_id in range(num_machines)} # machine makespan data in date time format
        machine_makespan_memory = [0] * num_machines
        last_repair_time = [0] * num_machines
        no_idle_time_introduced = [0] * num_machines
        job_seq_memory = [0] * num_jobs
        prev_job_seq_end_memory = [0] * num_jobs
        job_end_memory = [0] * num_jobs
        
        
        for row in range(self.operation_2d_array.shape[0]):
            job_id = self.operation_2d_array[row, 0]
            operation_id = self.operation_2d_array[row, 1]
            sequence = self.operation_2d_array[row, 2] # for ease of coding operation sequence is included
            machine = self.operation_2d_array[row, 3]
            buffer_time = 0
            
            if preschedule_idle: # when robust pro-active reschedule method is enabled
                buffer_time, last_repair_time[machine], no_idle_time_introduced[machine] = get_idle_time_for_machine_breakdown(self.data.machine_threshold_list,
                                             self.data.machine_avg_process_list,
                                             self.data.machine_repair_duration_list,
                                             machine,
                                             machine_makespan_memory[machine],
                                             last_repair_time[machine], 
                                             no_idle_time_introduced[machine])
            
            setup = 0
            if job_seq_memory[job_id] < sequence:
                prev_job_seq_end_memory[job_id] = job_end_memory[job_id]

            
            if prev_job_seq_end_memory[job_id] <= machine_makespan_memory[machine]: # if completion time of previous operation of the job 'job_id' is less than machine makespan
                wait = 0
            else:
                wait = prev_job_seq_end_memory[job_id] - machine_makespan_memory[machine]

            runtime = self.data.get_runtime(job_id, operation_id, machine) #process time of operation
            tmp_dt = machine_datetime_dict[machine] + datetime.timedelta(minutes=buffer_time + setup + runtime)
            
            if not continuous and (tmp_dt.time() > end_time or tmp_dt.day != machine_datetime_dict[machine].day): # for sift basis schedule
                machine_datetime_dict[machine] += datetime.timedelta(days=1)
                machine_datetime_dict[machine].replace(hour=start_time.hour, minute=start_time.minute,
                                                       second=start_time.second)
            else:
                machine_datetime_dict[machine] += datetime.timedelta(minutes=wait)

            
            if runtime == 0:
                setup = 0
                buffer_time = 0

            operation_data = OperationHandler(job_id,
                                    operation_id,
                                    machine,
                                    float(wait),
                                    float(setup),
                                    float(runtime),
                                    machine_datetime_dict[machine],
                                    buffer_time)
            
            result.append(operation_data) 
            
            job_runtime_matrix = dict()
            job_runtime_matrix['job_id'] = operation_data.job_id
            job_runtime_matrix['operation_id'] = operation_data.operation_id
            job_runtime_matrix['start_time'] = operation_data.setup_start_time
            job_runtime_matrix['end_time'] = operation_data.runtime_end_time    
            job_runtime_matrix['buffer_time'] = buffer_time
            job_operation_runtime_matrix.append(job_runtime_matrix)                

           # machine_makespan_memory[machine] += runtime + wait + setup 

            machine_makespan_memory[machine] += runtime + wait + setup + buffer_time
            job_end_memory[job_id] = machine_makespan_memory[machine]
            job_seq_memory[job_id] = sequence
            
        return result, pd.DataFrame(job_operation_runtime_matrix), machine_makespan_memory


        
    def get_stock_cost(self):
        """    
        Evaluates stock cost of the solution
        
        Paramters
        --------------------------
        self :  class instance
    
        Returns
        ---------------
        stock_cost : calculated stock cost
        """  
        
        
        number_of_jobs = self.data.total_number_of_jobs        
        stock_cost = 0
        
        for i in range(number_of_jobs):
            job_df = self.job_operation_runtime_matrix.loc[self.job_operation_runtime_matrix['job_id'] == i]
            tot_operations = job_df.shape[0]
            
            for j in range(tot_operations - 1):
                operation_a = job_df.loc[(job_df['job_id']==i) & (job_df['operation_id']==j)]
                operation_b = job_df.loc[(job_df['job_id']==i) & (job_df['operation_id']==j+1)]  
                operation_b_start_time = operation_b.iloc[0]['start_time']
                operation_a_end_time = operation_a.iloc[0]['end_time']
                stock_cost += (operation_b_start_time - operation_a_end_time).total_seconds() 
                
        if stock_cost == 0:
            return stock_cost
        return stock_cost/60 # stock cost from seconds -> minutes
    
    
    def get_due_date(self):
        
         """    
        Evaluates due date for each job in the solution
        
        Paramters
        --------------------------
        self :  class instance
    
        Returns
        ---------------
        job_due_date_dict : dictionary that contains due date value of each job
        """  
        
         operation_processing_matrix = [list(j) for j in self.data.operation_processing_times_matrix]
         job_due_date_matrix = dict()
         count = 0
         for job_index in self.data.job_operation_index_matrix:
             total_time = 0
             for operation_index in job_index:
                 if operation_index != -1:
                     processing_time = operation_processing_matrix[operation_index] 
                     total_time += processing_time
             job_due_date_matrix[count] = total_time 
             count +=1   
         return job_due_date_matrix
     
        
    def get_tardiness_cost(self):
        
         """    
        Evaluates tardiness cost of the solution
        
        Paramters
        --------------------------
        self :  class instance
    
        Returns
        ---------------
        tardiness_cost : tardiness cost of the solution
        """  
        
         tardiness_cost = 0         
         number_of_jobs = self.data.total_number_of_jobs
         for i in range(number_of_jobs):
            job_df = self.job_operation_runtime_matrix.loc[self.job_operation_runtime_matrix['job_id'] == i]
            tot_operations = job_df.shape[0]
            final_op = job_df.loc[(job_df['job_id']==i) & (job_df['operation_id']==tot_operations-1)]   # last operation of job (final completion time)
            final_op.reset_index(drop=True, inplace=True)
            cost = ((final_op.end_time - self.start_datetime).dt.total_seconds())[0]  # start_datetime is subtracted because  starttime is not 0  whereas specific time like (9 am)
            
            cost = (cost/60) - self.due_date[i]
            tardiness_cost += cost 
         return tardiness_cost
    
    
    
    def get_stability_cost(self):    
        
        """    
        Evaluates stability cost of the solution
        
        Paramters
        --------------------------
        self :  class instance
    
        Returns
        ---------------
        stability_cost : stability cost of the solution
        """  
        early_start_deviation = 0
        late_start_deviation = 0
        machine_change_cost = 0
        completion_time_deviation_cost = 0
        strftime = "%Y-%m-%d %H:%M:%S"
        
        for operation in self.operations:
            job_id = operation.job_id 
            operation_id = operation.operation_id
            machine = operation.machine
            runtime = operation.runtime
            operation_start_time = operation.setup_start_time
            operation_end_time = operation.runtime_end_time
            
            if runtime != 0: # only unprcessed operations are considered
                init_operation_data = self.initial_schedule_df.loc[(self.initial_schedule_df.job == job_id) & (self.initial_schedule_df.operation == operation_id)] # select operation 'operation_id' from previous schedule
                
                if not init_operation_data.empty:
                    i_start_time = datetime.datetime.strptime(init_operation_data.iloc[0]['setup_start'], strftime)
                    i_completion_time = datetime.datetime.strptime(init_operation_data.iloc[0]['runtime_end'], strftime)
                    start_time_deviation = (operation_start_time - i_start_time).total_seconds()
                    if start_time_deviation < 0:
                        early_start_deviation += (abs(start_time_deviation)/60)
                    else:
                        late_start_deviation += (start_time_deviation/60)
                    
                    completion_time_deviation_cost += abs((operation_end_time - i_completion_time).total_seconds())
                    
                    if init_operation_data.iloc[0]['machine'] != machine:
                        machine_change_cost += 100
        
        '''More penalty for ealry start -> where complexity will be high, and also for change of machine'''
        stability_cost = 0.3 * early_start_deviation + 0.15 * late_start_deviation + 0.4 * machine_change_cost + 0.15 * completion_time_deviation_cost       
        return stability_cost
    
    
    
    
    def create_schedule_xlsx_file(self, output_path, job_mapping, start_date=datetime.date.today(),
                                  start_time=datetime.time(hour=datetime.datetime.now().hour, minute=(datetime.datetime.now().minute + 2)%60),
                                  end_time=datetime.time(hour=20, minute=0), continuous=False, schedule_type=None,
                                  preschedule_idle=False):
        """    
        Used to create schedule in xlsx format        
        """  
        return create_schedule_xlsx_file(self, output_path, job_mapping, start_date=start_date, 
                                         start_time=start_time, end_time=end_time, continuous=continuous,
                                         schedule_type=schedule_type, preschedule_idle=preschedule_idle)
        
        
        

    def iplot_gantt_chart(self, title='Gantt Chart', start_date=datetime.date.today(),
                          start_time=datetime.time(hour=8, minute=0), end_time=datetime.time(hour=20, minute=0),
                          continuous=False):
        """    
        Used to plot Gannt chart        
        """          
        create_gantt_chart(self, "", title=title, start_date=start_date, start_time=start_time,
                           end_time=end_time, iplot_bool=True, continuous=continuous)
        
        
        

    def create_gantt_chart_html_file(self, output_path, title='Gantt Chart', start_date=datetime.date.today(),
                                     start_time=datetime.time(hour=datetime.datetime.now().hour, minute=(datetime.datetime.now().minute + 2)%60),
                                     end_time=datetime.time(hour=20, minute=0), auto_open=False, continuous=False,
                                     preschedule_idle=False):
        """    
        Used to create Gannt chart in HTML format        
        """  
        create_gantt_chart(self, output_path, title=title, start_date=start_date, start_time=start_time,
                           end_time=end_time, iplot_bool=False, auto_open=auto_open,
                           continuous=continuous, preschedule_idle=preschedule_idle)