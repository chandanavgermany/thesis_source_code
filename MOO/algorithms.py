#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 18 11:04:19 2020

@author: chandan
"""
import time
import random
import pandas as pd
from Optimizer.solution import Solution
from Optimizer.coordinator import CoOrdinator
from Optimizer.Genetic_alg import GASelectionEnum
from Optimizer.data_fjs import Data_Flexible_Job_Shop
from Optimizer.data_normal_job_shop import Data_Normal_Job_Shop
from Rescheduling.utility import get_machine_data

benchmark = True
verbose = True
progress_bar = False

def perform_Tabu_Search(co_ordinator_agent, initial_population=""):
    """
    Starting point of Tabu search
    
    Paramters
    --------------------------
    co_ordinator_agent : object of CoOrdinator class
    initial_population : algorithm name to retrieve solutions
    
    Returns
    ---------------
    best_solution from Tabu search
    """ 
    
    runtime = 15 # in seconds
    num_processes = 4
    num_solutions_per_process = 1
    tabu_list_size = 10
    neighborhood_size = 50
    neighborhood_wait = 0.12
    probability_change_machine = 0.25
    reset_threshold = 50
    population = None
    
    if initial_population is not "":
        population = get_initial_population(co_ordinator_agent, initial_population)
    return co_ordinator_agent.tabu_search_time(runtime=runtime,
                            initial_solutions = population,
                            num_processes=num_processes,
                            num_solutions_per_process=num_solutions_per_process,
                            tabu_list_size=tabu_list_size,
                            neighborhood_size=neighborhood_size,
                            neighborhood_wait=neighborhood_wait,
                            probability_change_machine=probability_change_machine,
                            reset_threshold=reset_threshold,
                            benchmark=benchmark,
                            verbose=verbose,
                            progress_bar=progress_bar)


def perform_Genetic_Search(co_ordinator_agent, initial_population=""):
    """
    Starting point of Genetic algorithm
    
    Paramters
    --------------------------
    co_ordinator_agent : object of CoOrdinator class
    initial_population : algorithm name to retrieve solutions
    
    Returns
    ---------------
    best_solution from Genetic algorithm
    """    
    
    runtime = 15 # in seconds
    mutation_probability = 0.25
    population_size = 100
    selection_method = GASelectionEnum.FITNESS_PROPORTIONATE
    selection_size = 8
    population = None
    
    if initial_population is not "":
        population = get_initial_population(co_ordinator_agent, initial_population)         
    co_ordinator_agent.genetic_algorithm_time(runtime=runtime, 
                              population=population,
                              population_size=population_size, 
                              selection_method_enum=selection_method,
                              selection_size=selection_size,
                              mutation_probability=mutation_probability, 
                              benchmark=benchmark,
                              verbose=verbose,
                              progress_bar=progress_bar)    
    
    
def get_initial_population(co_ordinator_agent, agent_type):

    """
    Returns initial solutions from other algorithm
    
    Paramters
    --------------------------
    co_ordinator_agent : object of CoOrdinator class
    agent_type : algorithm name to retrieve solutions
    
    Returns
    ---------------
    population : solutions from defined algorithm
    """    
    
    
    if agent_type is "" or agent_type is None:
        return None
    population = []
    if agent_type == "tabu_search":
        for ts_agent in co_ordinator_agent.ts_agent_list:
            if ts_agent is not None:
                population += ts_agent.all_solutions
                population = random.sample(population, 4)
    
    elif agent_type == "genetic":
        if co_ordinator_agent.ga_agent is not None: 
            population = co_ordinator_agent.ga_agent.memory # Pareto memory from GA
            initial_solution = list()
            initial_solution.append(co_ordinator_agent.ga_agent.solution_df) # best solution from GA
            
            for i in range(3):
                solution = population.sample()
                initial_solution.append(solution)
                population.remove(solution)
            
            population = pd.concat(initial_solution)
            result_population = list()
            
            # Solution dataframe to list of solution objects
            for index, row in population.iterrows():
                sol_obj = Solution(row.data, row.operation_2d_array, dict_to_obj=True, makespan=row.makespan, stock_cost=row.stock_cost, machine_makespans=row.machine_makespans)
                result_population.append(sol_obj)
                
            population = result_population
  
    return population

            
def generate_output(co_ordinator_agent, job_mapping, schedule_type='initial',
                    preschedule_idle=False, schedule_alg="hybrid"): 
     """
        Provides solution in excel format and also algorithm performance plots
        
        Paramters
        --------------------------
        co_ordinator_agent : object of CoOrdinator class
        
        Returns
        ---------------
        None
        """    
    
    
     output_dir = './example_output'
     return co_ordinator_agent.output_benchmark_results(output_dir, job_mapping, 
                                                        schedule_type=schedule_type, 
                                                        preschedule_idle=preschedule_idle,
                                                        schedule_alg=schedule_alg)

'''
Practical problems and rescheduling experiments
'''

# =============================================================================
# 
# def main(machine_df, job_operation_df, objective_params, reschedule=False,
#          preschedule_idle=False, schedule_alg="hybrid"):
#     while True:
#         try:
#             data_agent = Data_Flexible_Job_Shop('data/seq_dep_matrix_2.xlsx',
#                                                 machine_df,
#                                                 job_operation_df)
#             break
#         except Exception as e:
#             print(str(e))
#             print('Waiting for machine to get fixed')
#             time.sleep(60)
#             machine_df = get_machine_data()
#             machine_df['machine_id'] = machine_df['machine_id'].replace({'M':''}, regex=True)
#             machine_df['machine_id'] = machine_df['machine_id'].astype(int)
#         
# 		   
#     data_agent = Data_Flexible_Job_Shop('data/seq_dep_matrix_2.xlsx',
#                                                 machine_df,
#                                                 job_operation_df)
#     job_mapping = data_agent.job_mapping.drop_duplicates(subset=['prod_name'], keep='last')
#     co_ordinator_agent = CoOrdinator(data_agent, objective_params, reschedule, preschedule_idle)
#     perform_Genetic_Search(co_ordinator_agent, initial_population="")    
#     best_solution = perform_Tabu_Search(co_ordinator_agent, initial_population="genetic")
#     schedule_type = 'initial'
#     if reschedule:
#         schedule_type = 'reschedule'
#     schedule = generate_output(co_ordinator_agent, job_mapping, 
#                                schedule_type, preschedule_idle,
#                                schedule_alg)
#     return schedule, best_solution
# 
# =============================================================================

'''
Benchmark Problems
'''
if __name__ == "__main__":
    
	objective_params = {'makespan': 0.6, 'stock_cost': 0.2, 'tardiness_cost': 0.2, 'stability': 0}    
	data_agent = Data_Normal_Job_Shop('a.txt')    
	co_ordinator_agent = CoOrdinator(data_agent, objective_params)    
	perform_Genetic_Search(co_ordinator_agent, initial_population="")        
	best_solution = perform_Tabu_Search(co_ordinator_agent, initial_population="genetic")
	print(best_solution.makespan)
	print(best_solution.stock_cost)
	print(best_solution.tardiness_cost)