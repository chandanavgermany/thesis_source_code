# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 09:09:44 2021

@author: Q514347
"""
import os
import collections
import numpy as np
import xml.etree.ElementTree as et    

from Petri_Net.arc import Arc
from Petri_Net.place import Place
from Petri_Net.transition import Transition

Initial = collections.namedtuple('Initial', 'performer_id product')

class PetriNet:
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []
        self.place_performer_ids = list()
        self.input_transition_place_pairs = list()
        self.output_transition_place_pairs = list()
        self.inputMatrix = None
        self.outputMatrix = None
    
    def addPlacePerformerId(self, place_label, performer_id):
        place_performer = dict()
        place_performer['place_label'] = place_label
        place_performer['performer_id'] = performer_id
        self.place_performer_ids.append(place_performer)
        
    def addPlace(self, place):
        self.places.append(place)

    def addTransition(self, transition):
        self.transitions.append(transition)

    def setPlaces(self, places):
        self.places = places

    def setTransitions(self, transitions):
        self.transitions = transitions

    def addArc(self, arc):
        self.arcs.append(arc)

    def getPlaces(self):
        return self.places

    def getTransitions(self):
        return self.transitions

    def getArcs(self):
        return self.arcs

    def getPlaceById(self, id):
        for obj in self.getPlaces():
            if obj.getId() == id:
                return obj
        return None

    def getTransitionById(self, id):
        for obj in self.getTransitions():
            if obj.getId() == id:
                return obj
        return None

    def getPlaceByLabel(self, label):
        for obj in self.getPlaces():
            if obj.getLabel() == label:
                return obj
        return None

    def getTransitionByLabel(self, label):
        for obj in self.getTransitions():
            if obj.getLabel() == label:
                return obj
        return None
    
    def generate_input_output_matrix(self):
        nRows = len(self.getPlaces())
        nColumns = len(self.getTransitions())
        
        inputMatrix = np.array([[0 for i in range(nColumns)] for j in range(nRows)])
        outputMatrix = np.array([[0 for i in range(nColumns)] for j in range(nRows)])
        
        for arc in self.getArcs():
            sourceId = arc.getSourceId()
            destinationId = arc.getDestinationId()
            source = None
            destination = None
        
            if (self.getPlaceById(sourceId) is not None) and (self.getTransitionById(destinationId) is not None):
                source = self.getPlaceById(sourceId)
                destination = self.getTransitionById(destinationId)
                destination.update_inputs(source)
                
            elif (self.getTransitionById(sourceId) is not None) and (self.getPlaceById(destinationId) is not None):
                source = self.getTransitionById(sourceId)
                destination = self.getPlaceById(destinationId)
                source.update_outputs(destination)
        
            sourceIdInNetList = None
            destinationIdInNetList = None
        
            if type(source) == Place:
                sourceIdInNetList = self.getPlaces().index(source)
                destinationIdInNetList = self.getTransitions().index(destination)
                inputMatrix[sourceIdInNetList, destinationIdInNetList] = arc.getMultiplicity()
        
            if type(source) == Transition:
                sourceIdInNetList = self.getTransitions().index(source)
                destinationIdInNetList = self.getPlaces().index(destination)
                outputMatrix[destinationIdInNetList, sourceIdInNetList] = arc.getMultiplicity()
        self.inputMatrix = inputMatrix
        self.outputMatrix = outputMatrix
    
    def printTransitionPreset(self, transition):
        transitionIndex = self.getTransitions().index(transition)
        inputColumn = self.inputMatrix[:, transitionIndex]

        placeList = []
        for place in self.getPlaces():
            placeIndex = self.getPlaces().index(place)
            if inputColumn[placeIndex] > 0:
                placeList.append(place.getLabel())
        print("•", transition.getLabel(), end=" = {", sep="")
        print(", ".join(placeList), end="}\n")
        input_tr_pl_pair = dict()
        input_tr_pl_pair['transition_label'] = transition.getLabel()
        input_tr_pl_pair['input_place_list'] = placeList
        self.input_transition_place_pairs.append(input_tr_pl_pair)
        

    def printTransitionPostset(self, transition):
        transitionIndex = self.getTransitions().index(transition)
        inputColumn = self.outputMatrix[:, transitionIndex]

        placeList = []
        for place in self.getPlaces():
            placeIndex = self.getPlaces().index(place)
            if inputColumn[placeIndex] > 0:
                placeList.append(place.getLabel())
        print(transition.getLabel(), "•", end=" = {", sep="")
        print(", ".join(placeList), end="}\n")
        output_tr_pl_pair = dict()
        output_tr_pl_pair['transition_label'] = transition.getLabel()
        output_tr_pl_pair['output_place_list'] = placeList
        self.output_transition_place_pairs.append(output_tr_pl_pair)

    def printAllTransitionsPresets(self):
        print("\nTransitions presets:")
        for t in self.getTransitions():
            self.printTransitionPreset(t)

    def printAllTransitionsPostsets(self):
        print("\nTransitions postsets:")
        for t in self.getTransitions():
            self.printTransitionPostset(t)
    
    def getPlacePerformerIds(self):
        return self.place_performer_ids


def get_petri_net_model(file_name, machine_set, stock_set):
    try:
        if os.path.exists(file_name) and os.path.isfile(file_name):
            print("Parsing file " + file_name + " to petri net model")
        else:
            raise Exception("Error: Can't import the file "+ file_name)
    except Exception as e:
        print(str(e))
        return None
         
    tree = et.parse(file_name)
    root = tree.getroot()
    prefix = "subnet/" if root.find("subnet") is not None else ""
    petri_net = PetriNet()
 
    '''  PLACE  '''
    for type_tag in root.findall(prefix + "place"):
        id = type_tag.find('id').text
        label = type_tag.find('label').text
        data = label.split('-')
        try:
           if len(data) != 3:
            raise Exception("Place should contain all info")
        except Exception as e:
            print(str(e))
            return None
        
        place_label = data[0]
        place_type = data[1]
        if place_type == 'I':
            place_type = "initial"
        elif place_type == 'M':
            place_type = 'machine'
        elif place_type == 'S':
            place_type = "stock"
        else:
            print("Error : improper place type !!")
            return None
        
        place_performer_id = data[2]
        petri_net.addPlacePerformerId(place_label, place_performer_id)
        
        if place_type == 'initial':
            performer = Initial(performer_id=place_performer_id, product=place_label)
        elif place_type == 'machine':
            performer = machine_set.get_machine_by_id(place_performer_id)
            if performer is None:
                print('Machine ' + place_performer_id + ' not available in the pool')
                return None
        else:
            performer = stock_set.get_stock_by_id(place_performer_id)
            if performer is None:
                print('Stock ' + place_performer_id + ' not available in the pool')
                return None
        
        tokens = int(type_tag.find('tokens').text)
       #static = True if type_tag.find('isStatice').text == "true" else False
        place = Place(id, place_label, place_type, performer, tokens)        
        petri_net.addPlace(place)
    
    '''  TRANSITION  '''
    for type_tag in root.findall(prefix + "transition"):
        id = type_tag.find('id').text
        label = type_tag.find('label').text
        petri_net.addTransition(Transition(id, label))

    '''  ARC  '''
    for type_tag in root.findall(prefix + "arc"):
        id = type_tag.find('id').text
        sourceId = type_tag.find('sourceId').text
        destinationId = type_tag.find('destinationId').text
        multiplicity = type_tag.find('multiplicity').text
        petri_net.addArc(Arc(id, sourceId, destinationId, multiplicity))
    
    ''' generating input and output matrix '''
    petri_net.generate_input_output_matrix()
    # transition presets/postsets
    petri_net.printAllTransitionsPresets()
    petri_net.printAllTransitionsPostsets()
    
    print("Petri net parsing successfull !!!!")
    print()
    print()
    
    return petri_net