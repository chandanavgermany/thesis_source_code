# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 08:50:03 2021

@author: q514347
"""
import json
import time
import random
import http.client as client
from datetime import datetime as dt
from logger import writeLogFile
from simulation_utility import is_process_finished, is_production_status_changed

class Schedule:
    def __init__(self, petri_net, schedule, schedule_path, product_name, job):
        self.petri_net = petri_net
        self.schedule = schedule
        self.schedule_path = schedule_path
        self.product_name = product_name
        self.remaining_path = schedule_path
        self.job = job
        
    def update_temp_schedule_log(self, operation, remaining_pieces, finished_pieces):
        c = client.HTTPConnection('localhost', 8080)
        data = {'prod_name': self.product_name, 'operation': str(operation), 
                'remaining_pieces': str(remaining_pieces), 'finished_pieces': str(finished_pieces)}
        c.request('POST', '/operation_status/', json.dumps(data))
        result = c.getresponse().read()
        c.close()
        data_string = result.decode('utf-8')
        data_dict = json.loads(data_string)
        return data_dict['result']
    
    def update_product_performance_log(self, operation_place_label, started_at, left_at, 
                                       operation=-1, place_type='initial', machine=-1):
        c = client.HTTPConnection('localhost', 8080)
        data = {'prod_name': self.product_name, 'operation_place': operation_place_label, 
                'started_at': started_at, 'left_at': left_at, 'job': str(self.job), 'operation': str(operation),
                'place_type': place_type, 'machine': str(machine)}
        c.request('POST', '/product_performance_status/', json.dumps(data))
        result = c.getresponse().read()
        c.close()
        data_string = result.decode('utf-8')
        data_dict = json.loads(data_string)
        return data_dict['result']
        
    def check_for_token(self, place):
        if place.tokens <= 0:
            writeLogFile(self.product_name + '.txt', "Token not found to process - " + place.place_label)
            raise Exception("Token not found at process - " + place.place_label)
        else: 
            return None
        
    def fire_machine(self, transition, place, next_place_label, machine_id, pieces, process_interruption_event):
        process_data = self.schedule.loc[self.schedule['machine_name']==machine_id] 
        process_start_time = process_data.iloc[0]['runtime_start'] 
        
        if isinstance(process_start_time, str):
            process_start_time = dt.strptime(process_start_time, '%Y-%m-%d %H:%M:%S')
        print(process_start_time)
        while True:  
            if is_production_status_changed():
                process_interruption_event.set()
                break
            
            if process_start_time <= dt.now():
                result, next_place_status = transition.fire(place.place_label, next_place_label, pieces)
                print(next_place_label + ' - ' + next_place_status)
                if not result:
                    if next_place_status == 'broken':
                        writeLogFile(self.product_name + '.txt', next_place_label + " broken can't proceed with the job")
                       # multi_processing_queue.put(pickle.dumps(self, protocol=-1))
                        process_interruption_event.set()
                        break
                        #raise Exception(next_place_label + " broken can't proceed with the job")
                    elif next_place_status == 'busy':
                        writeLogFile(self.product_name + '.txt', next_place_label + ' Busy !!')
                        time.sleep(random.randint(0, 5))
                        continue
                    else:
                        break
                else:
                    writeLogFile(self.product_name + '.txt', place.place_label + ' -> ' + next_place_label + ' fire sucessfull !!')
                    break
            else:
                time.sleep(random.randint(0, 15))
        
    def fire_stock(self, transition, place, next_place_label, pieces, process_interruption_event):
        while True:
            result, next_place_status = transition.fire(place.place_label, next_place_label, pieces)
            print(next_place_label + ' - ' + next_place_status)
            if not result:
                 writeLogFile(self.product_name + '.txt', next_place_label + ' ' + next_place_status)
                 process_interruption_event.set()
                 break
            else:
                writeLogFile(self.product_name + '.txt', place.place_label + ' -> ' + next_place_label + ' fire sucessfull !!')
                writeLogFile(self.product_name + '.txt', str(pieces) + ' has been deposited at ' + next_place_label)
                break
        
    def fire_transition(self, place, count, process_interruption_event, pieces):
        transition_label = self.schedule_path[count+1][1]
        transition = self.petri_net.getTransitionByLabel(transition_label)
        next_place_label = self.schedule_path[count+2][1]
        next_place = self.petri_net.getPlaceByLabel(next_place_label)
        print(next_place_label)
        if next_place.place_type == 'machine':            
           machine_id = next_place.place_performer.machine_id
           self.fire_machine(transition, place, next_place_label, machine_id, pieces, process_interruption_event)
        else: # Stock
           self.fire_stock(transition, place, next_place_label, pieces, process_interruption_event)
        return True
    
    def is_stop_execution(self, process_interruption_event):
        if is_production_status_changed():
            process_interruption_event.set()
            return True
        return False
    
    def start(self, process_interruption_event, multi_processing_queue=None):
        try:
            count = 0
            for item in self.remaining_path:
                if self.is_stop_execution(process_interruption_event): ### If a machine gets broken or machine gets repaired - reschedule
                    return 
                
                path_position_type = item[0]
                path_position_label = item[1]
                #path_position_performer_id = item[2]
                operation_num = -1
                machine = -1
                
                if path_position_type == "place":
                    time.sleep(random.randint(0,5))
                    place = self.petri_net.getPlaceByLabel(path_position_label)
                    if place is None:
                        raise Exception("Place not found")
                        writeLogFile(self.product_name + '.txt', path_position_label + ' - Place not found')
                    else:
                       # self.update_product_performance_log(place.place_label, str(dt.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')), '', place_type=place.place_type, operation=operation_num, machine=machine)
                        #self.check_for_token(place)
                        writeLogFile(self.product_name + '.txt', path_position_label + ' - processing on !!')
                        ########################## INITIAL CASE ########################################   
                        if place.place_type == 'initial':
                            t_start = time.time()
                            process_start = dt.fromtimestamp(t_start).strftime('%Y-%m-%d %H:%M:%S')
                            self.fire_transition(place, count, process_interruption_event, 0)
                        
                        ####################### MACHINE PROCESS #######################################
                        elif place.place_type == "machine":
                            while True:
                                if place.place_performer.get_machine_status() == "available":
                                    t_start = time.time()
                                    process_start = dt.fromtimestamp(t_start).strftime('%Y-%m-%d %H:%M:%S')
                                    process_data = self.schedule.loc[self.schedule['machine_name']==place.place_performer.machine_id] #path_position_performer_id    
                                    process_time = process_data.iloc[0]['runtime_duration']
                                    finished_pieces = process_data.iloc[0]['finished_pieces']
                                    remaining_pieces = process_data.iloc[0]['remaining_pieces']
                                    machine_takt_time = process_data.iloc[0]['takt_time']
                                    operation = process_data.iloc[0]['operation']
                                    operation_num = operation
                                    machine = process_data.iloc[0]['machine']
                                    place.place_performer.set_machine_status('busy')
                                    
                                    while process_time > 0:
                                        if place.place_performer.get_machine_status() == "broken" and is_production_status_changed():
                                            process_interruption_event.set()
                                            return 
                                        if process_time >= 60:
                                            process_time -= 60
                                            time.sleep(60)
                                            finished_pieces += machine_takt_time
                                            remaining_pieces -= machine_takt_time
                                            if remaining_pieces < 0:
                                                remaining_pieces = 0
                                        else:
                                            time.sleep(process_time)
                                            process_time = 0
                                            finished_pieces += remaining_pieces
                                            remaining_pieces = 0        
                                        self.update_temp_schedule_log(operation, remaining_pieces, finished_pieces)
                                    self.fire_transition(place, count, process_interruption_event, finished_pieces)
                                    
                                    if is_production_status_changed():
                                         process_interruption_event.set()
                                         return 
                                    place.place_performer.set_machine_status('available')
                                    break
                                else:
                                    time.sleep(random.randint(0,10))
                     
                        ###################### STOCK DEPOSIT AND WITHDRAW ###############################
                        
                        elif place.place_type == "stock":
                            t_start = time.time()
                            process_start = dt.fromtimestamp(t_start).strftime('%Y-%m-%d %H:%M:%S')
                            stock_type = place.place_performer.stock_type
                            if stock_type == 'F':
                                print(self.product_name + ' -> product execution done')
                                writeLogFile(self.product_name + '.txt', path_position_label + ' - process finished !!')
                                process_end = dt.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                                self.update_product_performance_log(place.place_label, str(process_start),
                                                                    str(process_end), place_type=place.place_type,
                                                                    operation=operation_num)
                                break
                            elif stock_type == 'I':
                                next_place_performer_id = self.schedule_path[count+2][2]
                                process_data = self.schedule.loc[self.schedule['machine_name']==next_place_performer_id] 
                                pieces = process_data.iloc[0]['remaining_pieces']
                                result, status = place.place_performer.withdraw_stock(pieces)
                                if not result:
                                    raise Exception(status)                                    
                                self.fire_transition(place, count, process_interruption_event, 0)
                        writeLogFile(self.product_name + '.txt', path_position_label + ' - process finished !!')
                        t_end = time.time()
                        process_end = dt.fromtimestamp(t_end).strftime('%Y-%m-%d %H:%M:%S')
                        self.update_product_performance_log(place.place_label, str(process_start), str(process_end),
                                                            place_type=place.place_type, operation=operation_num,
                                                            machine=machine)
                    count += 2
                       
        except Exception as e:
            print(str(e))
        
        if is_process_finished():
           # multi_processing_queue.put(pickle.dumps(self, protocol=-1))
           process_interruption_event.set()
        return 