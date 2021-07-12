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

        super().__init__()
        self.fjs_file_path = Path(input_file)
        
        with open(self.fjs_file_path, 'r') as fin:

            lines = [line for line in [l.strip() for l in fin] if line]  # read all non-blank lines
            first_line = [int(s) for s in re.sub(r'\s+', ' ', lines[0].strip()).split(' ')[:-1]]
            print(first_line)
            self.total_number_of_jobs = first_line[0]  # get total num jobs
            self.total_number_of_machines = first_line[1]  # get total num machines

            self.total_number_of_operations = 0
            self.max_operations_for_a_job = 0
            
            for line in lines[1:]: 
                line = [int(s) for s in re.sub(r'\s+', ' ', line.strip()).split(' ')]

                num_operations = self.total_number_of_machines #int(line[0])
                self.total_number_of_operations += num_operations
                self.max_operations_for_a_job = max(num_operations, self.max_operations_for_a_job)
            
           # print(self.total_number_of_operations)
            # initialize matrices
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
                # create and append new Job
                self.jobs.append(Job(job_id))

                operation_id = 0
                sequence = 0

                operation_data = [int(s) for s in re.sub(r'\s+', ' ', operation_data.strip()).split(' ')]
                i = 0
                while i < len(operation_data):  
                    #num_usable_machines = 1
                    required_machines = []
                    machine = operation_data[i] 
                    runtime = operation_data[i + 1]
                    required_machines.append(machine)
                    self.operation_processing_times_matrix[operation_index, machine] = runtime

                    self.jobs[job_id].get_operations().append(Operation(job_id, operation_id, sequence, required_machines, -1))
                    self.required_machine_matrix[operation_index] = np.resize(np.array(required_machines, dtype=np.intc),
                                                                        self.total_number_of_machines)
                    self.job_operation_index_matrix[job_id, operation_id] = operation_index

                    operation_id += 1
                    sequence += 1
                    operation_index += 1
                    i += 2

                self.jobs[job_id].set_max_sequence(sequence - 1)