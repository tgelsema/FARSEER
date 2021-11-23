"""
Module for serialization of DatasetDesign objects as JSON, 
such that they can be used by the GraphDB object.

Running this module will take DatasetDesigns defined in the domainmodel
and save them as JSON in datasetdesign folder.
"""


from farseer.domainmodel.dm import data
from farseer.kind.knd import DatasetDesign
import json
import os
from typing import Dict

def data_to_dict(design: DatasetDesign) -> Dict:
    """Serialize DatasetDesign object as python dictionary

    Args:
        design (DatasetDesign): DatasetDesign object. Construction type is assumed to be Application(is this okay?)

    Returns:
        Dict: Dictionary containing all information for storing design as JSON
    """
    datadict = {
                "name": design.name,
                "constr": {
                        "construction_type": "Application",
                        "arguments": {
                                        "operator": design.constr.op.name,
                                        "operands": [{"name": design.constr.args[i].name, "domain": design.constr.args[i].domain.name, "codomain": design.constr.args[i].codomain.name} for i in range(len(design.constr.args))]
                                        }
                        }
                }
    return datadict

def save_datadesign(design: DatasetDesign) -> None:
    """Save DatasetDesign dictionary as JSON in datasetdesign folder 

    Args:
        design (DatasetDesign): DatasetDesign dict created with data_to_dict()
    """
    dir_path = os.path.dirname(__file__)
    design_dict = data_to_dict(design)
    with open(os.path.join(dir_path, "datasetdesigns", f'{design_dict["name"]}data.json'), 'w+') as jsonfile:
        json.dump(design_dict, jsonfile)


if __name__ == '__main__':
    for design in data:
        save_datadesign(design)