# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 15:17:26 2021

@author: q514347
"""

class Transition:
    def __init__(self, transition_id, transition_label):
        self.transition_id = transition_id
        self.transition_label = transition_label
        self.inputs = dict()
        self.outputs = dict()
        self.input_places_id_list = list()
        self.output_places_id_list = list()
        
    def getId(self):
        return self.transition_id
    
    def getLabel(self):
        return self.transition_label
    
    def update_inputs(self, input_place):
        self.inputs[input_place.place_label] = input_place
        self.input_places_id_list.append(input_place.place_id)
        
    def update_outputs(self, output_place):
        self.outputs[output_place.place_label] = output_place
        self.output_places_id_list.append(output_place.place_id)
      
    def fire(self, source_label, destination_label, pieces):
        source = self.inputs[source_label]
        destination = self.outputs[destination_label]

        if source is not None and destination is not None:
            if destination.place_type == "machine":
                destination_status = destination.place_performer.get_machine_status()
                if destination_status == "available":
                    source.pop_token()
                    destination.push_token()
                    print(self.transition_label + " fired !! ")
                    print(source_label + ' -> ' + destination_label)
                    return True, destination_status
                else:
                    print("Failed to fire -> Destination - " + destination.place_label + ' is ' + destination_status)
                    return False, destination_status
            
            elif destination.place_type == "stock":
                if destination.place_performer.deposit_stock(pieces):
                    print(self.transition_label + " fired !! ")
                    print(source_label + ' -> ' + destination_label)
                    source.pop_token()
                    destination.push_token()
                    return True, 'deposited'
                else:
                    return False, "Stock_over_limit"

            else:
                return True, 'error'
        else:
            print('error')