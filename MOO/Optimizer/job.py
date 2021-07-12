#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 20:30:16 2020

@author: chandan
"""

class Job:
    def __init__(self, job_id):
        self._job_id = job_id
        self._operations = []
        self._max_sequence = 0

    def set_max_sequence(self, max_sequence):
        self._max_sequence = max_sequence

    def get_max_sequence(self):
        return self._max_sequence

    def get_operations(self):
        return self._operations

    def get_operation(self, operation_id):
        return self._operations[operation_id]

    def get_job_id(self):
        return self._job_id

    def get_number_of_operations(self):
        return len(self._operations)

    def __eq__(self, other):
        return self._job_id == other.get_job_id() \
               and self._max_sequence == other.get_max_sequence() \
               and self._operations == other.get_operations()