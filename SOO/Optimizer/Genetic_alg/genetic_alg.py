import random
import statistics
from enum import Enum
from ..exception import InfeasibleSolutionException
#from ..solution import SolutionFactory
from ..utility import get_stop_condition
from ._ga_helpers import crossover


def _tournament_selection(*args):
    """
    tournament selection method
    
    Paramters
    --------------------------
    *args :  multiple arguments
    
    Returns
    ---------------
    parent : selected parent 
    
    """
    selection_indices = random.sample(range(len(args[0])), args[1])
    selection_group = sorted([index for index in selection_indices],
                             key=lambda index: args[0][index].makespan)

    parent = args[0].pop(selection_group[0])
    return parent


def _fitness_proportionate_selection(*args):
    """
    fitness proportionate method
    
    Paramters
    --------------------------
    *args :  multiple arguments
    
    Returns
    ---------------
    sol : selected parent 
    
    """
    fitness_sum = sum(sol.makespan for sol in args[0])
    s = random.uniform(0, fitness_sum)
    partial_sum = 0
    for sol in args[0]:
        partial_sum += sol.makespan
        if partial_sum >= s:
            args[0].remove(sol)
            return sol


def _random_selection(*args):
    """
    Random selection method
    
    Paramters
    --------------------------
    *args :  multiple arguments
    
    Returns
    ---------------
    selected parent 
    
    """
    return args[0].pop(random.randrange(0, len(args[0])))

'''
Enumerated class for GA selection 
'''

class GASelectionEnum(Enum):
    TOURNAMENT = _tournament_selection
    FITNESS_PROPORTIONATE = _fitness_proportionate_selection
    RANDOM = _random_selection



class GeneticAlgorithmAgent:

    def __init__(self, stopping_condition, population, time_condition=False,
                 selection_method_enum=GASelectionEnum.FITNESS_PROPORTIONATE, mutation_probability=0.8,
                 selection_size=2, benchmark=False):
        """
        GeneticAlgorithmAgent constructor
        
        Paramters
        --------------------------
        stopping_condition : stopping condition for GA
        population : list of solutions -> population for GA
        time_condition : flag for time based search
        selection_method_enum : defines parent selection method 
        mutation_probability : probability value for performing mutation on offsprings
        selection_size : parent selection size
        benchmark : flag for plotting benchmark results
        
        Returns
        ---------------
        None
        
        """
        
        assert selection_size is not None and 1 < selection_size, "selection_size must be an integer greater than 1"

        self.runtime = None
        self.iterations = None
        self.time_condition = time_condition
        
        if time_condition:
            self.runtime = stopping_condition
        else:
            self.iterations = stopping_condition

        self.initial_population = population
        self.population_size = len(population)
        self.selection_method = selection_method_enum
        self.mutation_probability = mutation_probability
        self.selection_size = selection_size
        self.benchmark = benchmark

        self.result_population = []
        self.best_solution = None

        if benchmark:
            self.benchmark_iterations = 0
            self.best_solution_makespan_v_iter = []
            self.avg_population_makespan_v_iter = []
            self.min_makespan_coordinates = []



    def start(self):
        """
        function to perform GA search
        
        Paramters
        --------------------------
        self: class instance
        
        Returns
        ---------------
        best_solution : best solution found during the search
        
        """        

        population = self.initial_population[:]
        best_solution = min(population)
        iterations = 0

        data = self.initial_population[0].data
        dependency_matrix_index_encoding = data.job_operation_index_matrix
        required_machine_matrix = data.required_machine_matrix

        best_solution_makespan_v_iter = []
        avg_population_makespan_v_iter = []
        best_solution_iteration = 0
        stop_condition = get_stop_condition(self.time_condition, self.runtime, self.iterations)

        while not stop_condition(iterations):
            if self.benchmark:
                avg_population_makespan_v_iter.append(statistics.mean([sol.makespan for sol in population]))

            next_population = []         
            selection_size = self.selection_size 
            
            while selection_size > 0:
                parent1 = self.selection_method(population, selection_size)
                parent2 = self.selection_method(population, selection_size)

                feasible_child = False
                while not feasible_child:
                    try:
                        child1 = crossover(parent1, parent2,
                                           self.mutation_probability, dependency_matrix_index_encoding,
                                           required_machine_matrix)
                        if child1 != parent1 and child1 != parent2:
                            feasible_child = True
                    except InfeasibleSolutionException:
                        break
                        
                feasible_child = False
                while not feasible_child:
                    try:
                        child2 = crossover(parent2, parent1,
                                           self.mutation_probability, dependency_matrix_index_encoding,
                                           required_machine_matrix)
                        if child2 != parent1 and child2 != parent2:
                            feasible_child = True
                    except InfeasibleSolutionException:
                        break

                next_population.append(child1)
                next_population.append(child2)

                if min(child1, child2) < best_solution:
                    best_solution = min(child1, child2)
                    if self.benchmark:
                        best_solution_iteration = iterations
                selection_size -= 2
                    

            if self.benchmark:
                best_solution_makespan_v_iter.append(best_solution.makespan)
                iterations += 1
            elif not self.time_condition:
                iterations += 1
                
            next_population = self.elitism(population, next_population) 
            population = next_population

        self.best_solution = best_solution
        self.result_population = next_population

        if self.benchmark:
            self.benchmark_iterations = iterations
            self.best_solution_makespan_v_iter = best_solution_makespan_v_iter
            self.avg_population_makespan_v_iter = avg_population_makespan_v_iter
            self.min_makespan_coordinates = (best_solution_iteration, best_solution.makespan)

        return self.best_solution
    
    
    def elitism(self, population, next_population):
        """
        Performs elitism on current population to generate next generation of population
        
        Paramters
        --------------------------
        self: class instance
        population : list of current population of solutions
        next_population : list of next generation of solutions
        
        Returns
        ---------------
        next_population : list of next generation of solutions        
        """  
        population_size = self.population_size
        population_size = population_size - len(next_population)
        
        for i in range(population_size):
            next_population.append(self.selection_method(population, self.selection_size))
        return next_population