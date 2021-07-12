# -*- coding: utf-8 -*-
"""
Created on Thu Mar 25 10:44:32 2021

@author: Q514347
"""

import argparse

def get_args():
    parser = argparse.ArgumentParser('Production simulation using meta-heuristics')
    parser.add_argument("--machine_info_file_name", type=str, default='Data/machine_r.xlsx',
                        help="contains all machine's runtime, repair-tme related info")
    parser.add_argument("--job_operation_info_file_name", type=str, default='Data/jo_shop_armin.xlsx',
                        help="contanins job shop problem info")
    parser.add_argument("--petri_net_file", type=str, default='Data/newmodel.xml.pflow',
                        help="pnml file which was exported from online petri net modeler")
    parser.add_argument("--schedule_type", type=str, default='normal',
                        help="Define schedule type should be either of normal or robust")
    parser.add_argument("--reschedule_method", type=str, default='right_shift',
                        help="Define reschedule method should be from {right_shift, partial, complete}")
    parser.add_argument('--need_new_schedule', type=bool, default=True,
                        help="While doing rescheduling experiments")
    parser.add_argument('--alg', type=str, default='hybrid',
                        help="hybrid, nsga")
    return parser.parse_args('')