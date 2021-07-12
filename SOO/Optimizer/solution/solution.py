#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 08:45:00 2020

@author: chandan
"""


import datetime
import numpy as np


from ..exception import IncompleteSolutionException
from ._schedule_creator import create_schedule_xlsx_file, create_gantt_chart
#from ._makespan import compute_machine_makespans


class OperationHandler:
    def __init__(self, job_id, operation_id, machine, wait, setup, runtime, start_time):
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
        self.setup_start_time = start_time
        self.setup_end_time = self.setup_start_time + datetime.timedelta(minutes=setup)
        self.runtime_end_time = self.setup_end_time + datetime.timedelta(minutes=runtime)

    def __repr__(self):
        return f"job_id={self.job_id}, operation_id={self.operation_id}, machine={self.machine}, " \
               f"wait={self.wait}, setup={self.setup}, runtime={self.runtime}\n"


class Solution:
    def __init__(self, data, operation_2d_array):
        """    
       constructor of Solution  class
        
        Paramters
        --------------------------
        data : data object contains information of demand, jobs, machines
        operation_2d_array : 2d array of operations

    
        Returns
        ---------------
        result : None
        """  

        if operation_2d_array.shape[0] != data.total_number_of_operations:
            raise IncompleteSolutionException(f"Incomplete Solution of size {operation_2d_array.shape[0]}. "
                                              f"Should be {data.total_number_of_operations}")
       
# =============================================================================
#         self.machine_makespans = compute_machine_makespans(operation_2d_array,
#                                                            data.operation_processing_times_matrix,
#                                                            data.sequence_dependency_matrix,
#                                                            data.job_operation_index_matrix,
#                                                            data.machine_setup_time_matrix)
# =============================================================================
        self.operation_2d_array = operation_2d_array
        self.data = data
        _, self.machine_makespans = self.decode_chromosome_representation()
        self.makespan = max(self.machine_makespans)
        

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
               f"{self.operation_2d_array}"


    def __getstate__(self):
        self.machine_makespans = np.asarray(self.machine_makespans) 
        return {'operation_2d_array': self.operation_2d_array,
                'machine_makespans': self.machine_makespans,
                'makespan': self.makespan,
                'data': self.data}


    def __setstate__(self, state):
        self.operation_2d_array = state['operation_2d_array']
        self.machine_makespans = state['machine_makespans']
        self.makespan = state['makespan']
        self.data = state['data']

  

    def decode_chromosome_representation(self, start_date=datetime.date.today(), start_time=datetime.time(hour=8),
                                       end_time=datetime.time(hour=20), continuous=False, machines=None):
        
       
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
        
    
        Returns
        ---------------
        result : decoded operations data
        machine_makespans_memory : dictionary of machine makespan data
        """  
        

        result = []
        num_jobs = self.data.total_number_of_jobs
        num_machines = self.data.total_number_of_machines
        start_datetime = datetime.datetime(year=start_date.year, month=start_date.month, day=start_date.day,
                                           hour=start_time.hour, minute=start_time.minute, second=start_time.second)
        machine_datetime_dict = {machine_id: start_datetime for machine_id in range(num_machines)}

        machine_makespan_memory = [0] * num_machines # initial machine  makespan set to 0
        job_seq_memory = [0] * num_jobs
        prev_job_seq_end_memory = [0] * num_jobs
        job_end_memory = [0] * num_jobs

        for row in range(self.operation_2d_array.shape[0]):
            job_id = self.operation_2d_array[row, 0]
            operation_id = self.operation_2d_array[row, 1]
            sequence = self.operation_2d_array[row, 2] # for ease of coding operation sequence is included
            machine = self.operation_2d_array[row, 3]

            setup =  0

            if job_seq_memory[job_id] < sequence:
                prev_job_seq_end_memory[job_id] = job_end_memory[job_id]

            if prev_job_seq_end_memory[job_id] <= machine_makespan_memory[machine]:  # if completion time of previous operation of the job 'job_id' is less than machine makespan
                wait = 0
            else:
                wait = prev_job_seq_end_memory[job_id] - machine_makespan_memory[machine]

            runtime = self.data.get_runtime(job_id, operation_id, machine)  #process time of operation

            tmp_dt = machine_datetime_dict[machine] + datetime.timedelta(minutes=wait)
            if not continuous and (tmp_dt.time() > end_time or tmp_dt.day != machine_datetime_dict[machine].day):
                machine_datetime_dict[machine] += datetime.timedelta(days=1)
                machine_datetime_dict[machine].replace(hour=start_time.hour, minute=start_time.minute,
                                                       second=start_time.second)
            else:
                machine_datetime_dict[machine] += datetime.timedelta(minutes=wait)


            result.append(OperationHandler(job_id,
                                        operation_id,
                                        machine,
                                        float(wait),
                                        float(setup),
                                        float(runtime),
                                        machine_datetime_dict[machine])) 


            machine_makespan_memory[machine] += runtime + wait + setup 
            
            job_end_memory[job_id] = machine_makespan_memory[machine]
            job_seq_memory[job_id] = sequence

        return result, machine_makespan_memory
    


    def create_schedule_xlsx_file(self, output_path, start_date=datetime.date.today(), start_time=datetime.time(hour=8, minute=0),
                                  end_time=datetime.time(hour=20, minute=0), continuous=False):
        """    
        Used to create schedule in xlsx format        
        """  
        create_schedule_xlsx_file(self, output_path, start_date=start_date, start_time=start_time, end_time=end_time, continuous=continuous)



    def iplot_gantt_chart(self, title='Gantt Chart', start_date=datetime.date.today(),
                          start_time=datetime.time(hour=8, minute=0), end_time=datetime.time(hour=20, minute=0),
                          continuous=False):
        """    
        Used to plot Gannt chart        
        """ 
        create_gantt_chart(self, "", title=title, start_date=start_date, start_time=start_time,
                           end_time=end_time, iplot_bool=True, continuous=continuous)



    def create_gantt_chart_html_file(self, output_path, title='Gantt Chart', start_date=datetime.date.today(),
                                     start_time=datetime.time(hour=8, minute=0),
                                     end_time=datetime.time(hour=20, minute=0), auto_open=False, continuous=False):
        
        """    
        Used to create Gannt chart in HTML format        
        """  
        create_gantt_chart(self, output_path, title=title, start_date=start_date, start_time=start_time,
                           end_time=end_time, iplot_bool=False, auto_open=auto_open,
                           continuous=continuous)