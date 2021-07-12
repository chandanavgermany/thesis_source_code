#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 19:53:02 2020

@author: chandan
"""

import numpy as np
import pandas as pd
from pathlib import Path

from .data import Data
from .operation import Operation
from .job import Job

class Data_Flexible_Job_Shop(Data):  
    
    def __init__(self, sequence_dependency_matrix, machine_speed_matrix, job_operations):
        """
        Constructor for Data_Flexible_Job_Shop
        
        Parameter
        --------------------------------------------

        sequence_dependency_matrix : sequency dependency matrix for operations
        machine_speed_matrix : machine processing speed matrix
        job_operations : job_operations matrix
        
        Returns
        ------------------------------
        None        
        
        """
        
        super().__init__()        
        
        if isinstance(job_operations, pd.DataFrame):
            self.job_operations_df = job_operations
        else:
            self.job_operations_df = self.to_df(job_operations)
            
        if isinstance(sequence_dependency_matrix, pd.DataFrame) or sequence_dependency_matrix is None:
            self.sequence_dependency_matrix_df = sequence_dependency_matrix
        else:
            self.sequence_dependency_matrix_df = self.to_df(sequence_dependency_matrix)
            
        if isinstance(machine_speed_matrix, pd.DataFrame):
            self.machine_speed_matrix_df = machine_speed_matrix
        else:
            self.machine_speed_matrix_df = self.to_df(machine_speed_matrix)
        
        self._read_job_operations_df(self.job_operations_df)
        self._read_machine_speed_matrix_df(self.machine_speed_matrix_df)
        print(self.machine_speed_matrix)

        
        if self.sequence_dependency_matrix_df is not None and False:
            self._read_sequence_dependency_matrix_df(self.sequence_dependency_matrix_df)
        else:
            num_operations = self.job_operations_df.shape[0]
            self.sequence_dependency_matrix = np.zeros((num_operations, num_operations), dtype=np.intc)

        self.total_number_of_jobs = len(self.jobs)
        self.total_number_of_operations = sum(len(job.get_operations()) for job in self.jobs)
        self.max_operations_for_a_job = max(job.get_number_of_operations() for job in self.jobs)
        self.total_number_of_machines = self.machine_speed_matrix.shape[0]

        self.job_operation_index_matrix = np.full((self.total_number_of_jobs, self.max_operations_for_a_job), -1, dtype=np.intc)
 
        self.required_machine_matrix = np.empty((self.total_number_of_operations, self.total_number_of_machines),
                                                   dtype=np.intc)
        self.operation_processing_times_matrix = np.full((self.total_number_of_operations, self.total_number_of_machines), -1, dtype=np.float)


        operation_index = 0
        for job in self.jobs:
            for operation in job.get_operations():

                # create mapping of (job id, task id) to index
                self.job_operation_index_matrix[job.get_job_id(), operation.get_operation_id()] = operation_index
                # create row in usable_machines_matrix
                self.required_machine_matrix[operation_index] = np.resize(operation.get_required_machines(),
                                                                    self.total_number_of_machines)

                # create row in operation_processing_times
                for machine in operation.get_required_machines():
                   self.operation_processing_times_matrix[operation_index, machine] = operation.get_pieces() / self.machine_speed_matrix[machine]
                operation_index += 1
    
    
    
    def _read_machine_speed_matrix_df(self, machine_speed_matrix_df):
        
        machine_speed_matrix_df = machine_speed_matrix_df.sort_values('Machine')
        self.machine_speed_matrix = np.array([row['RunSpeed'] for i, row in machine_speed_matrix_df.iterrows()], dtype=np.float)
        self.machine_setup_time_matrix = np.array([int(row['Setup']) for i, row in machine_speed_matrix_df.iterrows()], dtype=np.intc)
        
        
        
    def _read_sequence_dependency_matrix_df(self, sequence_dependency_matrix_df):
        
        sequence_dependency_matrix_df = sequence_dependency_matrix_df.drop(sequence_dependency_matrix_df.columns[0], axis=1)  
        tmp = []
        for r, row in sequence_dependency_matrix_df.iterrows():
            tmp2 = []
            for c, value in row.iteritems():
                tmp2.append(value)
            tmp.append(tmp2)

        self.sequence_dependency_matrix = np.array(tmp, dtype=np.intc)
    
    
    def _read_job_operations_df(self, job_operations_df):

        seen_jobs_ids = set()
        job_operations_df.columns= job_operations_df.columns.str.lower()

        for i, row in job_operations_df.iterrows():
            # create task object
            operation = Operation(
                int(row['job']),
                int(row['operation']),
                int(row['sequence']),
                np.array([int(x) for x in row['required_machines'][1:-1].strip().split(' ')], dtype=np.intc),
                int(row['pieces'])
            )
            job_id = operation.get_job_id()

            # create & append new job if we encounter job_id that has not been seen
            if job_id not in seen_jobs_ids:
                self.jobs.append(Job(job_id))
                seen_jobs_ids.add(job_id)

            if operation.get_sequence() > self.get_job(job_id).get_max_sequence():
                self.get_job(job_id).set_max_sequence(operation.get_sequence())

            self.get_job(job_id).get_operations().append(operation)

    
    def to_df(self, path):
        path = Path(path)

        if path.suffix == ".csv":
            return pd.read_csv(path)
        elif path.suffix == ".xlsx":
            return pd.read_excel(path)
        else:
            raise Exception("File extension must either be .csv or .xlsx")
        