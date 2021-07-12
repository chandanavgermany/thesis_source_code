# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 14:40:45 2021

@author: Q514347
"""
import math
import random

def get_idle_time_for_machine_breakdown(machine_threshold_list, machine_avg_process_list, machine_repair_duration_list,
                                        machine_id, machine_makespan, last_repair_time, no_idle_time_introduced):
    
    """
    function to insert buffer time for the schedule based on breakdown probability
    
    Parameters
    -----------------------
    machine_threshold_list : dictionary of every machine's threshold value
    machine_avg_process_list : dictionary of every machine's avg process value
    machine_repair_duration_list : dictionary of every machine's repair duration
    machine: id of the machine
    machine_makespan : makespan of the machine with id 'machine_id'
    last_repair_time : last repair time of the machine
    no_idle_time_introduced : number of idle time that has been introduced

    Returns
    ----------------------
    idle_time : idle time or buffer time of machine
    last_repair_time : last repair time of the machine
    no_idle_time_introduced : number of idle time that has been introduced
    """
    e = math.exp
    idle_time = 0
    if machine_makespan != 0 and machine_makespan != last_repair_time:
        machine_threshold = machine_threshold_list[machine_id]
        machine_avg_process = machine_avg_process_list[machine_id]
        probability_of_machine_failure = 1 - e(-(machine_makespan - last_repair_time - no_idle_time_introduced)/machine_avg_process)

        if probability_of_machine_failure > machine_threshold and random.random()  > machine_threshold:
            last_repair_time = machine_makespan
            no_idle_time_introduced += 1

            return machine_repair_duration_list[machine_id], last_repair_time, no_idle_time_introduced
    return idle_time, last_repair_time, no_idle_time_introduced