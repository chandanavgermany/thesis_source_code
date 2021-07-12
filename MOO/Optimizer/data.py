#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 17:56:30 2020

@author: chandan
"""

import re
from abc import ABC
from pathlib import Path


class Data(ABC):    
    
    def __init__(self):
        self.sequence_dependency_matrix = None
        self.job_operation_index_matrix = None
        self.required_machine_matrix = None
        self.operation_processing_times_matrix = None
        self.machine_speed_matrix = None # time taken to produce one part
        self.machine_setup_time_matrix = None
        self.jobs = []
        self.machines = []
        
        self.total_number_of_jobs = 0
        self.total_number_of_operations = 0
        self.total_number_of_machines = 0
        
        self.max_operations_for_a_job = 0
        
    
    def get_setup_time(self, job1_id, job1_operation_id, job2_id, job2_operation_id):
        
        if min(job1_id, job1_operation_id, job2_id, job2_operation_id) < 0:
            return 0

        return self.sequence_dependency_matrix[
            self.job_operation_index_matrix[job1_id, job1_operation_id],
            self.job_operation_index_matrix[job2_id, job2_operation_id]
        ]
        
    
    def get_runtime(self, job_id, operation_id, machine):
        return self.operation_processing_times_matrix[self.job_operation_index_matrix[job_id, operation_id], machine]
    
    
    def get_job(self, job_id):
        return self.jobs[job_id]
    
    
    def __str__(self):
        result = f"total jobs = {self.total_number_of_jobs}\n" \
                 f"total operations = {self.total_number_of_operations}\n" \
                 f"total machines = {self.total_number_of_machines}\n" \
                 f"max operations for a job = {self.max_operations_for_a_job}\n" \
                 f"operations:\n" \
                 f"[jobId, operationId, sequence, usable_machines, pieces]\n"

        for job in self.jobs:
            for operation in job.get_operations():
                result += str(operation) + '\n'

        if self.sequence_dependency_matrix is not None:
            result += f"sequence_dependency_matrix: {self.sequence_dependency_matrix.shape}\n\n" \
                      f"{self.sequence_dependency_matrix}\n\n"

        if self.job_operation_index_matrix is not None:
            result += f"dependency_matrix_index_encoding: {self.job_operation_index_matrix.shape}\n\n" \
                      f"{self.job_operation_index_matrix}\n\n"

        if self.required_machine_matrix is not None:
            result += f"usable_machines_matrix: {self.required_machine_matrix.shape}\n\n" \
                      f"{self.required_machine_matrix}\n\n"

        if self.operation_processing_times_matrix is not None:
            result += f"operation_processing_times: {self.operation_processing_times_matrix.shape}\n\n" \
                      f"{self.operation_processing_times_matrix}\n\n"

        if self.machine_speed_matrix is not None:
            result += f"machine_speeds: {self.machine_speed_matrix.shape}\n\n" \
                      f"{self.machine_speed_matrix}"

        return result
    

    @staticmethod
    def convert_fjs_to_csv(fjs_file, output_dir):
 
        total_num_operations = 0

        fjs_file = Path(fjs_file)
        output_dir = Path(output_dir)

        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # read .fjs input file and create jobOperations.csv
        with open(fjs_file, 'r') as fin:
            with open(output_dir / 'jobOperations.csv', 'w') as fout:
                fout.write("job,operation,sequence,required_machines,pieces\n")

                lines = [line for line in [l.strip() for l in fin] if line]
                line = [int(s) for s in re.sub(r'\s+', ' ', lines[0].strip()).split(' ')[:-1]]

                total_num_machines = line[1]

                # iterate over jobs
                for job_id, operations in enumerate(lines[1:]):

                    # get the operations data
                    operation_data = [int(s) for s in re.sub(r'\s+', ' ', operations.strip()).split(' ')]
                    total_num_operations += operation_data[0]
                    operation_id = 0
                    sequence = 0

                    # iterate over operations
                    i = 1
                    while i < len(operation_data):
                        required_machines = "["
                        output_line = f"{job_id},{operation_id},{sequence},"
                        num_usable_machines = operation_data[i]

                        for j in range(i + 1, i + num_usable_machines * 2 + 1, 2):
                            required_machines += f"{operation_data[j] - 1} "

                        output_line += required_machines[:-1] + "]," + str(operation_data[i + 2])
                        i += num_usable_machines * 2 + 1
                        operation_id += 1
                        sequence += 1
                        fout.write(output_line + '\n')

        # create machineRunSpeed.csv
        with open(output_dir / 'machineRunSpeed.csv', 'w') as fout:
            fout.write("Machine,RunSpeed\n")
            for i in range(total_num_machines):
                fout.write(f"{i},1\n")

        # create sequenceDependencyMatrix.csv
        with open(output_dir / 'sequenceDependencyMatrix.csv', 'w') as fout:
            line = "0," * total_num_operations + "0\n"
            for _ in range(total_num_operations + 1):
                fout.write(line)