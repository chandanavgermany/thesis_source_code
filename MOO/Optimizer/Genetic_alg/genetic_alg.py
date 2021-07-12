import random
import statistics
import pandas as pd
from enum import Enum
from ..exception import InfeasibleSolutionException
from ..solution import SolutionFactory, Solution
from ..utility import get_stop_condition
from ._ga_helpers import crossover
from ..pareto_front import get_multi_objective_optimal_sol, dominates


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
                 selection_size=8, benchmark=False, objective_params=None, reschedule=False,
                 preschedule_idle=False):     
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
        self.memory = None
        self.objective_params = objective_params
        self.reschedule = 0
        self.preschedule_idle = 0
        
        if reschedule:
            self.reschedule = 1
        
        if preschedule_idle:
            self.preschedule_idle = 1
        
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
        pareto_solutions, best_solution = get_multi_objective_optimal_sol(population, self.objective_params, self.reschedule, visualize=True, rank=3)
        self.memory = pareto_solutions
        
        
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
            pareto_solutions, best_solution = get_multi_objective_optimal_sol(population, self.objective_params, self.reschedule, visualize=False, rank=3)
            
            parents = self.parent_selection_moo(pareto_solutions, self.selection_size)
            selection_size = self.selection_size 
            
            while selection_size > 0:
                parent1 = random.sample(parents, 1)
                parent2 = random.sample(parents, 1)
                
                feasible_child = False
                while not feasible_child:
                    try:
                        child1 = crossover(parent1, parent2,
                                           self.mutation_probability, 
                                           dependency_matrix_index_encoding,
                                           required_machine_matrix,
                                           reschedule=self.reschedule,
                                           preschedule_idle=self.preschedule_idle)
                        if child1 != parent1 and child1 != parent2:
                            feasible_child = True
                    except InfeasibleSolutionException:
                        break
                        
                feasible_child = False
                while not feasible_child:
                    try:
                        child2 = crossover(parent2, parent1,
                                           self.mutation_probability, 
                                           dependency_matrix_index_encoding,
                                           required_machine_matrix,
                                           reschedule=self.reschedule,
                                           preschedule_idle=self.preschedule_idle)
                        if child2 != parent1 and child2 != parent2:
                            feasible_child = True
                    except InfeasibleSolutionException:
                        break
                
                if self.child_dominates(child1):
                    next_population.append(child1)
                
                if self.child_dominates(child2):
                    next_population.append(child2)
                    
                selection_size -= 2
                parents.remove(parent1)
                parents.remove(parent2)
   
            population = self.elitism(population, next_population) # next generation

        self.memory, best_solution = get_multi_objective_optimal_sol(population, self.objective_params, self.reschedule, visualize=True, rank=3) # final generation results
        
        self.best_solution = best_solution        
        for index, row in self.memory.iterrows():
                sol_obj = Solution(row.data, row.operation_2d_array, dict_to_obj=True,
                                   makespan=row.makespan, stock_cost=row.stock_cost, 
                                   machine_makespans=row.machine_makespans,
                                   due_date=row.due_date,
                                   tardiness_cost=row.tardiness_cost,
                                   stability=row.stability,
                                   reschedule=self.reschedule,
                                   preschedule_idle=self.preschedule_idle,
                                   job_operation_runtime_matrix=row.job_operation_runtime_matrix,
                                   operations=row.operations)
                self.result_population.append(sol_obj)
            
        if self.benchmark:
            self.benchmark_iterations = iterations
            self.best_solution_makespan_v_iter = best_solution_makespan_v_iter
            self.avg_population_makespan_v_iter = avg_population_makespan_v_iter
            self.min_makespan_coordinates = (best_solution_iteration, best_solution.makespan)
        
        self.solution_df = self.best_solution 
        self.best_solution = self.convert_to_solution_obj(self.best_solution)[0]
        return self.best_solution


    def child_dominates(self, new_solution):
        """
        function to evaluate if a solution dominates
        
        Paramters
        --------------------------
        new_solution : solution
        
        Returns
        ---------------
        flag 
        
        """ 
        if dominates(self.memory, new_solution=new_solution, objective_params=self.objective_params, reschedule=self.reschedule):
            self.memory = pd.concat([self.memory, pd.DataFrame([new_solution.as_dict()])])
            self.memory = self.memory.loc[self.memory['rank']<=3] # drop solutions whose Pareto rank is above 3
            return True
        return False
    
    
    def convert_to_solution_obj(self, df):
        """
        function to convert solutions in dataframe type to solution object type
        
        Paramters
        --------------------------
        df : dataframe of  solutions
        
        Returns
        ---------------
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
    
    
    def parent_selection_moo(self, pareto_solutions, selection_size):
        """
        Parent selection method for MOO
        
        Paramters
        --------------------------
        pareto_solutions : dataframe of pareto solutions
        selection_size : parent selection size
        
        Returns
        ---------------
        parent : selected parent 
        
        """ 
        parents = []
        pareto_fronts = pareto_solutions.loc[pareto_solutions['rank']==0] # Pareto optimal solution
        pareto_fronts_solution_objects = self.convert_to_solution_obj(pareto_fronts)
        
        non_front_pareto_solutions = pareto_solutions.loc[pareto_solutions['rank'] != 0] # Non pareto optimal solutions
        non_front_pareto_solution_objects = self.convert_to_solution_obj(non_front_pareto_solutions)

        
        size_fittest = int(selection_size/2)
        size_random = size_fittest
        
        if len(pareto_fronts_solution_objects) < size_fittest:
            size_fittest = len(pareto_fronts_solution_objects)
            size_random = selection_size - size_fittest
        
        parents.append(random.sample(pareto_fronts_solution_objects, size_fittest)) # selection of fittest members
        parents.append(random.sample(non_front_pareto_solution_objects, size_random)) # selection of random members
        
        return parents
    
        
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
        
        pareto_solutions, best_solution = get_multi_objective_optimal_sol(population, self.objective_params, self.reschedule, visualize=True, rank=3) 
        
        pareto_solutions_objects = self.convert_to_solution_obj(pareto_solutions)
        next_population.append(pareto_solutions_objects)
        
        size = self.population_size - len(next_population)
        
        if size > 0:
            next_population.append(random.sample(population, size))
        
        return next_population