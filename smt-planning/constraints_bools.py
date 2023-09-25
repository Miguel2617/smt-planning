from rdflib import Graph
from z3 import Implies, Not, Or
from typing import List

from dicts.CapabilityDictionary import CapabilityDictionary
from dicts.PropertyDictionary import PropertyDictionary

def get_bool_constraints(graph: Graph, capability_dict: CapabilityDictionary, property_dictionary: PropertyDictionary, happenings: int, event_bound: int) -> List:
    
    # get all properties influenced by capability effect
    query_props_effected = """
    PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
    PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
    PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
    PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?de ?val (GROUP_CONCAT(?cap; separator=", ") as ?caps) WHERE { 
        ?cap a CaSk:ProvidedCapability;
            ^CSS:requiresCapability ?process.
        ?process VDI3682:hasOutput ?out.
        ?out VDI3682:isCharacterizedBy ?id.
        ?id ^DINEN61360:has_Instance_Description ?de;
            a DINEN61360:Boolean; 
            DINEN61360:Value ?val. 
    }
    GROUP by ?de ?val """
    
    # get all properties that are not influenced by capability effect
    query_props_not_effected = """
        PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        PREFIX CSS: <http://www.w3id.org/hsu-aut/css#>
        PREFIX CaSk: <http://www.w3id.org/hsu-aut/cask#>
        PREFIX VDI3682: <http://www.w3id.org/hsu-aut/VDI3682#>
        SELECT ?de WHERE { 
            ?cap a CaSk:ProvidedCapability;
                ^CSS:requiresCapability ?process.
            ?process VDI3682:hasInput ?in.
            ?in VDI3682:isCharacterizedBy ?id.
            ?id ^DINEN61360:has_Instance_Description ?de;
                a DINEN61360:Boolean.
            FILTER NOT EXISTS {
                ?process VDI3682:hasOutput ?out.
                ?out VDI3682:isCharacterizedBy ?out_id.
                ?out_id ^DINEN61360:has_Instance_Description ?de.
            }
        } """
	
    results = graph.query(query_props_effected) 
    constraints = []
    for happening in range(happenings):
        previous_property = None
        previous_value = None
        previous_prop_start = None
        previous_prop_end = None
        i = 0
        number_of_rows = len(results)
        for row in results:
            i += 1
            value = str(row.val)                                                        # type: ignore
            caps_result = row.caps.split(', ')                                          # type: ignore 
            caps = []
            for cap in caps_result:                                                     # type: ignore
                currentCap = capability_dict.getCapabilityVariableByIriAndHappening(cap, happening) # type: ignore
                caps.append(currentCap)
            prop_start = property_dictionary.get_provided_property(row.de, happening, 0) # type: ignore
            prop_end = property_dictionary.get_provided_property(row.de, happening, 1) # type: ignore
            
            if value == "true":
                constraint_1 = Implies(prop_end, Or(prop_start, *caps))
                constraints.append(constraint_1)
            elif value == "false":
                caps_constraint = [Not(cap) for cap in caps] 
                constraint_2 = Implies(Not(prop_end), Or(Not(prop_start), *caps_constraint))
                constraints.append(constraint_2)

            if previous_property == row.de: continue                                       # type: ignore
            if previous_value == "true":
                constraint_2 = Implies(Not(previous_prop_end), Not(previous_prop_start))
                constraints.append(constraint_2)

            elif previous_value == "false":
                constraint_1 = Implies(previous_prop_end, previous_prop_start)
                constraints.append(constraint_1)
            
            if i == number_of_rows:
                if value == "true":
                    constraint_2 = Implies(Not(prop_end), Not(prop_start))
                    constraints.append(constraint_2)

                elif value == "false":
                    constraint_1 = Implies(prop_end, prop_start)
                    constraints.append(constraint_1)

            previous_property = row.de                                                   # type: ignore 
            previous_value = str(row.val)                                                # type: ignore
            previous_prop_end = prop_end
            previous_prop_start = prop_start
            

    results = graph.query(query_props_not_effected) 
    for happening in range(happenings):
        for row in results:
            prop_start = property_dictionary.get_provided_property(row.de, happening, 0) # type: ignore
            prop_end = property_dictionary.get_provided_property(row.de, happening, 1) # type: ignore
            constraint_1 = Implies(prop_end, prop_start)
            constraint_2 = Implies(Not(prop_end), Not(prop_start))
            constraints.append(constraint_1)
            constraints.append(constraint_2)

    return constraints