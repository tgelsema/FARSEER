"""
The following module contains the GraphDB object; the main interface between
the domainmodel graph and the rest of farseer. Most of the graph is implemented in
a Neo4J database, to allow for efficient querying of paths. However, some specific
objects, mappings and constructions related to the domainmodel are still implemented
in python due to their special roles or because of 
difficulties in implementing these in native Neo4J.
"""

from neo4j import GraphDatabase
import json
from farseer.graphdb.query_generation import create_node, create_relationship, get_edge, get_node, graph_paths, get_nodes
from farseer.graphdb.dbconfig import types, elements, uri, user, password
from farseer.graphdb.conversion import query_result_to_dict, path_to_kind_dict
from farseer.kind.knd import Kind
from typing import Union, List
from farseer.kind.knd import Kind, Measure, Phenomenon, ObjectType, Variable , \
                                ObjectTypeRelation, DatasetDesign, Quantity, Constant, Operator, Level, Unit, \
                                    Representation, CodeList, MeasureRepresentationMapping, ObjectTypeInclusion, DatasetDescription, PhenomenonMeasureMapping, One, one
from farseer.term.trm import Application, product, composition, cartesian_product

import os
import csv
import time
import json

class GraphDB:

    def __init__(self, uri: str, user: str, passw: str):
        """
        Construct a GraphDB object, which serves as an API between Python and the domainmodel stored in the database. 
        On initialization, the driver for database located at the given URI is created using supplied username and password. 
        Then, a database session is created
        Args:
            uri (str): URI for database
            user (str): Username for database
            passw (str): Password for database
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, passw))
        self.session = self.driver.session()
        """
        Initialize dictionary that keeps track of which kinds have been rebuilt from the graph database.
        This is dictionary is quite an important object, as python implementations of domainmodel objects 
        have unique identifiers which are used in various checks during interpret phase.
        Also, we construct some special domainmodel objects.
        """
        self.rebuilt_dm = {}
        self.getal = Quantity(name='getal')
        self.one = one
        self.rebuilt_dm.update({'1': self.one, 'getal': self.getal})
        self.gedeelddoor = Operator(name='(/)', domain=Application(cartesian_product,[self.getal, self.getal]), codomain=self.getal)
        """
        Add extras. These include various mappings relating domainmodel objects to each other, 
        or strings representing linguistic classifications.
        """
        self.defaults = self.parse_extra('defaults.csv')
        self.prefvar = self.parse_extra('prefvar.csv')
        self.whichway = self.parse_extra('whichway.csv')
        self.overridetarget = self.parse_extra('overridetarget.csv')
        self.orientation = self.parse_extra('orientation.csv')
        self.orderedobjecttype = self.parse_extra('orderedobjecttype.csv')
        self.interrogativepronouns = self.parse_extra('interrogativepronouns.csv')
        """
        Add datasetdesign. Necessary for compiling SQL queries from terms. 
        """
        self.data = [self.parse_datasetdesign(fp) for fp in os.listdir(os.path.join(os.path.dirname(__file__), "datasetdesigns"))]
        """
        Add all objecttypes. Needed by get_origin(). 
        Possibly, there exists a more 'Neo4j native' approach, however, this works and performance is satisfactory
        """
        self.objecttypes = self.get_types_of_sort('ObjectType')

    def create_db_node(self, name: str, sort: str, altname: str = None) -> None:
        """
        Create database node, corresponding to Kind given by its name and sort.

        Args:
            name (str): name of kind, as given by: Kind.name
            sort (str): sort of kind, as given by: Kind.__class__.__name__
            altname (str): alternative name, needed by inform module
        """
        self.session.write_transaction(create_node, name, sort, altname)

    def create_db_relationship(self, name: str, sort: str, domain: str, domain_sort: str, codomain: str, codomain_sort: str, article: str = None) -> None:
        """
        Create relationship between two nodes, representing an element in the domainmodel. 
        The element is given by its name and sort. For reconstruction of elements from the database, 
        domain and codomain of elements needs to be defined in the relationship as well.
        (however, this could be avoided by adding additional queries to the function get_kind()(on to-do list)).

        Args:
            name (str): Name of relationship
            sort (str): Sort of relationship, can be any relationship sort appearing in graphdb.dbconfig.elements
            domain (str): Name of the domain of the relationship. Needs to exist, otherwise exception should be raised. If domain is derived from Kind object, name is given by Kind.__class__.__name__.
            domain_sort (str): Sort of the domain of the relationship. Can be any sort of type appearing in graphdb.dbconfig.types. If domain is derived from Kind object, sort is given by Kind.__class__.__name__
            codomain (str): Name of the domain of the relationship. Needs to exist, otherwise exception should be raised. If codomain is derived from Kind object, name is given by Kind.__class__.__name__.
            codomain_sort (str): Sort of the codomain of the relationship. Can be any sort of type appearing in graphdb.dbconfig.types. If codomain is derived from Kind object, sort is given by Kind.__class__.__name__
            article (str): article, required by inform module
        """

        self.session.write_transaction(create_relationship, name, sort, domain, domain_sort, codomain, codomain_sort, article)

    def get_kind(self, name: Union[str, Kind], sort: str = None) -> Kind:
        """
        Get Kind object from database node/edge. 
        Required is name of Kind, optionally sort of Kind can be provided to speed up query

        Args:
            name (str): Name of kind
            sort (str, optional): Sort of kind. 
                                    If none is provided, get_kind will first look for type with supplied name, 
                                    then look for edge with supplied name. Defaults to None.

        Raises:
            Exception: Unknown kind exception of sort of kind is not in farseer.graphdb.dbconfig
            TypeError: Error when name and/or sort are not string.

        Returns:
            Kind: Kind object, as reconstructed from graph database.
        """
        if isinstance(name, Kind):
            return name

        if isinstance(name, str) & isinstance(sort, str):
            if name in self.rebuilt_dm.keys():
                return self.rebuilt_dm[name]
            if sort in types:
                node = self.session.read_transaction(get_node, name)
                if node:
                    kind = self.dict_to_kind(query_result_to_dict(node))
                    return kind
            elif sort in elements:
                edge = self.session.read_transaction(get_edge, name)
                if edge:
                    kind = self.dict_to_kind(query_result_to_dict(edge))
                    return kind
            else:
                raise Exception("Sort of kind not known, see farseer.graphdb.dbconfig for list of known types and elements")

        elif not sort and isinstance(name, str):

            if name in self.rebuilt_dm.keys():
                return self.rebuilt_dm[name]

            node = self.session.read_transaction(get_node, name)
            if node:
                kind = self.dict_to_kind(query_result_to_dict(node))
                return kind

            edge = self.session.read_transaction(get_edge, name)
            if edge:
                kind = self.dict_to_kind(query_result_to_dict(edge))
                return kind
        elif not name:
            return None
        else:
            raise TypeError("Cannot get kind, name and/or sort not string")

    def get_paths(self, origin: Union[str, Kind], destination: Union[str, Kind]) -> List[List[Kind]]:
        """
        Get paths between origin and destination. 
        Paths are given as a list containing relationships represented by correspond Kind objects. 
        These appear in the order they are traversed when moving from origin to destination.

        Args:
            origin (Union[str, Kind]): Origin of path. Represented by either string with name of kind or Kind object.
            destination (Union[str, Kind]):  Kind of path. Represented by either string with name of kind or Kind object.

        Returns:
            List[List[[Kind]]: List of paths represented by a list of relationships appearing in order from origin to destination.
        """
        if isinstance(origin, Kind):
            origin = origin.name
        if isinstance(destination, Kind):
            destination = destination.name
        paths_list = []
        if origin != None and destination != None:
            paths = self.session.read_transaction(graph_paths, origin, destination)
            paths_list = []
            for path in paths:
                path_list = []
                path_as_kind_dicts = path_to_kind_dict(path)
                for kind_dict in path_as_kind_dicts:
                    kind = self.dict_to_kind(kind_dict)
                    path_list.append(kind)
                path_list.reverse()
                paths_list.append(path_list)
        return paths_list

    def get_origin(self, obj1: Union[str, Kind], obj2: Union[str, Kind]) -> Kind:
        """ 
        Return obj1 if there is at least one path from obj1 to obj2 in the
        domain model. Conversely, return obj2 if there is a path from obj2 to obj1.
        If both obj1 and obj2 are not equal to None, inspect the domainmodel graph for
        the occurrence of an object type that has a path both to obj1 and obj2.
        Return the object type that is 'closest' to both obj1 and obj2. Note:
        getorigin is for now applied to arguments obj1 and obj2 that are both
        object types. If getorigin needs to be extended to any pair of types, then
        the statement 'if obj.sort == 'object type'' needs to be replaced with
        'if obj.kind == 'type'' AND the other types should be loaded in memory.

        Note also: 
        Current implementation needs all domainmodel objecttypes
        to be loaded in memory on initializing the GraphDB object, because they are being looped over. 
        Again, possibly, there exists a more 'Neo4j native' approach, however, this works and performance is satisfactory.

        Args:
            obj1 (Union[str, Kind]): Kind or name of Kind. See description above for more info
            obj2 (Union[str, Kind]): Kind or name of Kind. See description above for more info

        Returns:
            Kind: See descrition above
        """
    
        if obj1 == None:
            origin = obj2
        elif self.get_paths(obj1, obj2) != []:
            origin = obj1
        elif self.get_paths(obj2, obj1) != []:
            origin = obj2
        elif obj1 != None and obj2 != None and obj1 != obj2:
            origin = None
            for obj in self.objecttypes:
                if self.get_paths(obj, obj1) != [] and self.get_paths(obj, obj2) != []:
                    if self.get_paths(origin, obj) != [] or origin == None:
                        origin = obj
        else:
            origin = obj1
        return self.get_kind(origin)

    def dict_to_kind(self, kind_dict: dict) -> Kind:
        """Function turning kind dictionary as returned by query_result_to_dict() into proper Kind() object.

        Args:
            kind_dict (dict): Dictionary describing kind.
            rebuilt_dm (dict, optional): Dictionary keeping track of parts of domainmodel that are stored in-memory for the duration of the question answering. Defaults to rebuilt_dm.

        Returns:
            Kind: Kind() object from knd module
        """
        name = kind_dict['name']
        if name in list(self.rebuilt_dm.keys()): #if kind object has already been constructed, return that object from dictionary
            kind = self.rebuilt_dm[name]
            return kind

        sort = kind_dict['sort']
        kind = None
        if sort in types:
            #Might be a better way to do this
            if sort == "ObjectType":
                if 'altname' in kind_dict.keys():
                    altname = kind_dict['altname']
                else:
                    altname = None
                kind = ObjectType(name=name, altname=altname)
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
            elif sort == "One":
                kind = One()
            elif sort == "Level":
                kind = Level(name=name)
            elif sort == "Codelist":
                kind = CodeList(name=name)
            elif sort == "Phenomenon":
                kind = Phenomenon(name=name)

        elif sort in elements:
            domain = self.dict_to_kind(json.loads(kind_dict['domain']))
            codomain = self.dict_to_kind(json.loads(kind_dict['codomain']))

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
                if 'article' in kind_dict.keys():
                    article = kind_dict['article']
                else:
                    article = None
                kind = Variable(name=name, domain=domain, codomain=codomain, article=article)
            elif sort == "Constant":
                if 'code' in kind_dict.keys():
                    code = kind_dict['code']
                else:
                    code = None
                kind = Constant(name=name, codomain=codomain, code=code)
            elif sort == "Operator":
                print("Kind: operator not implemented yet")
                #kind = Operator(name=name, domain=domain, codomain=codomain)
        self.rebuilt_dm.update({name: kind})#add kind to rebuilt domainmodel
        return kind

    def parse_extra(self, file_name: str) -> dict:
        """
        Parse CSV's containing lookup tables relating certain domainmodel objects to each other,
        or to strings representing linguistic characterisations.

        Args:
            file_name (str): name of file containing table, should be in ./extras folder

        Returns:
            dict: Dictionary of extras
        """
        dir_path = os.path.dirname(__file__)
        with open(os.path.join(dir_path, 'extras', file_name), 'r') as extra_file:
            reader = csv.reader(extra_file, delimiter = ';')
            header = next(reader)
            extras_dict = {}
            if file_name == 'defaults.csv':
                for row in reader:
                    kind = self.get_kind(row[0], row[1])
                    default_list = []
                    for i in range(int((len(row)/2))-1):
                        default = self.get_kind(row[2*i+2], row[2*i+3])
                        default_list.append(default)
                    extras_dict.update({kind: default_list})
            elif file_name == 'interrogativepronouns.csv':
                for row in reader:
                    kind = self.get_kind(row[0], row[1])
                    strng = row[2]
                    extras_dict.update({kind: strng})
            else:
                for row in reader:
                    kind_key = self.get_kind(row[0], row[1])
                    kind_value = self.get_kind(row[2], row[3])
                    extras_dict.update({kind_key: kind_value})
            return extras_dict

    def parse_datasetdesign(self, file_name: str) -> DatasetDesign:
        """
        Parse JSON files containing parameters for initializing DatasetDesign objects

        Args:
            file_name (str): name of JSON file containig parameters for DatasetDesign

        Returns:
            DatasetDesign: object describing dataset design
        """
        dir_path = os.path.dirname(__file__)
        file_path = os.path.join(dir_path, 'datasetdesigns' , file_name)

        with open(file_path, 'r') as jsonfile:

            data = json.loads(jsonfile.read())

            name = data["name"]
            constr = data["constr"]

            constr_type = constr["construction_type"]
            arguments = constr["arguments"]

            operator = arguments["operator"]
            operands = arguments["operands"]

            args = []

            for operand in operands:
                arg = self.get_kind(operand["name"], 'Variable')
                if arg:
                    args.append(arg)
                else:
                    arg = Variable(name=operand["name"], domain=self.get_kind(operand["domain"]), codomain=self.get_kind(operand["codomain"]))
                    self.rebuilt_dm.update({arg.name: arg})
                    args.append(arg)

            if constr_type == "Application":
                if operator == "product":
                    datadesign = DatasetDesign(name=name, constr=Application(product, args))
        return datadesign

    def get_types_of_sort(self, which_sort: str) -> List[Kind]:
        """
        Simple utility to get all kind of a given sort

        Args:
            which_sort (str): sort of interest

        Returns:
            List[Kind]: list of kinds of that sort
        """
        types = self.session.read_transaction(get_nodes, which_sort)
        type_list = [self.dict_to_kind(query_result_to_dict(t)) for t in types]
        return type_list

    def close(self):
        self.driver.close()

graph = GraphDB(uri, user, password)