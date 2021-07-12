#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 08:45:00 2020

@author: chandan
"""
import pickle
import time
from queue import Queue
import pandas as pd

from ._generate_neighbor import generate_neighbor
from ..exception import InfeasibleSolutionException
from ..utility import get_stop_condition, Heap
from ..pareto_front import get_multi_objective_optimal_sol, dominates, dominates_2
from ..solution import Solution


#standalone function
def rebuild(solution):
    p = TabuSearchAgent(stopping_condition=None, time_condition=None, initial_solution=None)
    p.best_solution = solution
    return p


class TabuSearchAgent:
    def __init__(self, stopping_condition, time_condition, initial_solution, num_solutions_to_find=1,
                 tabu_list_size=50, neighborhood_size=300, neighborhood_wait=0.1, probability_change_machine=0.8,
                 reset_threshold=100, benchmark=False, memory=None, population=None, objective_params=None, 
                 reschedule=False, preschedule_idle=False):
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
        benchmark : Flag to store benchmark results
        memory : Pareto memory from GA
        population : population from GA (not used)
        objective_params : objective functions list
        reschedule : Flag to set reschedule mode
        preschedule_idle : Flag to set preschedule_idle mode
        
        Returns
        ------------------------------
        self.memory : resulting pareto memory from tabu search   
        
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

        # uninitialized ts results
        self.all_solutions = []
        self.best_solution = None
        self.objective_params = objective_params
        self.reschedule = 0
        self.preschedule_idle = 0
        
        if reschedule:
            self.reschedule = 1
        if preschedule_idle:
            self.preschedule_idle = 1
        
        self.memory = memory
        self.population = population

        if benchmark:
            # uninitialized ts benchmark results
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
                                             dependency_matrix_index_encoding, required_machine_matrix,
                                             reschedule=self.reschedule,
                                             preschedule_idle=self.preschedule_idle)

                if neighbor not in neighborhood:
                    neighborhood.add(neighbor)

            except InfeasibleSolutionException:
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

        tabu_list = _TabuList()
        seed_solution = self.initial_solution
        
        best_solutions_heap = Heap(max_heap=True)
        for _ in range(self.num_solutions_to_find):
            best_solutions_heap.push(self.initial_solution)

        iterations = 0
        stop_condition = get_stop_condition(self.time_condition, self.runtime, self.iterations)

        while not stop_condition(iterations):
            neighborhood = self._generate_neighborhood(seed_solution,
                                                       dependency_matrix_index_encoding,
                                                       required_machine_matrix)

            sorted_neighborhood = sorted(neighborhood.solutions.items())
            neighbourhood = [ neighbor[0] for _, neighbor in sorted_neighborhood]
            
            neighbourhood_pareto, best_solution = get_multi_objective_optimal_sol(neighbourhood, self.objective_params, self.reschedule, visualize=False, rank=1) 
            
            neighbourhood_pareto = neighbourhood_pareto.loc[neighbourhood_pareto['rank'] == 0] # Pareto Optimal solutions from Neighburhood
            
            neighbourhood_pareto = self.convert_to_solution_obj(neighbourhood_pareto)
            
            for neighbor in neighbourhood_pareto:
                if neighbor not in tabu_list and neighbor not in self.memory and self.neighbor_dominates(neighbor):
                    tabu_list.put(neighbor)
            
            
            neighbour_best_flag = True
            while neighbour_best_flag:
                _, neighbor_best = get_multi_objective_optimal_sol(neighbourhood_pareto, self.objective_params, self.reschedule, visualize=False, rank=1)           
                
                if neighbor_best in tabu_list:
                    # if neighbor dominates seed solution
                     if dominates_2(neighbor_best, seed_solution, self.objective_params, self.reschedule):
                         neighbour_best_flag = False
                     else:
                         neighbourhood_pareto.remove(neighbor_best)
                else:
                    neighbour_best_flag = False
                    
            
            seed_solution = neighbor_best
            
            if seed_solution not in tabu_list:
                tabu_list.put(seed_solution)
                
            if len(tabu_list) > self.tabu_list_size:
                tabu_list.get() 
            
        self.memory = self.memory.loc[self.memory['rank'] == 0] # Pareto front (Pareto optimal solutions)
            
        if multi_process_queue is not None:
            multi_process_queue.put(pickle.dumps(self, protocol=-1))
        
        # Convert solutions from dataframe to list of solution objects 
        self.memory = self.convert_to_solution_obj(self.memory)
        return self.memory
    
    
    def neighbor_dominates(self, new_solution):
        """
        function to verify whether neighbor dominates Pareto solutions
        
        Parameters
        ---------------------------
        new_solution : solution object
        
        Returns 
        --------------------------
        Flag : whether neighbor dominates or not
        
        """
        
        if dominates(self.memory, new_solution=new_solution, objective_params=self.objective_params, reschedule=self.reschedule, rank=1):
            self.memory = pd.concat([self.memory, pd.DataFrame([new_solution.as_dict()])])
            return True
        return False        
    
 
    def convert_to_solution_obj(self, df):
        """
        function to convert solution dataframe into solution objects
        
        Parameters
        ---------------------------
        df : solution dataframe
        
        Returns 
        --------------------------
        result_population : list of solution objects
        
        """
        
        result_population = list()
        for index, row in df.iterrows():
                sol_obj = Solution(row.data, row.operation_2d_array, dict_to_obj=True, makespan=row.makespan,
                                   stock_cost=row.stock_cost, machine_makespans=row.machine_makespans,
                                   tardiness_cost=row.tardiness_cost, due_date=row.due_date,
                                   stability=row.stability,
                                   reschedule=self.reschedule,
                                   preschedule_idle=self.preschedule_idle,
                                   job_operation_runtime_matrix=row.job_operation_runtime_matrix,
                                   operations=row.operations)
                result_population.append(sol_obj)
        return result_population



"""
Tabu list in queue format (FIFO) or least recently used (LRU)
"""
    

class _TabuList(Queue):

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
