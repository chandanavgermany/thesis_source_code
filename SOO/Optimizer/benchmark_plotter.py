#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 08:45:00 2020

@author: chandan
"""

import datetime
import statistics
import webbrowser
from pathlib import Path

import plotly.graph_objs as go
from plotly.offline import iplot, plot
from jinja2 import PackageLoader, Environment


template_env = Environment(
    loader=PackageLoader('Optimizer', 'templates'),
    autoescape=True
)

benchmark_template = "benchmark.html"

def iplot_benchmark_results(ts_agent_list=None, ga_agent=None, sa_agent=None):
    """
    function to initiate plots for conducted experiment
    """
    if ts_agent_list is not None and all(ts_agent.benchmark for ts_agent in ts_agent_list):
        best_makespans_per_ts_agent = []
        iterations_per_ts_agent = []
        for ts_agent in ts_agent_list:
            best_makespans_per_ts_agent.append(ts_agent.min_makespan_coordinates[1])
            iterations_per_ts_agent.append(ts_agent.benchmark_iterations)

        # create traces for plots
        makespans_traces, makespans_layout, \
        nh_sizes_traces, nh_sizes_layout, \
        tl_sizes_traces, tl_sizes_layout = _make_tabu_search_traces(ts_agent_list)

        # create plots
        iplot(dict(data=makespans_traces, layout=makespans_layout))
        iplot(dict(data=nh_sizes_traces, layout=nh_sizes_layout))
        iplot(dict(data=tl_sizes_traces, layout=tl_sizes_layout))
        min([ts_agent.best_solution for ts_agent in ts_agent_list]).iplot_gantt_chart(continuous=True)
        print(best_makespans_per_ts_agent)

    if ga_agent is not None and ga_agent.benchmark:
        # create traces for plot
        makespans_traces, makespans_layout = _make_gnetic_algorithm_traces(ga_agent)

        # create plot
        iplot(dict(data=makespans_traces, layout=makespans_layout))
        ga_agent.best_solution.iplot_gantt_chart(continuous=True)
        
    
    if sa_agent is not None and sa_agent.benchmark:
        makespans_traces, makespans_layout = _make_simulated_annealing_algorithm_traces(sa_agent)

        # create plot
        iplot(dict(data=makespans_traces, layout=makespans_layout))
        sa_agent.best_solution.iplot_gantt_chart(continuous=True)        
        
        

def output_benchmark_results(output_dir, ts_agent_list=None, ga_agent=None, sa_agent=None,  title=None, auto_open=True):
 
    if (ts_agent_list is None or not all(ts_agent.benchmark for ts_agent in ts_agent_list)) \
            and (ga_agent is None or not ga_agent.benchmark) and (sa_agent is None or not sa_agent.benchmark):
        raise UserWarning("agent arguments were None or were not ran in benchmark mode.")

    if title is None:
        title = "Benchmark Run {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    output_dir = Path(output_dir)

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    def compute_stats(lst):
        return {
            'min': round(min(lst)),
            'median': round(statistics.median(lst)),
            'max': round(max(lst)),
            'std': round(statistics.stdev(lst)) if len(lst) > 1 else 0,
            'var': round(statistics.variance(lst)) if len(lst) > 1 else 0,
            'mean': round(statistics.mean(lst))
        }

    # tabu search results
    if ts_agent_list is not None and all(ts_agent.benchmark for ts_agent in ts_agent_list):
        _create_ts_plots(ts_agent_list, output_dir)
        ts_result_makespans = []
        ts_initial_makespans = []
        ts_iterations = []
        for ts_agent in ts_agent_list:
            ts_result_makespans.append(ts_agent.best_solution.makespan)
            ts_initial_makespans.append(ts_agent.initial_solution.makespan)
            ts_iterations.append(ts_agent.benchmark_iterations)

        ts_result_makespans_stats = compute_stats(ts_result_makespans)
        ts_initial_makespans_stats = compute_stats(ts_initial_makespans)
        ts_iterations_stats = compute_stats(ts_iterations)

    else:
        ts_result_makespans_stats = None
        ts_initial_makespans_stats = None
        ts_iterations_stats = None


    # genetic algorithm results
    if ga_agent is not None and ga_agent.benchmark:
        _create_ga_plots(ga_agent, output_dir)
        ga_initial_makespans = [sol.makespan for sol in ga_agent.initial_population]
        ga_result_makespans = [sol.makespan for sol in ga_agent.result_population]

        ga_initial_makespans_stats = compute_stats(ga_initial_makespans)
        ga_result_makespans_stats = compute_stats(ga_result_makespans)

    else:
        ga_initial_makespans_stats = None
        ga_result_makespans_stats = None


    # simulated annealing algorithm results
    if sa_agent is not None and sa_agent.benchmark:
        _create_sa_plots(sa_agent, output_dir)
        sa_initial_makespans = [sa_agent.initial_solution.makespan]
        sa_result_makespans = [sa_agent.best_solution.makespan]

        sa_initial_makespans_stats = compute_stats(sa_initial_makespans)
        sa_result_makespans_stats = compute_stats(sa_result_makespans)

    else:
        sa_initial_makespans_stats = None
        sa_result_makespans_stats = None        
    

    # render template
    template = template_env.get_template(benchmark_template)
    rendered_template = template.render(
        title=title,
        ts_agent_list=ts_agent_list,
        ts_initial_makespans_stats=ts_initial_makespans_stats,
        ts_result_makespans_stats=ts_result_makespans_stats,
        iterations_per_ts_agent_stats=ts_iterations_stats,
        output_directory=output_dir.resolve(),
        ga_agent=ga_agent,
        ga_initial_makespans_stats=ga_initial_makespans_stats,
        ga_result_makespans_stats=ga_result_makespans_stats,
        sa_agent=sa_agent,
        sa_initial_makespans_stats=sa_initial_makespans_stats,
        sa_result_makespans_stats=sa_result_makespans_stats,
    )

    # create index.html
    with open(output_dir / 'index.html', 'w') as output_file:
        output_file.write(rendered_template)

    if auto_open:
        webbrowser.open(f'file://{output_dir.resolve()}/index.html')


def _create_ts_plots(ts_agent_list, output_directory):
    """
    create plots for Tabu search 
    """
    # create traces for plots
    makespans_traces, makespans_layout, \
    nh_sizes_traces, nh_sizes_layout, \
    tl_sizes_traces, tl_sizes_layout = _make_tabu_search_traces(ts_agent_list)

    # create plots
    plot(dict(data=makespans_traces, layout=makespans_layout),
         filename=str(output_directory / 'ts_makespans.html'),
         auto_open=False)
    plot(dict(data=nh_sizes_traces, layout=nh_sizes_layout),
         filename=str(output_directory / 'neighborhood_sizes.html'),
         auto_open=False)
    plot(dict(data=tl_sizes_traces, layout=tl_sizes_layout),
         filename=str(output_directory / 'tabu_list_sizes.html'),
         auto_open=False)

    # create schedule
    best_solution = min([ts_agent.best_solution for ts_agent in ts_agent_list])
    best_solution.create_schedule_xlsx_file(str(output_directory / 'ts_schedule'), continuous=True)
    best_solution.create_gantt_chart_html_file(str(output_directory / 'ts_gantt_chart.html'), continuous=True)


def _create_ga_plots(ga_agent, output_directory):
    """
    create plots for Genetic algorithm 
    """

    # create trace for plot
    makespans_traces, makespans_layout = _make_gnetic_algorithm_traces(ga_agent)

    # create plot
    plot(dict(data=makespans_traces, layout=makespans_layout),
         filename=str(output_directory / 'ga_makespans.html'),
         auto_open=False)

    # create schedule
    ga_agent.best_solution.create_schedule_xlsx_file(str(output_directory / 'ga_schedule'), continuous=True)
    ga_agent.best_solution.create_gantt_chart_html_file(str(output_directory / 'ga_gantt_chart.html'), continuous=True)       
        
        
def _create_sa_plots(sa_agent, output_directory):
    """
    create plots for  Simulated Annealing  
    """
    # create trace for plot
    makespans_traces, makespans_layout = _make_simulated_annealing_algorithm_traces(sa_agent)

    # create plot
    plot(dict(data=makespans_traces, layout=makespans_layout),
         filename=str(output_directory / 'sa_makespans.html'),
         auto_open=False)

    # create schedule
    sa_agent.best_solution.create_schedule_xlsx_file(str(output_directory / 'sa_schedule'), continuous=True)
    sa_agent.best_solution.create_gantt_chart_html_file(str(output_directory / 'sa_gantt_chart.html'), continuous=True)      
    
    
def _make_tabu_search_traces(ts_agent_list):
    """
    create plots for tabu search instances
    """
    # create traces for plots
    makespans_traces = [
        go.Scatter(x=[ts_agent.min_makespan_coordinates[0] for ts_agent in ts_agent_list],
                   y=[ts_agent.min_makespan_coordinates[1] for ts_agent in ts_agent_list], mode='markers',
                   name='best makespans')
    ]

    nh_sizes_traces = []
    tl_sizes_traces = []

    for i, ts_agent in enumerate(ts_agent_list):
        x_axis = list(range(ts_agent.benchmark_iterations))
        makespans_traces.append(
            go.Scatter(x=x_axis, y=ts_agent.seed_solution_makespan_v_iter, name=f'TS trace {i}'))
        nh_sizes_traces.append(
            go.Scatter(x=x_axis, y=ts_agent.neighborhood_size_v_iter, name=f'TS trace {i}'))
        tl_sizes_traces.append(go.Scatter(x=x_axis, y=ts_agent.tabu_size_v_iter, name=f'TS trace {i}'))

    # create layouts for plots
    makespans_layout = dict(title='Seed Solution Makespan vs Iteration',
                            xaxis=dict(title='Iteration'),
                            yaxis=dict(title='Makespans (minutes)'))
    nh_sizes_layout = dict(title='Neighborhood size vs Iteration',
                           xaxis=dict(title='Iteration'),
                           yaxis=dict(title='Size of Neighborhood'))
    tl_sizes_layout = dict(title='Tabu list size vs Iteration',
                           xaxis=dict(title='Iteration'),
                           yaxis=dict(title='Size of Tabu list'))

    return makespans_traces, makespans_layout, nh_sizes_traces, nh_sizes_layout, tl_sizes_traces, tl_sizes_layout


def _make_gnetic_algorithm_traces(ga_agent):
    """
    create plots for Genetic algorithm 
    """
    # create traces for plot
    makespans_traces = [
        go.Scatter(x=[ga_agent.min_makespan_coordinates[0]], y=[ga_agent.min_makespan_coordinates[1]],
                   mode='markers',
                   name='best makespan'),
        go.Scatter(x=list(range(ga_agent.benchmark_iterations)), y=ga_agent.best_solution_makespan_v_iter,
                   name='Best makespan trace'),
        go.Scatter(x=list(range(ga_agent.benchmark_iterations)), y=ga_agent.avg_population_makespan_v_iter,
                   name='Avg population makespan')
    ]

    makespans_layout = dict(title='Makespans vs Iterations',
                            xaxis=dict(title='Iteration'),
                            yaxis=dict(title='Makespans (minutes)'))

    return makespans_traces, makespans_layout


def _make_simulated_annealing_algorithm_traces(sa_agent):
    """
    create plots for Simulated annealing algorithm 
    """
    makespans_traces = [
        go.Scatter(x=[sa_agent.min_makespan_coordinates[0]], y=[sa_agent.min_makespan_coordinates[1]],
                   mode='markers',
                   name='best makespan'),
                   
        go.Scatter(x=list(range(sa_agent.benchmark_iterations)), y=sa_agent.seed_solution_makespan_v_iter,
                   name='makespan trace')
    ]

    makespans_layout = dict(title='Makespans vs Iterations',
                            xaxis=dict(title='Iteration'),
                            yaxis=dict(title='Makespans (minutes)'))

    return makespans_traces, makespans_layout 