#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 20:39:01 2020

@author: chandan
"""
import re
import numpy as np
from pathlib import Path

from .data import Data
from .job import Job
from .operation import Operation

class Data_Normal_Job_Shop(Data):
    
    def __init__(self, input_file):
        """
        Constructor for Data_Normal_Job_Shop
        
        Parameter
        --------------------------------------------

        input_file : benchmark problem data file     
        
        Returns
        ------------------------------
        None        
        
        """
        
        super().__init__()
        self.fjs_file_path = Path(input_file)
        
        with open(self.fjs_file_path, 'r') as fin:

            lines = [line for line in [l.strip() for l in fin] if line]  
            first_line = [int(s) for s in re.sub(r'\s+', ' ', lines[0].strip()).split(' ')[:-1]]
            self.total_number_of_jobs = first_line[0]  
            self.total_number_of_machines = first_line[1]  

            self.total_number_of_operations = 0
            self.max_operations_for_a_job = 0
            
            for line in lines[1:]:  
                line = [int(s) for s in re.sub(r'\s+', ' ', line.strip()).split(' ')]

                num_operations = int(line[0])
                self.total_number_of_operations += num_operations
                self.max_operations_for_a_job = max(num_operations, self.max_operations_for_a_job)

            self.operation_processing_times_matrix = np.full((self.total_number_of_operations, self.total_number_of_machines), -1,
                                                        dtype=np.float)
            self.sequence_dependency_matrix = np.zeros((self.total_number_of_operations, self.total_number_of_operations),
                                                       dtype=np.intc)
            self.required_machine_matrix = np.empty((self.total_number_of_operations, self.total_number_of_machines),
                                                   dtype=np.intc)
            self.job_operation_index_matrix = np.full((self.total_number_of_jobs, self.max_operations_for_a_job), -1,
                                                 dtype=np.intc)

            operation_index = 0
            
            for job_id, operation_data in enumerate(lines[1:]):  
                self.jobs.append(Job(job_id))
                operation_id = 0
                sequence = 0
                operation_data = [int(s) for s in re.sub(r'\s+', ' ', operation_data.strip()).split(' ')]

                i = 1
                while i < len(operation_data):  
                    num_usable_machines = operation_data[i]
                    required_machines = []

                    for j in range(i + 1, i + num_usable_machines * 2 + 1, 2):  #
                        machine = operation_data[j] 
                        runtime = operation_data[j + 1]

                        required_machines.append(machine)
                        self.operation_processing_times_matrix[operation_index, machine] = runtime

                    self.jobs[job_id].get_operations().append(Operation(job_id, operation_id, sequence, required_machines, -1))
                    self.required_machine_matrix[operation_index] = np.resize(np.array(required_machines, dtype=np.intc),
                                                                        self.total_number_of_machines)
                    self.job_operation_index_matrix[job_id, operation_id] = operation_index

                    operation_id += 1
                    sequence += 1
                    operation_index += 1
                    i += num_usable_machines * 2 + 1

                self.jobs[job_id].set_max_sequence(sequence - 1)