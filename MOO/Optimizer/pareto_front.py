#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 18:59:06 2021

@author: chandan
"""
import random
import string
import numpy as np
import pandas as pd
from pymoo.factory import get_visualization, get_decision_making, get_decomposition

def get_random_string(length):
    """
    helper function to generate random strings
    """    
    
    letters = string.ascii_lowercase
    result = ''.join(random.choice(letters) for i in range(length))
    return result

def calc_fronts_with_rank(M):
    """
    function to evaluate Pareto rankings 
    
    Paramerters
    -----------------------------
    numpy array of objective values of all solutions
    
    Returns
    -----------------------------
    fronts : All solutions array with ranking
    """    
    
    i_dominates_j = np.all(M[:,None] <= M, axis=-1) & np.any(M[:,None] < M, axis=-1)
    remaining = np.arange(len(M))
    fronts = np.empty(len(M), int)
    frontier_index = 0
    while remaining.size > 0:
        dominated = np.any(i_dominates_j[remaining[:,None], remaining], axis=0)
        fronts[remaining[~dominated]] = frontier_index
        remaining = remaining[dominated]
        frontier_index += 1
    return fronts

## only for 2 objective values at the time
def visualize_sol(pareto_front_sol, objective_list, alg_type, rank=0, reschedule=None): 
# =============================================================================
#     if reschedule:
#         objective_list = ['makespan', 'stability']
#     
# =============================================================================
    
    """
    function to plot pareto solutions in the solution space
    """
    if len(objective_list) > 2:
        objective_list = ['stock_cost', 'tardiness_cost']
        
    pareto_front_sol.to_excel('a_' + str(random.randint(0, 100)) + '.xlsx')
    print(objective_list)
    sol_space = pareto_front_sol[objective_list].to_numpy()
    fronts = pareto_front_sol.loc[pareto_front_sol['rank'] == 0]

    pareto = fronts[objective_list].to_numpy()
    plot = get_visualization("scatter")
    plot.add(sol_space, color="green", marker="x")
    plot.add(pareto, color="red", marker="*")
    plot.show()
    plot.save('Data/plots/' + get_random_string(5) + ' ' + alg_type)
	
	
    
def normalize_objective_values(fronts, objective_list):
    """
    function to normalize objective values to calculate pseudo weights
    
    """
    pareto_fronts_top = fronts[objective_list]
    weights = dict()
    for column in pareto_fronts_top:
        max_val = max(fronts[column])
        min_val = min(fronts[column])
        difference = max_val - min_val
        denominator = (fronts[max] - fronts[column]) / difference
        weights[column] = ((fronts[max] - fronts[column]) / difference) / sum(denominator)
    weights = pd.DataFrame(weights)
    return weights



def get_best_solution(fronts, objective_list, weights, decision_making_method="pseudo-weights"):
    """
    function to find out best solution from Pareto front
    
    Parameters
    ------------------------
    fronts : list of Pareto solutions
    objective_list : list of objective functions
    weights: weights for objective functions
    decision_making_method : decision making method 
    
    Returns
    ------------------------
    best_solution
    """
    
    weights = np.array(weights)
    pareto_fronts_top = fronts[objective_list]
    F = pareto_fronts_top.to_numpy()
    try:
        if decision_making_method == "pseudo-weights":
            best_sol_index, pseudo_weights = get_decision_making("pseudo-weights", weights).do(F, return_pseudo_weights=True)
        else:
            ################ compromise programming #########################
            ################### Achievement Scalarization Function ################################
            best_sol_index = get_decomposition("asf").do(F, weights).min()
            
        best_solution = fronts.loc[fronts.index==best_sol_index]
    except Exception as e:
        #print(str(e))
        best_solution = fronts.loc[fronts.index==0]
    return best_solution




def dominates(memory, new_solution, objective_params, reschedule, rank=3):
    """
    function to find out  Pareto solutions
    """
    objective_list = list(objective_params.keys())
    
    if not reschedule:
        objective_list = objective_list[:-1]
    
    new_solution_df = pd.DataFrame([new_solution.as_dict()])
    df = pd.concat([memory, new_solution_df])
    objective_values = df[objective_list].to_numpy()
    pareto_fronts = pd.DataFrame(calc_fronts_with_rank(objective_values))
    return (pareto_fronts.iloc[-1][0] <= rank)


def dominates_2(new_solution, best_solution, objective_params, reschedule):
    """
    function to find if a new solution dominates best solution
    """
    objective_list = list(objective_params.keys())
    if not reschedule:
        objective_list = objective_list[:-1]
    
    new_solution_df = pd.DataFrame([new_solution.as_dict()])
    best_solution_df =  pd.DataFrame([best_solution.as_dict()])
    df = pd.concat([new_solution_df, best_solution_df])
    objective_values = df[objective_list].to_numpy()

    fronts = pd.DataFrame(calc_fronts_with_rank(objective_values))
    return (fronts.iloc[0][0] < fronts.iloc[0][0]) # if new solution dominates current best
    
    
    
    
def get_multi_objective_optimal_sol(population, objective_params, reschedule, alg_type="genetic", visualize=False, rank=0):
    
    """
    function to evaluate Pareto ranking, Pareto fronts and to obtain best solution
    
    Parameters
    ---------------------------
    population : list of solutions
    objective_params : objective functions with weights
    reschedule : reschedule flag
    
    Returns
    ---------------------------
    fronts :  solutions with Pareto ranking
    best_solution
    """
    
    objective_list = list(objective_params.keys())
    weights = list(objective_params.values())
    
    if not reschedule:
        objective_list = objective_list[:-1]
        weights = weights[:-1]
    
    population_df = pd.DataFrame([x.as_dict() for x in population])
    objective_values = population_df[objective_list].to_numpy()
    pareto_fronts = pd.DataFrame(calc_fronts_with_rank(objective_values))
    pareto_fronts = pareto_fronts.rename(columns={0: 'rank'})
    pareto_front_sol = pd.concat([population_df, pareto_fronts], axis=1)
    
    for column in objective_list:
        pareto_front_sol = pareto_front_sol.loc[pareto_front_sol[column] >= 0]
    
    if visualize:
        visualize_sol(pareto_front_sol, objective_list, alg_type, rank, reschedule)
    fronts = pareto_front_sol.loc[pareto_front_sol['rank'] == 0]
    
    for i in range(1, rank+1):
        fronts = pd.concat([fronts, pareto_front_sol.loc[pareto_front_sol['rank'] == i]])

    fronts.reset_index(drop=True, inplace=True)
    best_solution = get_best_solution(fronts, objective_list, weights)
    return fronts, best_solution