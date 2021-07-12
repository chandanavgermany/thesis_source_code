#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 08:45:00 2020

@author: chandan
"""


import pickle
import time
from queue import Queue

import numpy as np

from ._generate_neighbor import generate_neighbor
from ..exception import InfeasibleSolutionException
from ..utility import get_stop_condition, Heap


class TabuSearchAgent:
    def __init__(self, stopping_condition, time_condition, initial_solution, num_solutions_to_find=1,
                 tabu_list_size=50, neighborhood_size=300, neighborhood_wait=0.1, probability_change_machine=0.8,
                 reset_threshold=100, benchmark=False):
        """
        Constructor for TabuSearchAgent
        
        Parameter
        --------------------------------------------

        stopping_condition : stopping condition for the search
        time_condition : flag for time based search
        initial_solution : initial solution candidate for the search
        num_solutions_to_find : number of best solutions to obtain per process
            
        tabu_list_size :  size of the tabu list 
        neighbourhood_size : size of the neighbourhood
        probability_change_machine : probability of machine change (FJSSP)
        reset_threshold : reset threshold for the search        
        
        Returns
        ------------------------------
        None        
        
        """
        
        self.runtime = None
        self.iterations = None
        self.time_condition = time_condition
        if time_condition:
            self.runtime = stopping_condition
        else:
            self.iterations = stopping_condition

        self.initial_solution = initial_solution
        self.num_solutions_to_find = num_solutions_to_find
        self.tabu_list_size = tabu_list_size
        self.neighborhood_size = neighborhood_size
        self.neighborhood_wait = neighborhood_wait
        self.probability_change_machine = probability_change_machine
        self.reset_threshold = reset_threshold
        self.benchmark = benchmark

        self.all_solutions = []
        self.best_solution = None

        if benchmark:
            self.benchmark_iterations = 0
            self.neighborhood_size_v_iter = []
            self.seed_solution_makespan_v_iter = []
            self.tabu_size_v_iter = []
            self.min_makespan_coordinates = (0, 0)
            
            

    def _generate_neighborhood(self, seed_solution, dependency_matrix_index_encoding, required_machine_matrix):
        """
        function to generate neighbourhood of seed solution
        
        Parameter
        --------------------------------------------
        seed_solution :  solution candidate whom's neighbourhood has to be found
        dependency_matrix_index_encoding : job operation matrix
        required_machine_matrix : required machine matrix of all operations of all jobs
        
        Returns
        ------------------------------
        neighborhood : neighbourhood of seed solution        
        
        """
        
        stop_time = time.time() + self.neighborhood_wait
        neighborhood = _SolutionSet()
        while neighborhood.size < self.neighborhood_size and time.time() < stop_time:
            try:
                neighbor = generate_neighbor(seed_solution, self.probability_change_machine,
                                             dependency_matrix_index_encoding, required_machine_matrix)

                if neighbor not in neighborhood:
                    neighborhood.add(neighbor)

            except InfeasibleSolutionException:
                # this should not happen
                # if it does don't add the infeasible solution to the neighborhood
                pass
        return neighborhood
    

    def start(self, multi_process_queue=None):
        """
        function to execute tabu search
        
        Parameter
        --------------------------------------------
        multi_process_queue : multi process queue object to store the best solution of the current process
        
        Returns
        ------------------------------
        best solution of current tabu instance 
        
        """
        dependency_matrix_index_encoding = self.initial_solution.data.job_operation_index_matrix
        required_machine_matrix = self.initial_solution.data.required_machine_matrix
        tabu_list = _TabuList() # initialize tabu list
        seed_solution = self.initial_solution # current best solution
        best_solution = seed_solution # overall best solution
        best_solutions_heap = Heap(max_heap=True)
        
        for _ in range(self.num_solutions_to_find):
            best_solutions_heap.push(self.initial_solution)

        iterations = 0
        neighborhood_size_v_iter = []
        tabu_size_v_iter = []
        seed_solution_makespan_v_iter = []
        absolute_best_solution_makespan = seed_solution.makespan
        absolute_best_solution_iteration = 0
        stop_condition = get_stop_condition(self.time_condition, self.runtime, self.iterations)


        while not stop_condition(iterations):
            neighborhood = self._generate_neighborhood(seed_solution,
                                                       dependency_matrix_index_encoding,
                                                       required_machine_matrix)

            sorted_neighborhood = sorted(neighborhood.solutions.items())
            neighbourhood = [ neighbor[0] for _, neighbor in sorted_neighborhood]


            _, lst = sorted_neighborhood[0]
            neighbour_best_flag = True

            while neighbour_best_flag:
                neighbour_best = sorted(neighbourhood)[0] # best solution from neighbourhood

                if neighbour_best in tabu_list:
                    if neighbour_best < seed_solution:
                        neighbour_best_flag = False
                    
                    else:
                        neighbourhood.remove(neighbour_best)
                else:
                    neighbour_best_flag = False
            
            if neighbour_best < best_solution:
                best_solution = neighbour_best
                
            seed_solution = neighbour_best
                    
            if seed_solution < best_solutions_heap[0]:
                best_solutions_heap.pop()  
                best_solutions_heap.push(seed_solution)  
                if self.benchmark and seed_solution.makespan < absolute_best_solution_makespan:
                    absolute_best_solution_makespan = seed_solution.makespan
                    absolute_best_solution_iteration = iterations

            if seed_solution not in tabu_list:
                tabu_list.put(seed_solution)
            
            if len(tabu_list) > self.tabu_list_size:
                tabu_list.get()           
                
            if self.benchmark:
                iterations += 1
                neighborhood_size_v_iter.append(neighborhood.size)
                seed_solution_makespan_v_iter.append(seed_solution.makespan)
                tabu_size_v_iter.append(len(tabu_list))
            elif not self.time_condition:
                iterations += 1
                
        self.best_solution = best_solution

        if self.benchmark:
            self.benchmark_iterations = iterations
            self.neighborhood_size_v_iter = neighborhood_size_v_iter
            self.seed_solution_makespan_v_iter = seed_solution_makespan_v_iter
            self.tabu_size_v_iter = tabu_size_v_iter
            self.min_makespan_coordinates = (absolute_best_solution_iteration, absolute_best_solution_makespan)

        if multi_process_queue is not None:
            self.initial_solution.machine_makespans = np.asarray(self.initial_solution.machine_makespans)
            multi_process_queue.put(pickle.dumps(self, protocol=-1))

        return self.best_solution


class _TabuList(Queue):
    """
    Tabu list in queue format (FIFO) or least recently used (LRU)
    """

    def __init__(self, max_size=0):
        super().__init__(max_size)
        self.solutions = _SolutionSet()

    def put(self, solution, block=True, timeout=None):
        super().put(solution, block, timeout)
        self.solutions.add(solution)

    def get(self, block=True, timeout=None):
        result = super().get(block, timeout)
        self.solutions.remove(result)
        return result

    def __contains__(self, solution):
        return solution in self.solutions

    def __len__(self):
        return self.solutions.size


class _SolutionSet:
    def __init__(self):
        self.size = 0
        self.solutions = {}

    def add(self, solution):
        if solution.makespan not in self.solutions:
            self.solutions[solution.makespan] = [solution]
        else:
            self.solutions[solution.makespan].append(solution)

        self.size += 1

    def remove(self, solution):
        if len(self.solutions[solution.makespan]) == 1:
            del self.solutions[solution.makespan]
        else:
            self.solutions[solution.makespan].remove(solution)

        self.size -= 1

    def __contains__(self, solution):
        return solution.makespan in self.solutions and solution in self.solutions[solution.makespan]
