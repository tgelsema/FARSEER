"""
This file contains some configurations for working with Graph implemented in Neo4J
"""

LOCAL = True #For debugging purposes. Set to true if working with local Neo4j database, set to False if working with remote.

types = ["ObjectType", "Phenomenon", "Quantity", "Measure",\
             "Unit","Representation", "One", "Level", "CodeList"]
elements = ["DatasetDesign", "ObjectTypeInclusion", "DatasetDescription",\
                "PhenomenonMeasureMapping", "MeasureRepresentationMapping", "ObjectTypeRelation", \
                "Variable" , "Constant", "Operator"]
one_name = "1"
one_type = "One"

if LOCAL:
    uri = "neo4j://localhost:7687" #Standard URL and port for local database
    user = "neo4j"
    password = "password"

else:
    uri = "" #URL for neo4j database
    user = ""
    password = ""