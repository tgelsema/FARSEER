"""
Script to create graph in Neo4J database
"""


from farseer.domainmodel.dm import domainmodel
from farseer.kind.knd import Phenomenon, ObjectType, Variable, ObjectTypeRelation, DatasetDesign, Quantity, Constant, Operator, Level, Kind
from farseer.term.trm import Application, product, composition, cartesian_product
import xml.etree.ElementTree as ET
from farseer.graphdb.query_generation import create_node, create_relationship, add_type_label, add_element_label, clear
from typing import Tuple
from farseer.graphdb.dbconfig import types, elements, one_name, one_type, uri, user, password
from neo4j import GraphDatabase
from typing import Union, List

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

    def create_db_node(self, name: str, sort: str, altname=None) -> None:
        """
        Create database node, corresponding to Kind given by its name and sort

        Args:
            name (str): name of kind, as given by: Kind.name
            sort (str): sort of kind, as given by: Kind.__class__.__name__
        """
        self.session.write_transaction(create_node, name, sort, altname)

    def create_db_relationship(self, name: str, sort: str, domain: str, domain_sort: str, codomain: str, codomain_sort: str, article=None, code=None) -> None:
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
        """

        self.session.write_transaction(create_relationship, name, sort, domain, domain_sort, codomain, codomain_sort, article, code)

    def get_kind(self, name: Union[str, Kind], sort: str = None) -> Kind:
        """
        Get Kind object from database node/edge

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
                kind = self.dict_to_kind(query_result_to_dict(node))
                return kind
            elif sort in elements:
                edge = self.session.read_transaction(get_edge, name)
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

    def dict_to_kind(self, kind_dict: dict) -> Kind:
        """Function turning kind dictionary as returned by query_result_to_dict() into proper Kind() object.

        Args:
            kind_dict (dict): Dictionary describing kind.
            rebuilt_dm (dict, optional): Dictionary keeping track of parts of domainmodel that are stored in-memory for the duration of the question answering. Defaults to rebuilt_dm.

        Returns:
            Kind: Kind() object from knd module
        """
        print("dict_to_kind(", kind_dict, ")")
        name = kind_dict['name']
        if name in list(self.rebuilt_dm.keys()): #if kind object has already been constructed, return that object from dictionary
            print(name, "already built")
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
                print("Building one")
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
                kind = Constant(name=name, codomain=codomain)
            elif sort == "Operator":
                print("Kind: operator not implemented yet")
                #kind = Operator(name=name, domain=domain, codomain=codomain)
        self.rebuilt_dm.update({name: kind})#add kind to rebuilt domainmodel
        return kind

    def parse_extra(self, file_name):
        with open(os.path.join('extras', file_name), 'r') as extra_file:
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

    def get_types_of_sort(self, which_sort: str):
        types = self.session.read_transaction(get_nodes, which_sort)
        type_list = [self.dict_to_kind(query_result_to_dict(t)) for t in types]
        return type_list

    def clear_all(self):
        self.session.write_transaction(clear)

    def close(self):
        self.driver.close()

graph = GraphDB(uri, user, password)


def divide_types_and_elements(domainmodel: list, types: list, elements: list) -> Tuple[dict, dict]:
    """
    Creating database relationships before all nodes have been created leads to problems,
    hence, all types(database nodes) in the domainmodel should be created before elements(database relationships) are added.
    This function splits up types and elements, so that the above can be achieved

    Args:
        domainmodel (list): List of objects in domainmodel
        types (List): List of all types, as string
        elements (List): List of all elements, as string

    Returns:
        Tuple[dict, dict]: Tuple of dictionaries of the form {"kind of type": Kind(), "another}
    """
    dm_types = {}
    dm_elements = {}
    for kind in domainmodel:
        kind_of_kind = kind.__class__.__name__
        if kind_of_kind in types:
            if kind_of_kind in list(dm_types.keys()):
                dm_types[kind_of_kind].append(kind)
            else:
                dm_types.update({kind_of_kind: [kind]})
        elif kind_of_kind in elements:
            if kind_of_kind in list(dm_elements.keys()):
                dm_elements[kind_of_kind].append(kind)
            else:
                dm_elements.update({kind_of_kind: [kind]})
        else:
            pass
    return dm_types, dm_elements

def create_all_dm_nodes(graph: GraphDB, dm_types: dict, one_name: str, one_type: str):
    """Create all database nodes using this function.

    Args:
        session (session): Database session
        dm_types (dict): Dictionary of the form {"kind_of_type": [instance_of_kind, another_instance, ....], "another_kind_of_type": [instance_of_antoher_kind, another_instance_of_that_kind, ...]}
        one_name (str): Name of singleton class One(), supplied by dbconfig.py
        one_type (str): Type for singleton class One(), supplied by dbconfig.py 
    """
    #First, create node for the special object "one"
    graph.create_db_node(one_name, one_type)
    #Second, go through dictionary of domainmodel types 
    for (key, value_list) in dm_types.items():
        if key in ["ObjectType", "Phenomenon", "Quantity", "Level"]:
            for dm_type in value_list:
                graph.create_db_node(dm_type.name, key, dm_type.altname)

def create_all_relationships(graph: GraphDB, dm_elements: dict, ones: list = None, alls: list = None):
    """Function to create all relationships between objects
    Args:
        session (session): database session
        dm_elements (dict): Dictionary of elements of the form {"kind_of_element": [instance_of_element, another_instance_of_element, ....], "another_kind_of_element": [...,..]}
        ones (list): if ones are not in domainmodel, they should be supplied here
        alls (list): if alls are not in domainmodel, they should be supplied here
    """

    #add domainmodel elements
    for (key, element_list) in dm_elements.items():
        if key in ["ObjectTypeRelation", "Variable"]: 
            for element in element_list:
                try: #add domain if specified
                    domain = element.domain.name
                    domain_sort = element.domain.__class__.__name__
                except AttributeError:
                    print(f"No domain specified for {key} {element}")
                try:
                    codomain = element.codomain.name
                    codomain_sort = element.codomain.__class__.__name__
                except AttributeError:
                    print(f"No domain specified for {key} {element}")
                graph.create_db_relationship(name = element.name, sort = key, codomain=codomain, codomain_sort=codomain_sort, domain=domain, domain_sort=domain_sort, article=element.article)
        if key == "Constant":
            for element in element_list:
                try: #add domain if specified
                    codomain = element.codomain.name
                    codomain_sort = element.codomain.__class__.__name__
                except AttributeError:
                    print(f"No codomain specified for {key} {element}")
                domain = one_name
                domain_sort = one_type
                graph.create_db_relationship(name = element.name, sort = key, codomain=codomain, codomain_sort=codomain_sort, domain=domain, domain_sort=domain_sort, article=element.article, code=element.code)
        if key == "Operator":
            print("Operator not implemented in graph database")
            pass
        if key == "":
            pass
def add_labels_to_nodes(session, label_name: str, label_dict: dict):
    """
    Function to add labels to nodes.
    E.g. if the default for ObjectType 'persoon' is [naam],
    the label persoon.default = [naam] will be added to the node.

    Args:
        session (): Database session
        label_name (str): Name of label(property) to be added to database node
        label_dict (dict): Dictionary with keys corresponding to nodes and values corresponding to the value the label should take
    """
    for (key, value) in label_dict.items():
        var_val_tuple = (label_name, value)
        session.write_transaction(add_type_label, key, var_val_tuple)

def add_labels_to_relationships(session, label_name: str, label_dict: dict):
    """
    Function to add labels to relationship.
    E.g. if the prefaggrmode of 'leeftijd' is 'avg'
    the label leeftijd.prefaggrmode = 'avg' will be added to the node.

    Args:
        session (): Database session
        label_name (str): Name of label(property) to be added to database node
        label_dict (dict): Dictionary with keys corresponding to nodes and values corresponding to the value the label should take
    """
    for (key, value) in label_dict.items():
        var_val_tuple = (label_name, value)
        session.write_transaction(add_element_label, key, var_val_tuple)

def make_graph():

    graph.clear_all()
    
    dm_types, dm_elements = divide_types_and_elements(domainmodel, types, elements)

    create_all_dm_nodes(graph, dm_types, one_name, one_type)
    create_all_relationships(graph, dm_elements, types, elements)



if __name__ == '__main__':
    make_graph()