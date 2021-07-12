#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 08:45:00 2020
@author: chandan
"""
import pickle
import datetime
import multiprocessing as mp

from .utility import _run_progress_bar
from . import benchmark_plotter
from . import Genetic_alg
from . import Tabu_Search
from . import Simulated_Annealing
from .solution import SolutionFactory


class CoOrdinator:

    def __init__(self, data):
        """    
       constructor of CoOrdinator  class
        
        Paramters
        --------------------------
        data : data object contains information of demand, jobs, machines
 
    
        Returns
        ---------------
        result : None
        """  
        
        self.data = data
        self.solution = None
        self.ts_agent_list = None
        self.ga_agent = None
        self.sa_agent = None
        self.solution_factory = SolutionFactory(data)

    
    def simulated_annealing_search_time(self, runtime, initial_solution, num_solutions_to_find=1, neighborhood_size=100, neighborhood_wait=0.1, probability_change_machine=0.8, T = 200, termination = 10, halting = 10, mode = 'random', shrink = 0.8, benchmark=False, verbose=False, progress_bar=False):
        """    
        simulated_annealing search (time as a constraint)
        """        
        
        if isinstance(runtime, datetime.timedelta):
            runtime_seconds = runtime.total_seconds()
        else:
            runtime_seconds = runtime       
        return self._simulated_annealing(runtime_seconds, time_condition=True, initial_solution=initial_solution, num_solutions_to_find=1, neighborhood_size=neighborhood_size, neighborhood_wait=neighborhood_wait, probability_change_machine=probability_change_machine, T=T, termination=termination, halting=halting, mode=mode, shrink=shrink, benchmark=benchmark, verbose=verbose, progress_bar=progress_bar)
        
    
    
    def _simulated_annealing(self, stopping_condition, time_condition, initial_solution, num_solutions_to_find, neighborhood_size, neighborhood_wait, probability_change_machine, T, termination, halting, mode, shrink, benchmark, verbose, progress_bar):
        """    
        simulated_annealing search builder function
        
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
        best solution from SA
        """               
        
        
        if initial_solution is None:
            initial_solution = self.solution_factory.get_solution()
        
        if isinstance(initial_solution, list):
            initial_solution = initial_solution[0]
        
        self.sa_agent = Simulated_Annealing.SimulatedAnnealingAgent(stopping_condition, 
                                                                    time_condition, 
                                                                    initial_solution, 
                                                                    num_solutions_to_find,
                                                                    neighborhood_size, 
                                                                    neighborhood_wait, 
                                                                    probability_change_machine,
                                                                    T,
                                                                    termination,
                                                                    halting,
                                                                    mode,
                                                                    shrink, 
                                                                    benchmark)
        if verbose:
            if benchmark:
                print("Running benchmark of SA")
            else:
                print("Running SA")
            print("Parameters:")
            print(f"stopping_condition = {stopping_condition} {'seconds' if time_condition else 'iterations'}")
            print("time_condition =", time_condition)
            print("neighborhood_size =", neighborhood_size)
            print("neighborhood_wait =", neighborhood_wait)
            print("probability_change_machine =", probability_change_machine)
            print()
            print("Initial Solution's makespans:")
            
            print(round(initial_solution.makespan))
            print()

        if progress_bar and time_condition:
            mp.Process(target=_run_progress_bar, args=[stopping_condition]).start()

        self.solution = self.sa_agent.start() 
        
        print(self.solution)
        return self.solution
        
 ################################ Tabu Search Algorithm ###########################
   
    
    def tabu_search_time(self, runtime, num_solutions_per_process=1, num_processes=4, tabu_list_size=50,
                         neighborhood_size=300, neighborhood_wait=0.1, probability_change_machine=0.8,
                         reset_threshold=100, initial_solutions=None, benchmark=False, verbose=False, progress_bar=False):
        """
       Tabu search initiator (time as constraint)
       """
        if isinstance(runtime, datetime.timedelta):
            runtime_seconds = runtime.total_seconds()
        else:
            runtime_seconds = runtime

        return self._tabu_search(runtime_seconds, time_condition=True, num_solutions_per_process=num_solutions_per_process,
                                 num_processes=num_processes, tabu_list_size=tabu_list_size,
                                 neighborhood_size=neighborhood_size, neighborhood_wait=neighborhood_wait,
                                 probability_change_machine=probability_change_machine,
                                 reset_threshold=reset_threshold, initial_solutions=initial_solutions,
                                 benchmark=benchmark, verbose=verbose, progress_bar=progress_bar)


    def tabu_search_iter(self, iterations, num_solutions_per_process=1, num_processes=4, tabu_list_size=50,
                         neighborhood_size=300, neighborhood_wait=0.1, probability_change_machine=0.8,
                         reset_threshold=100, initial_solutions=None, benchmark=False, verbose=False):
        """
       Tabu search initiator (iterations as constraint)
        """
        
        return self._tabu_search(iterations, time_condition=False, num_solutions_per_process=num_solutions_per_process,
                                 num_processes=num_processes, tabu_list_size=tabu_list_size,
                                 neighborhood_size=neighborhood_size, neighborhood_wait=neighborhood_wait,
                                 probability_change_machine=probability_change_machine,
                                 reset_threshold=reset_threshold, initial_solutions=initial_solutions,
                                 benchmark=benchmark, verbose=verbose, progress_bar=False)


    def _tabu_search(self, stopping_condition, time_condition, num_solutions_per_process, num_processes, tabu_list_size,
                     neighborhood_size, neighborhood_wait, probability_change_machine, reset_threshold,
                     initial_solutions, benchmark, verbose, progress_bar):
        """    
        Tabu search builder function
        
        Parameters
        -----------------------------
        stopping_condition : stopping condition for the search
        time_condition : flag for time based search
        initial_solution : initial solution candidate for the search
        num_solutions_per_process : number of best solutions to obtain per process
        num_processes : number of process which executes tabu search in parallel
            
        tabu_list_size :  size of the tabu list 
        neighbourhood_size : size of the neighbourhood
        probability_change_machine : probability of machine change (FJSSP)
        reset_threshold : reset threshold for the search
        initial_solutions : list of initial solution candidates
        
        
        Returns
        ------------------------------
        best solution from all tabu search processes
        """               
        
        if initial_solutions is None:
            initial_solutions = [self.solution_factory.get_solution() for _ in range(num_processes)]
        else:
            initial_solutions += [self.solution_factory.get_solution() for _ in
                                  range(max(0, num_processes - len(initial_solutions)))]

        ts_agent_list = [Tabu_Search.TabuSearchAgent(stopping_condition,
                                                     time_condition,
                                                     initial_solution,
                                                     num_solutions_per_process,
                                                     tabu_list_size,
                                                     neighborhood_size,
                                                     neighborhood_wait,
                                                     probability_change_machine,
                                                     reset_threshold,
                                                     benchmark)
                         for initial_solution in initial_solutions] # initialize tabu instances

        if verbose:
            if benchmark:
                print("Running benchmark of TS")
            else:
                print("Running TS")
            print("Parameters:")
            print(f"stopping_condition = {stopping_condition} {'seconds' if time_condition else 'iterations'}")
            print("time_condition =", time_condition)
            print("num_solutions_per_process =", num_solutions_per_process)
            print("num_processes =", num_processes)
            print("tabu_list_size =", tabu_list_size)
            print("neighborhood_size =", neighborhood_size)
            print("neighborhood_wait =", neighborhood_wait)
            print("probability_change_machine =", probability_change_machine)
            print("reset_threshold =", reset_threshold)
            print()
            print("Initial Solution's makespans:")
            print([round(x.makespan) for x in initial_solutions])
            print()
            
        '''
        For multi agent
        '''

        # create tabu instances to run tabu search
        child_results_queue = mp.Queue()
        processes = [
            mp.Process(target=ts_agent.start, args=[child_results_queue])
            for ts_agent in ts_agent_list
        ]

        # start execution of tabu instances
        for p in processes:
            p.start() # Start tabu search process
            if verbose:
                print(f"child TS process started. pid = {p.pid}")


        if progress_bar and time_condition:
            mp.Process(target=_run_progress_bar, args=[stopping_condition]).start()

        # collect results from Queue and wait for all tabu search processes to finish
        self.ts_agent_list = []
        for p in processes:
            self.ts_agent_list.append(pickle.loads(child_results_queue.get()))

            if verbose:
                print(f"child TS process finished. pid = {p.pid}")
 
        # Find overall best solution from all the tabu instances or processes
        self.best_solution = min([ts_agent.best_solution for ts_agent in self.ts_agent_list])
        return self.best_solution
    
    '''
    For single agent 
    '''
# =============================================================================
#         agent = ts_agent_list[0]
#         self.ts_agent_list = []
#         best_solution = agent.start()
#         self.ts_agent_list.append(agent)        
#         return best_solution
# 
# =============================================================================
    
    
################################ Genetic Algorithm ###########################
    def genetic_algorithm_time(self, runtime, population=None, population_size=200,
                               selection_method_enum=Genetic_alg.GASelectionEnum.TOURNAMENT,
                               mutation_probability=0.8, selection_size=10, benchmark=False, verbose=False,
                               progress_bar=False):
        """
        Genetic algorithm (time constraint)
        """
        if isinstance(runtime, datetime.timedelta):
            runtime_seconds = runtime.total_seconds()
        else:
            runtime_seconds = runtime
        return self._genetic_algorithm(runtime_seconds, time_condition=True, population=population,
                                       population_size=population_size,                 selection_method_enum=selection_method_enum,
                                       mutation_probability=mutation_probability,
                                       selection_size=selection_size, benchmark=benchmark, verbose=verbose,
                                       progress_bar=progress_bar)


    def genetic_algorithm_iter(self, iterations, population=None, population_size=200,
                               selection_method_enum=Genetic_alg.GASelectionEnum.FITNESS_PROPORTIONATE,
                               mutation_probability=0.8,
                               selection_size=10, benchmark=False, verbose=False):
        """
        Genetic algorithm (iterations constraint)
        """
        return self._genetic_algorithm(iterations, time_condition=False, population=population,
                                       population_size=population_size, selection_method_enum=selection_method_enum,
                                       mutation_probability=mutation_probability,
                                       selection_size=selection_size, benchmark=benchmark, verbose=verbose,
                                       progress_bar=False)


    def _genetic_algorithm(self, stopping_condition, time_condition, population=None, population_size=200,
                           selection_method_enum=Genetic_alg.GASelectionEnum.FITNESS_PROPORTIONATE, mutation_probability=0.8,
                           selection_size=8, benchmark=False, verbose=False, progress_bar=False):
        """
        Genetic Algorithm builder function
        
        Parameters
        -------------------------
        stopping_condition : stopping condition for the search
        time_condition : flag for time based search
        population : population of solutions
        population_size : size of the population
        selection_method_enum : Parent selection method identifier
        mutation_probability : probability value for performing mutation on offsprings
        selection_size : parent selection size
        benchmark : flag for plotting benchmark results


        Returns
        ------------------
        best solution from GA search
        """
        if population is None:
            population = [self.solution_factory.get_solution() for _ in range(population_size)]
        else:
            population = population[:] + [self.solution_factory.get_solution() for _ in range(max(0, population_size - len(population)))]

        # genetic algorithm instance creation
        self.ga_agent = Genetic_alg.GeneticAlgorithmAgent(stopping_condition,
                                                                population,
                                                                time_condition,
                                                                selection_method_enum,
                                                                mutation_probability,
                                                                selection_size,
                                                                benchmark
                                                                )
        if verbose:
            if benchmark:
                print("Running benchmark of GA")
            else:
                print("Running GA")
            print("Parameters:")
            print(f"stopping_condition = {stopping_condition} {'seconds' if time_condition else 'iterations'}")
            print("time_condition =", time_condition)
            print("population_size =", population_size)
            print("selection_method =", selection_method_enum.__name__)
            print("mutation_probability =", mutation_probability)
            if selection_method_enum is Genetic_alg.GASelectionEnum.TOURNAMENT:
                print("selection_size =", selection_size)

        if progress_bar and time_condition:
            mp.Process(target=_run_progress_bar, args=[stopping_condition]).start()

        # Execution stating point for genetic algorithm
        self.solution = self.ga_agent.start()
        return self.solution


    ############################ Utility functions #############################################

    def iplot_benchmark_results(self):
        self._check_agents()
        benchmark_plotter.iplot_benchmark_results(ts_agent_list=self.ts_agent_list, 
                                                                                  ga_agent=self.ga_agent,
                                                                                  sa_agent=self.sa_agent)


    def output_benchmark_results(self, output_dir, title=None, auto_open=True):
        self._check_agents()
        benchmark_plotter.output_benchmark_results(output_dir, 
                                                                                   ts_agent_list=self.ts_agent_list,
                                                                                   ga_agent=self.ga_agent,
                                                                                   sa_agent=self.sa_agent,
                                                                                   title=title, 
                                                                                   auto_open=auto_open)


    def _check_agents(self):
        # check if both agents are none before plotting results
        
        if self.ts_agent_list is None and self.ga_agent is None and self.sa_agent is None:
            raise UserWarning("Solver's agents were None. You need to run at least one optimization function.")

        # check if one agent was ran in benchmark mode
        if not any([self.ts_agent_list is None or all(ts_agent.benchmark for ts_agent in self.ts_agent_list),
                    self.ga_agent is None or self.ga_agent.benchmark or self.sa_agent or self.sa_agent.benchmark]):
            raise UserWarning("You must run one of the optimization functions in benchmark mode.")