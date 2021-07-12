#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 20:34:11 2020

@author: chandan
"""

import numpy as np

class Operation:

    def __init__(self, job_id, operation_id, sequence, required_machines, pieces):
        """
        Constructor of class Operation
        
        
        Parameters
        -----------------------
        job_id : id of the job
        operation_id : id of the operation
        sequnce : sequence which operation belongs to
        required_machines : list of machines where operation can be executed
        pieces : number of pieces operation contains to process
        
        Returns
        -----------------------
        None
        """
        
        self._job_id = job_id
        self._operation_id = operation_id
        self._sequence = sequence
        self._required_machines = required_machines
        self._pieces = pieces

    def get_job_id(self):
        return self._job_id

    def get_operation_id(self):
        return self._operation_id

    def get_sequence(self):
        return self._sequence

    def get_required_machines(self):
        return self._required_machines

    def get_pieces(self):
        return self._pieces

    def __eq__(self, other):
        return self._job_id == other.get_job_id() \
               and self._operation_id == other.get_operation_id() \
               and self._sequence == other.get_sequence() \
               and np.array_equal(self._required_machines, other.get_required_machines())  

    def __str__(self):
        return f"[{self._job_id}, " \
            f"{self._operation_id}, " \
            f"{self._sequence}, " \
            f"{self._required_machines}, " \
            f"{self._pieces}]"