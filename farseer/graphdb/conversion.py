"""
This module contains utility functions for various conversions between data
"""

from farseer.kind.knd import Kind, Measure, Phenomenon, ObjectType, Variable, ObjectTypeRelation, DatasetDesign, Quantity, Constant, Operator, Level, Unit, Representation, CodeList, MeasureRepresentationMapping, ObjectTypeInclusion, DatasetDescription, PhenomenonMeasureMapping
import json
import pprint
from farseer.domainmodel.dm import dm
import time
from neo4j.graph import Path
from farseer.graphdb.dbconfig import one_type, one_name, types, elements
from neo4j.work.result import Result


def dm_to_dmdict(domainmodel):
    dmdict = {}
    for kind in domainmodel:
        name = kind.name
        dmdict.update({name: kind})
    return dmdict

def kind_to_dict(kind: Kind) -> dict:
    """Store information needed to be built in dictionary.
    Args:
        kind (Kind): Kind object, to be stored in graph database

    Returns:
        dict: Dictionary containing all information needed to build kind object.
    """

    name = kind.name
    sort = kind.__class__.__name__
    kind_dict = {"kind": sort, "name": name}

    if sort in types:
        kind_dict = kind_dict
    elif sort in elements:
        codomain = kind_to_dict(kind.codomain)
        if sort != "Constant":
            domain = kind_to_dict(kind.domain)
        else:
            domain = {"kind": one_type, "name": one_name}
        kind_dict.update({"domain": domain, "codomain": codomain})
    #print("Kind dict for", kind, ":", kind_dict)
    return kind_dict

def kind_to_json(kind: Kind) -> str:
    kind_dict = kind_to_dict(kind)

    kind_as_json = json.dumps(kind_dict)
    return kind_as_json

def remove_unicode_chars(string):
    string = string.replace("\\u00a0", "")
    return string

def json_to_kind(jsonstring: str) -> Kind:
    """Function for building kind from JSON as returned by kind_to_json()

    Args:
        jsonstring (string): Information needed to build kind object, contained in JSON format

    Returns:
        Kind: Kind object
    """
    jsonstring = remove_unicode_chars(jsonstring)
    kind_dict = json.loads(jsonstring)
    sort = kind_dict['kind']
    name = kind_dict['name']
    kind = None
    if sort in types:
        if sort == "ObjectType":
            kind = ObjectType(name=name)
        elif sort == "Phenomenom":
            kind = Phenomenon(name=name)
        elif sort == "Quantity":
            kind = Quantity(name=name)
        elif sort == "Measure":
            kind = Measure(name=name)
        elif sort == "Unit":
            kind = Unit(name=name)
        elif sort == "Representation":
            kind = Representation(name=name)
        elif sort == "1":
            kind = Variable(name=name)
        elif sort == "Level":
            kind = Level(name=name)
        elif sort == "Codelist":
            kind = CodeList(name=name)
        if sort == "Phenomenon":
            kind = Phenomenon(name=name)           

    elif sort in elements:
        
        domain_jsons = str(kind_dict['domain']).replace("'",'"')
        domain = json_to_kind(domain_jsons)
        
        codomain_jsons = str(kind_dict['domain']).replace("'", '"')
        codomain = json_to_kind(codomain_jsons)

        if sort == "DatasetDesign":
            print("Kind DatasetDesign not implemented yet")
            #kind = DatasetDesign(name=name, domain=domain, codomain=codomain)
        elif sort == "ObjectTypeInclusion":
            kind = ObjectTypeInclusion(name=name, domain=domain, codomain=codomain)
        elif sort == "DatasetDescription":
            kind = DatasetDescription(name=name, domain=domain, codomain=codomain)
        elif sort == "PhenomenonMeasureMapping":
            kind = PhenomenonMeasureMapping(name=name, domain=domain, codomain=codomain)
        elif sort == "MeasureRepresentationMapping":
            kind = MeasureRepresentationMapping(name=name, domain=domain, codomain=codomain)
        elif sort == "ObjectTypeRelation":
            kind = ObjectTypeRelation(name=name, domain=domain, codomain=codomain)
        elif sort == "Variable":
            kind = Variable(name=name, domain=domain, codomain=codomain)
        elif sort == "Constant":
            kind = Constant(name=name, codomain=codomain)
        elif sort == "Operator":
            print("Kind: operator not implemented yet")
            #kind = Operator(name=name, domain=domain, codomain=codomain)
    return kind

def path_to_kind_dict(path: Path) -> list:
    """Function for translating neo4j.graph.Path object into a list Kind objects

    Args:
        path (Path): neo4j.graph.Path object containing relationships and nodes

    Returns:
        list: List of dictionaries describing the elements which form the path.
    """
    edges = path.relationships
    nodes = path.nodes
    node_dicts = []
    edge_dicts = []
    for edge in edges:
        edge_dict = query_result_to_dict(edge)
        edge_dicts.append(edge_dict)
    return edge_dicts

def query_result_to_dict(result: Result) -> dict:
    """Function to turn neo4j.work.results.Result object into a dictionary describing kind.

    Args:
        result (Result): neo4j.work.results.Result object; i.e. output of reading a transaction

    Returns:
        dict: Dictionary describing kind object
    """
    kind_dict = {}
    if result:
        kind_keys = result.keys()
        for key in kind_keys:
            kind_dict.update({key: result.get(key)})
    return kind_dict

