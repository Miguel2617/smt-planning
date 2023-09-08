import copy

from rdflib import Graph
from z3 import Implies, Not

from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary

def get_real_variable_constraints(graph: Graph, capability_dict: CapabilityDictionary, property_dictionary: PropertyDictionary, happenings: int, event_bound: int):
    
    # get all properties influenced by capability effect
    query_props_effected = """
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
        PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
        SELECT ?cap ?de WHERE { 
            ?cap a CaSk:ProvidedCapability;
                ^CSS:requiresCapability ?process.
            ?process VDI3682:hasOutput ?out.
            ?out VDI3682:isCharacterizedBy ?prop.
            ?prop ^DINEN61360:has_Instance_Description ?de.  
        } """
    
    # get all properties that are not influenced by capability effect
    query_props_not_effected = """
		PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
		PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
		PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
		PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
		SELECT ?cap ?de WHERE { 
			?cap a CaSk:ProvidedCapability;
				^CSS:requiresCapability ?process.
			?process VDI3682:hasInput ?in.
			?in VDI3682:isCharacterizedBy ?prop.
			?prop ^DINEN61360:has_Instance_Description ?de.
			FILTER NOT EXISTS {
				?process VDI3682:hasOutput ?out.
				?out VDI3682:isCharacterizedBy ?out_prop.
				?out_prop ^DINEN61360:has_Instance_Description ?de.
			}
		} """
	
    results = graph.query(query_props_effected) 
    constraints = []
    for happening in range(happenings):
        for row in results:
            currentCap = capability_dict.getCapabilityVariableByIriAndHappening(row.cap, happening) # type: ignore
            prop_start = property_dictionary.getPropertyVariable(row.de, 0, happening) # type: ignore
            prop_end = property_dictionary.getPropertyVariable(row.de, 1, happening) # type: ignore
            constraint = Implies(Not(currentCap), prop_end == prop_start)
            constraints.append(constraint)
            
    results = graph.query(query_props_not_effected) 
    for happening in range(happenings):
        for row in results:
            prop_start = property_dictionary.getPropertyVariable(row.de, 0, happening) # type: ignore
            prop_end = property_dictionary.getPropertyVariable(row.de, 1, happening) # type: ignore
            constraint = prop_end == prop_start
            constraints.append(constraint)

    return constraints