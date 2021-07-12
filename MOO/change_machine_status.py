# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 08:10:47 2021

@author: q514347
"""
    
import time
from simulation_utility import production_status, machine_status, delete_production_status

def update_broken_status(machine_id, status, prod_status, update_prod_status=False):
    machine_status(machine_id, status)
    delete_production_status()
    if update_prod_status:
        production_status(prod_status)
    

if __name__ == '__main__':
    breakdown_minute = 0
    repair_minute = 2
    machine_id = 'M2'
    status = 'available'
    prod_status = 'broken'
    
    ########################## wait for breakdown ########################
    time.sleep(breakdown_minute * 60)
    print('breakdown', machine_id, status, prod_status)
    update_broken_status(machine_id, status, prod_status, True)             
    
    ########################### wait for repair #######################
# =============================================================================
#     time.sleep(repair_minute * 60)
#     status = 'available'
#     prod_status = 'repaired'
#     print('repaired', machine_id, status, prod_status)
#     update_broken_status(machine_id, status, prod_status, True)
# 
# =============================================================================
