#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 20:30:16 2020

@author: chandan
"""

class Job:
    def __init__(self, job_id):
        """
        Constructor of class Job
        
        
        Parameters
        -----------------------
        job_id : id of the job
        
        Returns
        -----------------------
        None
        """
        self._job_id = job_id
        self._operations = []
        self._max_sequence = 0

    def set_max_sequence(self, max_sequence):
        """
        Max operations -> setter
        
        """
        self._max_sequence = max_sequence

    def get_max_sequence(self):
        """
        Max operations -> getter
        
        """        
        return self._max_sequence

    def get_operations(self):
        """
        Returns list of operations belongs to job object
        """
        return self._operations

    def get_operation(self, operation_id):
        """
        Returns a specific operation based on its id
        """
        return self._operations[operation_id]

    def get_job_id(self):
        """
        Returns a specific job based on its id
        """
        return self._job_id

    def get_number_of_operations(self):
        """
        Returns a number of operations belongs the job
        """
        return len(self._operations)

    def __eq__(self, other):
        return self._job_id == other.get_job_id() \
               and self._max_sequence == other.get_max_sequence() \
               and self._operations == other.get_operations()