#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 09:20:33 2020

@author: chandan
"""

import pickle
import random
import time
import math

import numpy as np

from ._generate_neighbor import generate_neighbor
from ..exception import InfeasibleSolutionException
from ..utility import get_stop_condition, Heap


class SimulatedAnnealingAgent:
    def __init__(self, stopping_condition, time_condition, initial_solution, num_solutions_to_find=1,
                 neighborhood_size=200, neighborhood_wait=0.1, probability_change_machine=0.8, T = 200,
                 termination = 10, halting = 10,mode = 'random', shrink = 0.8, benchmark=False):
        """    
       constructor for SA 
        
        Parameters
        -----------------------------
        stopping_condition : stopping condition for the search
        time_condition : flag for time based search
        initial_solution : initial solution candidate for the search
        num_solutions_to_find : number of best solutions to obtain
        neighbourhood_size : size of the nieghbourhood
        neighbourhood_wait : waiting period 
        probability_change_machine : probability of machine change (FJSSP)
        T : temperature 
        termination : termination value for SA
        halting : halting value for SA
        mode : search mode 
        shrink : shrink value for SA
        
        
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
        self.neighborhood_size = neighborhood_size
        self.neighborhood_wait = neighborhood_wait
        self.probability_change_machine = probability_change_machine
        self.T = T
        self.termination = termination
        self.halting = halting 
        self.mode = mode
        self.shrink = shrink
        self.benchmark = benchmark

        self.all_solutions = []
        self.best_solution = None

        if benchmark:
            self.benchmark_iterations = 0
            self.neighborhood_size_v_iter = []
            self.seed_solution_makespan_v_iter = []
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
                pass
        return neighborhood
    
    
    def start(self, multi_process_queue=None):
        """
        function to execute simulated annealing
        
        Parameter
        --------------------------------------------
        multi_process_queue : multi process queue object to store the best solution of the current process
        
        Returns
        ------------------------------
        best solution of SA
        
        """
        dependency_matrix_index_encoding = self.initial_solution.data.job_operation_index_matrix
        required_machine_matrix = self.initial_solution.data.required_machine_matrix
        seed_solution = self.initial_solution

        if isinstance(self.initial_solution, list):
            seed_solution = self.initial_solution[0]
            
        best_solutions_heap = Heap(max_heap=True)
        
        for _ in range(self.num_solutions_to_find):
            best_solutions_heap.push(self.initial_solution)
        
        iterations = 0
        neighborhood_size_v_iter = []
        seed_solution_makespan_v_iter = []
        absolute_best_solution_makespan = seed_solution.makespan
        absolute_best_solution_iteration = 0
        stop_condition = get_stop_condition(self.time_condition, self.runtime, self.iterations)
        
        while not stop_condition(iterations):
            self.T = self.shrink * float(self.T)
            for j in range(self.termination):
                neighborhood = self._generate_neighborhood(seed_solution,
                                                   dependency_matrix_index_encoding,
                                                   required_machine_matrix)

                sorted_neighborhood = sorted(neighborhood.solutions.items())
                for makespan, lst in sorted_neighborhood:  
                    for neighbor in sorted(lst):  
                        probability = math.exp(-neighbor.makespan / self.T)
                        if (neighbor < seed_solution) or (random.random() < probability):
                            seed_solution = neighbor
                neighborhood_size_v_iter.append(neighborhood.size)
                                
            if seed_solution < best_solutions_heap[0]:
                best_solutions_heap.pop()  
                best_solutions_heap.push(seed_solution)  
                
                if self.benchmark and seed_solution.makespan < absolute_best_solution_makespan:
                    absolute_best_solution_makespan = seed_solution.makespan
                    absolute_best_solution_iteration = iterations


            if self.benchmark:
                iterations += 1
                neighborhood_size_v_iter.append(neighborhood.size)
                seed_solution_makespan_v_iter.append(seed_solution.makespan)

            elif not self.time_condition:
                iterations += 1
        
        best_solutions_list = []
        while len(best_solutions_heap) > 0:
            sol = best_solutions_heap.pop()
            sol.machine_makespans = np.asarray(sol.machine_makespans)
            best_solutions_list.append(sol)

        self.all_solutions = best_solutions_list
        self.best_solution = min(best_solutions_list)

        if self.benchmark:
            self.benchmark_iterations = iterations
            self.neighborhood_size_v_iter = neighborhood_size_v_iter
            self.seed_solution_makespan_v_iter = seed_solution_makespan_v_iter
            self.min_makespan_coordinates = (absolute_best_solution_iteration, absolute_best_solution_makespan)

        if multi_process_queue is not None:
            self.initial_solution.machine_makespans = np.asarray(self.initial_solution.machine_makespans)
            multi_process_queue.put(pickle.dumps(self, protocol=-1))

        return self.best_solution
    
    
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