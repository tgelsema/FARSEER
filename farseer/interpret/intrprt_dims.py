#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 16:25:17 2019

@author: tgelsema

The farseer.interpret.intrprt_dims package exposes two routines used in the
farseer.interpret.intrprt package, viz. getdimensionpaths() and
appendvariablestopaths(). The first computes paths from the pivot to objects
that can be interpreted as the dimensions of a query. The getdimensionpaths()
routine also computes some extra information in the form of a dictionary, which
only applies in the case of intrprt.assembletermforclass5(). The second appends
suitable variables to the paths found in getdimensionpaths() to get true
dimensions. These two are used in combination in the farseer.interpret.intrprt
routines.
"""
from farseer.interpret.intrprt_base import ispostfix, getindexfrompattern, insertsorted, getoptimalpath, makeproduct
from farseer.graphdb.dm import defaults
from farseer.term.trm import Application
from farseer.kind.knd import Variable
from farseer.graphdb.graphdb import graph

def getdimensionpaths(objectlist, keywordlist, pivot, target, ignoresplit, hints):
    """Return two lists of paths. The first is a list of paths from pivot to
    every dimension indexed and discovered by extractdimensions(). Some clues
    are given to the getoptimalpath() routine to help the discovery and are
    calculated first. First, extractdimensions() extracts indices to suitable
    object types, object type relations and categorical variables from
    keywordlist. Then optimal paths from pivot to these objects are calculated.
    Paths that are part of other paths are ignored (insertwithoutpostfixes).
    The resulting list of paths is returned. Note that a path may 'end with' an
    object type relation (i.e., path[0] is an object type relation) or path may
    'end with' a categorical variable. Suitable variables must therefore be
    appended to each path (if applicable) to turn them into true dimensions.
    See appendvariablestopaths().
    Hints are given to getdimensionpaths() only in the case of
    intrprt.assembletermforclass5(), which involes finding suitable dimensions
    for a numerator and a denominator. In this case, and only in this case,
    the second set of paths, pathsfrompivotdict, returned in the discovery of
    dimensions for the numerator is given as hints for finding dimensions for
    the denominator. In this case, it is necessary that dimensions for
    numerator and denominator 'align' in some way, and hints provides a
    mechanism to achieve that. Also, only in case assembletermforclass5() a so-
    called split may apply (given by ignoresplit): this is a dimension that
    should for some reason be ignored from the list of paths.
    Note that the dictionary pathsfrompivotsdict is just a suitable copy (viz.
    as a dictionary) of the first list returned, with possibly some extra paths
    that are postfixes of others.
    """
    pathsfrompivotdict = {}
    dimsdict = extractdimensions(objectlist, keywordlist, pivot, target)
    someclues = getsomeclues(objectlist, keywordlist, target, dimsdict)
    pathsfrompivot = []
    for k in dimsdict.keys():
        clues = someclues
        obj = objectlist[k]
        if k != dimsdict[k]:
            clues.append(objectlist[dimsdict[k]])
        if keywordlist[k] == '<ot>':
            dest = obj
        else:
            dest = obj.codomain
            clues.append(obj)
        if dest != ignoresplit:
            hint = []
            if k in hints.keys():
                if hints[k] != []:
                    if isinstance(hints[k][0], Variable):
                        hint = hints[k][1:]
                    else:
                        hint = hints[k]
            path = getoptimalpath(graph.get_paths(pivot, dest), clues, hint)
            pathsfrompivot = insertwithoutpostfixes(path, pathsfrompivot)
            pathsfrompivotdict[k] = path
    return (pathsfrompivot, pathsfrompivotdict)

def getsomeclues(objectlist, keywordlist, target, dimsdict):
    """Return some object types as clues to find optimal paths. Object types
    must not be the 'endpoints' of the objects pointed to by dimsdict. Find
    remaining object types in objectlist and return them. Target is always a
    clue.
    """
    clues = [target]
    endpoints = []
    for k in dimsdict.keys():
        obj = objectlist[k]
        if keywordlist[k] == '<ot>':
            if obj not in endpoints: 
                endpoints.append(obj)
        else:
            if obj.codomain not in endpoints:
                endpoints.append(obj.codomain)
    k = 0
    while k < len(keywordlist):
        if keywordlist[k] == '<ot>' and objectlist[k] not in clues:
            clues.append(objectlist[k])
        k += 1
    return clues

def insertwithoutpostfixes(path, paths):
    """Insert path into a list of paths if path is not part of another path p
    already present in the list. Also, if there is a path p in paths that is a
    part of path, then remove p and insert path into paths. Return the
    resulting paths list. From the way paths are formed, the essential check is
    whether p is a postfix of path, or whether path is a postfix of p.
    """
    donotinsert = False
    for p in paths:
        if ispostfix(path, p):
            donotinsert = True
            break
        if ispostfix(p, path):
            paths.remove(p)
    if not donotinsert:
        paths = insertsorted(paths, path)
    return paths

def appendvariablestopaths(paths):
    """Append variables to each path in paths, if a path does not end with a
    variable already (i.e., path[0] is not a variable). The variables appended
    are the defaults that are listed in the domainmodel for each object type.
    The routine 'appendvariables()' appends these defauts to an individual path.
    Return the list of paths thus obtained.
    """
    returnpaths = []
    for path in paths:
        if path != []:
            path = appendvariables(path)
        returnpaths.append(path)
    return returnpaths

def appendvariables(path):
    """If path ends with a variable (i.e., if path[0] is a variable), return
    path without change. Otherwise, append a product of suitable default
    variables (taken from the defaults dictionary of domainmodel), i.e., insert
    it at position 0 in the path. Return the resulting path.
    """
    if path == []:
        return path
    elif path[0].__class__.__name__ == 'Variable' or isinstance(path[0], Application):
        return path
    else:
        if path[0].codomain in defaults:
            path.insert(0, makeproduct(defaults[path[0].codomain]))
        return path

def extractdimensions(objectlist, keywordlist, pivot, target):
    """Collect indices to potential dimensions from keywordlist, according to
    some given patterns. For the patterns <ot><prep><otr> and
    <catvar><prep><otr> (these correspond to e.g. 'gemeente van vestiging'
    and 'geslacht van werknemer'), also collect indices to the corresponding
    object type relations ('vestiging' and 'werknemer', respectively). These
    will serve as clues when paths from the target to the endpoints of the
    potential dimensions are investigated. From the dictionary of indices so
    collected, possibly remove indices, e.g. when there is a path from an
    endpoint to the target, or when an endpoint corresponds to the pivot.
    Finally, remove potential dimensions when they correspond to (the
    codomain of) a constant: in this case, the potential dimension has already
    been used as a selection criterion. Return the dictionary of indices and
    clues so obtained.
    """
    dimindices = {}
    i = 0
    while i < len(keywordlist):
        k = [-1, -1, -1]
        k[0] = getindexfrompattern(['<per>'], 0, i, keywordlist, True)
        k[1] = getindexfrompattern(['<prep>','<all>'], 0, i, keywordlist, True)
        k[2] = getindexfrompattern(['<prep>', '<ot>'], 0, i, keywordlist, True)
        j = len(keywordlist)
        for l in k:
            if l != -1 and l < j:
                j = l
        if j < len(keywordlist):
            j += 1
            while j < len(keywordlist) and (
                keywordlist[j] == '<ot>' or
                keywordlist[j] == '<otr>' or
                keywordlist[j] == '<catvar>' or
                keywordlist[j] == '<all>' or
                keywordlist[j] == '<prep>' or ####
                keywordlist[j] == '<unk>'):
                if getindexfrompattern(['<ot>', '<prep>', '<otr>'], 0, j, keywordlist, True) == j:
                    dimindices[j] = j + 2
                    j += 2
                elif getindexfrompattern(['<catvar>', '<prep>', '<otr>'], 0, j, keywordlist, True) == j:
                    dimindices[j] = j + 2
                    j += 2
                elif keywordlist[j] == '<ot>' or keywordlist[j] == '<catvar>' or keywordlist[j] == '<otr>':
                    dimindices[j] = j
                j += 1
        i = j
    # possibly remove some object types. Also correct for selection criteria
    remove = []
    for i in dimindices.keys():
        if keywordlist[i] == '<catvar>':
            obj = objectlist[i].codomain
        elif keywordlist[i] == '<otr>':
            if dimindices[i] != i:
                obj = objectlist[dimindices[i]]
            else:
                obj = objectlist[i].codomain
        else:
            obj = objectlist[i]
        if obj.equals(pivot) or obj.equals(target) or graph.get_paths(obj, target) != []:
            if not i in remove:
                remove.append(i)
        k = 0
    for r in remove:
        if r in dimindices.keys():
            dimindices.pop(r)
    return dimindices