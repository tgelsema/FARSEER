"""
Replacement for farseer.domainmodel.dm to import from. Used primarily by interpret modules.
"""

from farseer.graphdb.graphdb import graph


getal = graph.getal
one = graph.one
defaults = graph.defaults
interrogativepronouns = graph.interrogativepronouns
prefvar = graph.prefvar
overridetarget = graph.overridetarget
whichway = graph.whichway
orientation = graph.orientation
orderedobjecttype = graph.orderedobjecttype
gedeelddoor = graph.gedeelddoor
data = graph.data
"""
domainmodel = dm[1]
defaults = dm[3]
overridetarget = dm[4]
prefaggrmode = dm[5]
vocab = dm[6]
optimalpathhelper = dm[9]
getal = dm[13]
gedeelddoor = dm[14]
"""