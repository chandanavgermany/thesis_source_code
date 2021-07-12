import random
import numpy as np

from ..data_fjs import Data_Flexible_Job_Shop
from ..utility import Heap
from .solution import Solution


class SolutionFactory:

    def __init__(self, data):
        """    
        Constructor for the class SolutionFactory
        
        Paramters
        --------------------------
        self :  class instance
        data : data object contains information of demand, jobs, machines
        
        Returns
        ---------------
        None
        """
        self.jssp_instance_data = data


    def get_n_solutions(self, n):
        """
        function to return n solutions
        """
        return [self.get_solution() for _ in range(n)]


    def get_solution(self):
        """
        function to return a solution
        """
        return self._generate_solution()


    def get_n_longest_process_time_first_solution(self, n):
        """
        function to return n solutions based on LPT dispatching method
        """
        return [self._generate_solution_w_processing_time_criteria(lpt=True) for _ in range(n)]


    def get_longest_process_time_first_solution(self):
        """
        function to return a solution which is based on LPT dispatching method
        """
        return self._generate_solution_w_processing_time_criteria(lpt=True)


    def get_n_shortest_process_time_first_solution(self, n):
        """
        function to return n solutions based on SPT dispatching method
        """
        return [self._generate_solution_w_processing_time_criteria(lpt=False) for _ in range(n)]


    def get_shortest_process_time_first_solution(self):
        """
        function to return a solution which is based on SPT dispatching method        
        """
        return self._generate_solution_w_processing_time_criteria(lpt=False)


    def _generate_solution(self):
        """
        function to generate a solution
        
        Paramters
        --------------------------
        self :  class instance
        
        Returns
        ---------------
        solution object
        
        """
        
        operation_list = []
        available = {job.get_job_id(): [operation for operation in job.get_operations() if operation.get_sequence() == 0] for job in self.jssp_instance_data.jobs}  # dictionary of first unprocessed operations of each job
        
        while 0 < len(available):
            rand_job_id = random.choice(list(available.keys()))
            rand_operation = random.choice(available[rand_job_id])
            rand_machine = np.random.choice(rand_operation.get_required_machines())

            available[rand_job_id].remove(rand_operation)
            
            if len(available[rand_job_id]) == 0:
                #   if selected operation is last operation of the job 
                if rand_operation.get_sequence() == self.jssp_instance_data.get_job(rand_job_id).get_max_sequence():
                    del available[rand_job_id]
                else:
                    available[rand_job_id] = [t for t in self.jssp_instance_data.get_job(rand_job_id).get_operations() if
                                              t.get_sequence() == rand_operation.get_sequence() + 1]


            operation_list.append([rand_job_id, rand_operation.get_operation_id(), rand_operation.get_sequence(), rand_machine])  # chromosome representation 
        return Solution(self.jssp_instance_data, np.array(operation_list, dtype=np.intc))



    def _generate_solution_w_processing_time_criteria(self, lpt):
        """
        function to generate a solution based on LPT or SPT
        
        Paramters
        --------------------------
        self :  class instance
        
        Returns
        ---------------
        solution object
        
        """
        
        operation_list = []
        last_operation_scheduled_on_machine = [None] * self.jssp_instance_data.total_number_of_machines
        available_heap = _JobOperationHeap(self.jssp_instance_data, max_heap=lpt)

        while 0 < len(available_heap):
            get_unstuck = 0
            rand_operation = available_heap.pop()
            rand_job_id = rand_operation.get_job_id()
            rand_machine = np.random.choice(rand_operation.get_required_machines())
            tmp_operation_list = []
        
            if isinstance(self.jssp_instance_data, Data_Flexible_Job_Shop):
                while last_operation_scheduled_on_machine[rand_machine] is not None \
                        and last_operation_scheduled_on_machine[rand_machine].get_job_id() == rand_job_id \
                        and last_operation_scheduled_on_machine[rand_machine].get_sequence() + 1 < rand_operation.get_sequence():

                    tmp_operation_list.append(rand_operation)

                    rand_operation = available_heap.pop()
                    rand_job_id = rand_operation.get_job_id()
                    rand_machine = np.random.choice(rand_operation.get_required_machines())
                    get_unstuck += 1

                    if get_unstuck > 50:
                        return self.get_solution()

            for operation in tmp_operation_list:
                available_heap.push(operation)

            if len(available_heap.dict[rand_job_id]) == 0:
                if rand_operation.get_sequence() == self.jssp_instance_data.get_job(rand_job_id).get_max_sequence():
                    del available_heap.dict[rand_job_id]
                else:
                    for t in self.jssp_instance_data.get_job(rand_job_id).get_operations():
                        if t.get_sequence() == rand_operation.get_sequence() + 1:
                            available_heap.push(t)

            last_operation_scheduled_on_machine[rand_machine] = rand_operation
            operation_list.append([rand_job_id, rand_operation.get_operation_id(), rand_operation.get_sequence(), rand_machine])

        return Solution(self.jssp_instance_data, np.array(operation_list, dtype=np.intc))

'''
Helper classes, for ease of computation Heap data structure is used to improve computational speed
'''

class _JobOperationHeap(Heap):
    def __init__(self, data, max_heap=False):
        super().__init__(max_heap)
        self.data = data
        self.dict = {}
        for job in data.jobs:
            self.dict[job.get_job_id()] = []
            for operation in job.get_operations():
                if operation.get_sequence() == 0:
                    self.push(operation)

    def push(self, operation):
        super().push(OperationWrapper(self.data, operation))
        self.dict[operation.get_job_id()].append(operation)

    def pop(self):
        operation_wrapper = super().pop()
        operation = operation_wrapper.val
        self.dict[operation.get_job_id()].remove(operation)
        return operation


class OperationWrapper:
    def __init__(self, data, val):
        self.data = data
        self.val = val

    def _get_avg_processing_time(self, other):
        self_index = self.data.job_operation_index_matrix[self.val.get_job_id(), self.val.get_operation_id()]
        other_index = self.data.job_operation_index_matrix[other.val.get_job_id(), other.val.get_operation_id()]
        self_processing_times = [processing_time for processing_time in
                                 self.data.operation_processing_times_matrix[self_index] if
                                 processing_time != -1]
        other_processing_times = [processing_time for processing_time in
                                  self.data.operation_processing_times_matrix[other_index]
                                  if
                                  processing_time != -1]
        self_avg_processing_time = sum(self_processing_times) / len(self_processing_times)
        other_avg_processing_time = sum(other_processing_times) / len(other_processing_times)
        return other_avg_processing_time, self_avg_processing_time

    def __lt__(self, other):
        other_avg_processing_time, self_avg_processing_time = self._get_avg_processing_time(other)
        return self_avg_processing_time < other_avg_processing_time

    def __gt__(self, other):
        other_avg_processing_time, self_avg_processing_time = self._get_avg_processing_time(other)
        return self_avg_processing_time > other_avg_processing_time

    def __eq__(self, other):
        return self.val == other.val
