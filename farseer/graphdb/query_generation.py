"""
This module contains utility functions for generating queries to be executed by Neo4j's session object.
Using the GraphDB object will call these functions, but the user of the GraphDB object does not need to worry about functions in this module.
For example, creating a node in the graph is done by calling GraphDB.create_node(), which will in turn call Neo4j's write transaction function,
with input the create_node() function defined in this module. 
"""

from neo4j import GraphDatabase
from farseer.kind.knd import Kind
from typing import List
from neo4j import Transaction
from neo4j.work.result import Result
from farseer.graphdb.dbconfig import uri, user, password

driver = GraphDatabase.driver(uri, auth=(user, password))

#QUERY GENERATION AND EXECUTION
def create_node(tx: Transaction, name: str, sort: str, altname = None):
    """
    Generate and run query to create graph node for Kind with given name and sort.
    This function gets called by Neo4j's session.write_transaction() function.
    See GraphDB.create_node() function for more details

    Args:
        tx (transaction): Neo4J transaction object
        name (string): Name of Kind
        sort (string): Sort of Kind
    """
    query = """CREATE (a:Type {name:"%(name)s", sort:"%(sort)s" """ % {"name": name, "sort": sort}
    if altname:
        query = query + """, altname:"%(altname)s" """ % {"altname": altname}
    query = query + """}) RETURN id(a)"""
    tx.run(query)

def create_relationship(tx: Transaction, name: str, sort: str, domain: str, domain_sort: str, codomain: str, codomain_sort: str, article: str = None, code: str = None):
    """
    Generate and run query to create graph relationship for Kind with given name and sort.
    This function gets called by Neo4j's session.write_transaction() function.
    See GraphDB.create_relationship() function for more details

    Args:
        tx (transaction): Neo4J transaction object
        name (string): Name of Kind
        sort (string): Sort of Kind
        domain (string): Domain of element
        domain_sort (string): Sort of domain
        codomain (string): codomain of element
        codomain_sort (string): sort of codomain
        article (string): article of element. Defaults to None.
        code (string): code of element. Defaults to None.
    """
    #Start base query to create relationship
    query = """MATCH (a:Type {name:"%(domain)s"}), (b:Type {name:"%(codomain)s"}) CREATE (a)-[r:Element {name:"%(name)s", sort:"%(sort)s" """ % {"codomain": codomain, "domain": domain, "name": name, "sort": sort}
    #Add article if provided
    if article:
        query += """, article:"%(article)s" """ % {"article": article}
    #Add code if provided
    if code:
        query += """, code:"%(code)s" """ % {"code": code}
    #Finish base query to create relationship
    query += """}]->(b)"""
    #Set additional attributes
    query += """ SET r.codomain = '{"name": "%(codomain)s", "sort":"%(codomain_sort)s"}' SET r.domain = '{"name": "%(domain)s", "sort":"%(domain_sort)s"}' """ % {"codomain": codomain, "codomain_sort": codomain_sort, "domain": domain, "domain_sort": domain_sort}
    tx.run(query)

def shortestpath(tx, start: str, end: str):
    query = "MATCH (a:Type {name:'%(start)s'}), (b:Type {name:'%(end)s'}), p=shortestPath((a)-[*]->(b)) RETURN p" % {"start": start, "end": end}
    return tx.run(query).single().value()

def graph_paths(tx: Transaction, start: str, end: str) -> List[Result]:
    """
    Find all paths in database between start and end. Return a Result object which need further parsing.
    See GraphDB.get_paths() for more info.

    Args:
        tx (Transaction): neo4j transaction object
        start (str): Name of start node
        end (str): Name of end node

    Returns:
        List[Result]: List of neo4j.work.result.Result objects containing information about paths.
    """
    query = "MATCH (a:Type {name:'%(start)s'}), (b:Type {name:'%(end)s'}), p=(a)-[*]->(b) RETURN p" % {"start": start, "end": end}
    results = tx.run(query).value()
    return [result for result in results]

def get_nodes(tx: Transaction, which_sort: str) -> List[Result]:
    """
    Get multiple nodes of a given sort.

    Args:
        tx (Transaction): Neo4j transaction object
        which_sort (str): sort of kinds to be retrieved

    Returns:
        List[Result]: List of Neo4j results representing the nodes.
    """    
    QUERY = """MATCH (a {sort: '%(sort)s'}) RETURN a""" % {"sort": which_sort}
    results = tx.run(QUERY).value()
    return [result for result in results]

def get_node(tx, node_name: str) -> Result:
    QUERY = """MATCH (a {name: "%(name)s"}) RETURN a""" % {"name": node_name}
    result = tx.run(QUERY).single()
    if result:
        result = result.value()
    return result

def get_edge(tx, edge_name: str) -> Result:
    QUERY = """MATCH (a)-[r {name: "%(edge_name)s"}]->(b) RETURN r""" % {"edge_name": edge_name}
    result = tx.run(QUERY).single()
    if result:
        result = result.value()
    return result

def clear(tx):
    tx.run("""MATCH (n) DETACH DELETE (n)""")
    print("Graph cleared")

"""
Now follow some functions for adding labels. 
Currently, these are not being used.
"""

def set_object_label(tx, type: str, name: str, var_val_dict: dict):
    query = "MATCH (a:%(type)s {name:'%(name)s'})" % {"type": type, "name": name}
    for (variable, value) in list(var_val_dict.items()):
        if not isinstance(value, list):
            query = query + " SET a.%(variable)s = '%(value)s'" % {"variable": variable, "value": value}
        else:
            value_list = value
            quoted_values = ""
            for value in value_list:
                quoted_values += f"'{value}', "
            quoted_values = quoted_values.strip(", ")
            query += " SET a.%(variable)s = [%(quoted_values)s]" % {"variable": variable, "quoted_values": quoted_values}
    tx.run(query)

def set_element_label(tx, type: str, name: str, var_val_dict: dict):
    query = "MATCH (a)-[r:%(type)s {name:'%(name)s'}]->(b)" % {"type": type, "name": name}
    for (variable, value) in list(var_val_dict.items()):
        if not isinstance(value, list):
            query = query + " SET r.%(variable)s = '%(value)s'" % {"variable": variable, "value": value}
        else:
            value_list = value
            quoted_values = ""
            for value in value_list:
                quoted_values += f"'{value}', "
            quoted_values = quoted_values.strip(", ")
            query += " SET r.%(variable)s = [%(quoted_values)s]" % {"variable": variable, "quoted_values": quoted_values}
    tx.run(query)

def add_type_label(tx, name: str, var_val_tuple: tuple):
    """Function to generate and run query for adding labels to types(nodes).

    Args:
        tx (transaction): database transaction
        name (str): Name of type(node)
        var_val_tuple (tuple): tuple of variable(label name) and value(label)
    """
    variable, values = var_val_tuple[0], var_val_tuple[1]
    query = """MATCH (%(name)s {name:'%(name)s'})""" % {"name": name}
    
    if isinstance(values, list):
        if len(values) != 0:
            value_list_string = ""
            for value in values:
                if isinstance(value, Kind):
                    value_json = kind_to_json(value)
                elif isinstance(value, str):
                    value_json = """{'string': %(value)s}""" % {"value": value}
                else:
                    print("Unable to add label %(label)s, label datatype not supported" % {'label': variable})
                value_list_string = value_list_string \
                                        + "%(value_json)s" % {"value_json": value_json} \
                                        + ", "
            value_list_string = value_list_string.strip(", ")
            value_list_json = """ {'list': [%(value_list_string)s] } """ % {"value_list_string": value_list_string}
            query += """ SET %(name)s.%(var)s = "%(value_list_json)s" """ % {"name": name, "var": variable, "value_list_json": value_list_json}
        if len(values) == 0:
            query += """ RETURN %(name)s""" % {"name": name} #do nothing
    elif isinstance (values, Kind):
        value_json = kind_to_json(values)
        query += """ SET %(name)s.%(var)s = "%(value)s" """ % {"name": name, "var": variable, "value": value_json}
    elif isinstance(values, str):
        value_type = 'string'
        value_name = values
        value_json = '{%(value_type)s: %(value_name)s}' % {"value_type": value_type, "value_name": value_name}
        query += """ SET %(name)s.%(var)s = "%(value)s" """ % {"name": name, "var": variable, "value": value_json}
    else:
        print("Unable to add label, label datatype not supported")
    tx.run(query)

def add_element_label(tx, name: str, var_val_tuple: tuple):
    """Function to generate and run query for adding labels to elements(edges/relationships).

    Args:
        tx (transaction): database transaction
        name (str): Name of element 
        var_val_tuple (tuple): tuple of variable(label name) and value(label value)
    """
    query = """MATCH (a)-[%(name)s {name: '%(name)s'}]->(b)""" % {"name": name}
    variable, values = var_val_tuple[0], var_val_tuple[1]
    if isinstance(values, list):
        if len(values) != 0:
            value_list_string = ""
            for value in values:
                if isinstance(value, Kind):
                    value_json = kind_to_json(value)
                elif isinstance(value, str):
                    value_json = """{"string": %(value)s}""" % {"value": value}
                else:
                    print("Unable to add label, label datatype not supported")
                value_list_string = value_list_string \
                                        + "%(value_json)s" % {"value_json": value_json} \
                                        + ", "
            value_list_string = value_list_string.strip(", ")
            query += """ SET %(name)s.%(var)s = ["%(value_list_string)s"]""" % {"name": name, "var": variable, "value_list_string": value_list_string}
            print(query)
        if len(values) == 0:
            query += """ RETURN %(name)s""" % {"name": name} #do nothing
    elif isinstance (values, Kind):
        value_json = kind_to_json(values)
        query += """ SET %(name)s.%(var)s = '%(value)s'""" % {"name": name, "var": variable, "value": value_json}
    elif isinstance(values, str):
        value_type = 'string'
        value_name = values
        value_json = '{%(value_type)s: %(value_name)s}' % {"value_type": value_type, "value_name": value_name}
        query += """ SET %(name)s.%(var)s = "%(value)s" """ % {"name": name, "var": variable, "value": value_json}
    else:
        print("Unable to add label, label datatype not supported")
    tx.run(query)



    