#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 18 11:04:19 2020

@author: chandan
"""
import random
#from Optimizer.data_fjs import Data_Flexible_Job_Shop
from Optimizer.data_normal_job_shop import Data_Normal_Job_Shop

from Optimizer.coordinator import CoOrdinator
from Optimizer.Genetic_alg import GASelectionEnum

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
    
    runtime = 15 #  seconds
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
    
    runtime = 15 # seconds
    mutation_probability = 0.25
    population_size = 100
    selection_method = GASelectionEnum.FITNESS_PROPORTIONATE
    selection_size = 8
    population = None
    
    if initial_population is not "":
        population = get_initial_population(co_ordinator_agent, initial_population)   
        
    return co_ordinator_agent.genetic_algorithm_time(runtime=runtime, 
                              population=population,
                              population_size=population_size, 
                              selection_method_enum=selection_method,
                              selection_size=selection_size,
                              mutation_probability=mutation_probability, 
                              benchmark=benchmark,
                              verbose=verbose,
                              progress_bar=progress_bar)
    
    
def perform_Simulated_Annealing_Search(co_ordinator_agent, initial_population=""):
    """
    Starting point of Simulated annealing
    
    Paramters
    --------------------------
    co_ordinator_agent : object of CoOrdinator class
    initial_population : algorithm name to retrieve solutions
    
    Returns
    ---------------
    best_solution from Simulated annealing
    """    
    runtime = 15 # in seconds
    neighborhood_size = 50
    neighborhood_wait = 0.1
    T = 100
    termination = 10
    halting = 10
    shrink = 0.9
    population = None
    
    if initial_population is not "":
        population = get_initial_population(co_ordinator_agent, initial_population)
    
    return co_ordinator_agent.simulated_annealing_search_time(runtime=runtime, 
                                                       initial_solution=population,
                                                       num_solutions_to_find=1, 
                                                       neighborhood_size=neighborhood_size, 
                                                       neighborhood_wait=neighborhood_wait, 
                                                       probability_change_machine=0.8,
                                                       T = T, 
                                                       termination = termination,
                                                       halting = halting,
                                                       shrink = shrink, 
                                                       benchmark=benchmark,
                                                       verbose=verbose,
                                                       progress_bar=progress_bar)
    
    
def get_initial_population(co_ordinator_agent, alg):
    """
    Returns initial solutions from other algorithm
    
    Paramters
    --------------------------
    co_ordinator_agent : object of CoOrdinator class
    alg : algorithm name to retrieve solutions
    
    Returns
    ---------------
    population : solutions from defined algorithm
    """    
    
    
    if alg is "" or alg is None:
        return None
    
    population = []
    if alg == "tabu_search":
        for ts_agent in co_ordinator_agent.ts_agent_list:
            if ts_agent is not None:
                population += ts_agent.all_solutions
    
    elif alg == "genetic":
        if co_ordinator_agent.ga_agent is not None: 
            population = co_ordinator_agent.ga_agent.result_population # extract final generation of population
            population = sorted(population) # sort population based on fitness value
            size = int((20 * len(population)) / 100)
            population = population[:size] # top 20 % of solutions from final generation
            population = random.sample(population, 3)
            population.append(co_ordinator_agent.ga_agent.best_solution) # best solution from GA as initial solution
    
    elif alg == "simulated_annealing":
        if co_ordinator_agent.sa_agent is not None: 
            population = co_ordinator_agent.sa_agent.all_solutions
            
    return population



def generate_output(co_ordinator_agent):
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
    co_ordinator_agent.output_benchmark_results(output_dir)


if __name__ == "__main__":
    """
   Main execution block
    """        
    output_dir = './example_output'
    
    '''
    For practical problems
    '''
# =============================================================================
#     data_agent = Data_Flexible_Job_Shop('data/given_data/seq_dep_matrix_2.xlsx',
#                         'data/given_data/machine_info.csv',
#                        'data/given_data/job_info_3.xlsx')
#     co_ordinator_agent = CoOrdinator(data_agent)      
#     best_solution_ga = perform_Genetic_Search(co_ordinator_agent, initial_population="")    
#     best_solution_ts = perform_Tabu_Search(co_ordinator_agent, initial_population="genetic")
# =============================================================================
  
    '''
    For benchmark problems
    '''
  #=============================================================================
    data_agent_nj = Data_Normal_Job_Shop("output.txt")
    co_ordinator_agent = CoOrdinator(data_agent_nj)
    best_solution_ga = perform_Genetic_Search(co_ordinator_agent)    
    best_solution_ts = perform_Tabu_Search(co_ordinator_agent, initial_population="genetic")
  #=============================================================================
  #  generate_output(co_ordinator_agent)    
# =============================================================================
