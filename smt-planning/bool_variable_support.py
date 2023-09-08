from rdflib import Graph
from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary
from typing import List
from z3 import Implies, Not

def getPropositionSupports(property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
	supports = []
	for happening in range(happenings)[2:]:
		for property in property_dictionary.properties.values():
			property_current_happening_start = property.states[0][happening]
			property_last_happening_end = property.states[event_bound + 1][happening-1]
			
			# Track change between happenings, so that no random change is possible
			# 1: If a property is set at start of a happening, it must have been set at the last happening's end
			support = Implies(property_current_happening_start, property_last_happening_end)
			supports.append(support)
			
			# 1: If a property is NOT set at start of a happening, it must NOT have been set at the last happening's end
			support_negated = Implies(Not(property_current_happening_start), Not(property_last_happening_end))
			supports.append(support_negated)
	return supports