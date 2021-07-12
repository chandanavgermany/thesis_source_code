# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 08:18:41 2021
@author: Chandan
"""
import json
import http.client as client


def get_machine_data(machine_id):
    c = client.HTTPConnection('localhost', 8080)
    c.request('GET', '/machine/'+str(machine_id))
    result = c.getresponse().read()
    c.close()
    data_string = result.decode('utf-8')
    data_dict = json.loads(data_string)
    return data_dict['result'][0]

def set_machine_status(machine_id, status):
    data = {'machine': machine_id, 'status': status}
    c = client.HTTPConnection('localhost', 8080)
    c.request('POST', '/set_machine_status', json.dumps(data))
    #print(c.getresponse().read())
    c.close()


class Machine:    
    def __init__(self, machine_id, machine_takt_time=0, machine_status="available"):
        ''' machine_status - available, busy, broken, repair '''
        self.machine_id = machine_id
        self.machine_takt_time = machine_takt_time
        self.machine_status = machine_status
        
    def get_machine_status(self):
        #return self.machine_status
        return get_machine_data(self.machine_id)[2]
    
    def set_machine_status(self, machine_status="available"):
        ''' Machine status - available, busy, broken '''
        self.machine_status = machine_status
        set_machine_status(self.machine_id, machine_status)
            
    def as_dict(self):
        return {'machine_id': self.machine_id, 'machine_status': self.machine_status}
    
class MachineSet:
    def __init__(self):
        self.machines = []
    
    def addMachine(self, machine):
        self.machines.append(machine)
    
    def removeMachine(self, machine):
        self.machines.remove(machine)
        
    def get_machine_by_id(self, machine_id):
        for machine_obj in self.machines:
            if machine_obj.machine_id == machine_id:
                return machine_obj
        return None