# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 15:17:57 2021

@author: q514347
"""

class Arc:
    def __init__(self, id, sourceId, destinationId, multiplicity=1):
        self.id = id
        self.sourceId = sourceId
        self.destinationId = destinationId
        self.multiplicity = multiplicity
        self.source = None
        self.destination = None

    def getId(self):
        return self.id

    def getSourceId(self):
        return self.sourceId

    def getDestinationId(self):
        return self.destinationId

    def getMultiplicity(self):
        return self.multiplicity