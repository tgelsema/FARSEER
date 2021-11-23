#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 10:43:35 2019

@author: tgelsema

This package exposes two main routines used in the intrprt.py package, viz.
getiota() and getkappa(). The getiota() routine returns a selection term with
selection criteria that match the constants in objectlist. If pivot does not
equal target, the selection term must be 'embedded' inside a kappa term (range)
which means that a composition term that is derived from a path from pivot to
target is composed with the selection term, and the whole is taken as argument
for the kappa term. The kappa term is constructed by the getkappa() routine.
In some cases, the selection term must be constructed in two phases (in
particular in the intrprt.assembletermforclass5() routine): in that case,
getiotapaths() is called, followed by makeiota(). This is to make sure that a
dictionary of 'hints' can be passed as an extra argument to optimal path
finding routines. In the standard case, getiota() does not make use of 'hints'.
"""

from farseer.graphdb.dm import prefvar
from farseer.interpret.intrprt_base import getoptimalpath, alle, makecomposition, makeproduct, terminlist, getclueindexfrompattern, getcontext, makekappa, makeinclusion
from farseer.interpret.intrprt_dims import appendvariablestopaths
from farseer.graphdb.graphdb import graph

def getiotapaths(objectlist, keywordlist, pivot, target, hints):
    """Return a dictionary of paths (indexed by indices in objectlist to
    constants) from the pivot to the codomain of all constants in objectlist.
    This codomain is the codomain of an appropriate variable that matches the
    constant, as 'geslacht' matches 'man' or 'vrouw'. For each of these
    constants get some clues: objects in objectlist that correspond to these
    constants, as e.g. the constant 'Den Haag' in 'wonen in Den Haag' gets
    'wonen' as a clue. Helped by these clues, obtain a path for each constant
    from the pivot to the codomain of the constant. Makeiota() uses these paths
    to build a proper iota (selection) term. As an external mechanism, besides
    'clues', also 'hints' can be used in the searching for appropriate paths
    routine. These are only used in the intrprt.assembletermforclass5()
    routine and form a dictionary of paths, of the same structure as returned
    by getiotapaths().
    """
    cluedict = {}
    k = 0
    while k < len(keywordlist):
        if keywordlist[k] == '<const>':
            cluedict[k] = getclues(k, keywordlist)
        k += 1
    cluesasobjs = getcluesasobjects(cluedict, objectlist, keywordlist)
    paths = getpathstoconstants(cluesasobjs, objectlist, pivot, target, hints)
    return paths

def getiota(objectlist, keywordlist, pivot, target):
    """Return an inclusion term by calling makeiota(), but first find all paths
    from the pivot to the codomain of all constants from objectlist, obtained
    by calling getiotapaths().
    """
    paths = getiotapaths(objectlist, keywordlist, pivot, target, {})
    return makeiota(paths, objectlist, pivot)

def makeiota(paths, objectlist, pivot):
    """From a dictionary of paths, indexed by indices to constants in
    objectlist, all from the pivot to a certain variable compatible with these
    constants, make an inclusion term (a 'iota' term). The inclusion term acts
    as a list of conditions on pivot. The inclusion term is sorted so that the
    order in which paths are stored in the dictionary is irrelevant to the
    result.
    """
    args = []
    for k in paths.keys():
        if paths[k][len(paths[k]) - 1].domain == pivot:
            const = objectlist[k]
            arg1 = makecomposition(paths[k])
            arg2 = makecomposition([const, alle(pivot)])
            if terminlist(arg1, args):
                arg2old = args[args.index(arg1) + 1]
                if arg2.__repr__() > arg2old.__repr__():
                    args.remove(arg1)
                    args.remove(arg2old)
                    args = insertsorted(args, arg1, arg2)
            else:
                args = insertsorted(args, arg1, arg2)
    return makeinclusion(args)

def insertsorted(args, arg1, arg2):
    """Insert into args the arguments arg1 and arg2 (right after each other),
    such that the list args remains sorted with respect to the arg1 arguments;
    these are the arguments with even index in args. As sorting criterium, the
    string representation of arg1 is used, obtained by the .__repr__() method.
    """
    i = 0
    while i < len(args) and args[i].__repr__() > arg1.__repr__():
        i += 2
    args.insert(i, arg1)
    args.insert(i + 1, arg2)
    return args

def getpathstoconstants(cluesasobjs, objectlist, pivot, target, hints):
    """Return a dictionary of paths from the pivot to the codomains of the
    constants in objectlist that are indexed by the keys of the cluesasobjs
    dictionary. For each constant (index) k, look into the list of clues
    obtained by cluesasobjs[k] and pass these clues as arguments to the
    getoptimalpath() routine in order to find a path that best matches these
    clues. Also, see if one of the clues is a variable that corresponds with
    the constant, and append it to the optimal path. Otherwise, choose a
    default variable and append that. Return a dictionary of all paths that is
    indexed by the same indices taken from cluesasobjects (which are all
    indices to constants in objectlist). As an extra argument to
    getoptimalpath(), a hint can be given, obtained from the dictionary hints.
    """
    paths = {}
    for k in cluesasobjs.keys():
        const = objectlist[k]
        clues = []
        destinationvar = None
        for o in cluesasobjs[k]:
            if o.__class__.__name__ == 'Variable' and o.codomain == const.codomain:
                destinationvar = o
            else:
                clues.append(o)
        if destinationvar == None:
            destinationvar = prefvar[const.codomain]
        destination = destinationvar.domain
        if pivot != target:
            clues.append(target)
        if k in hints.keys() and hints[k] != []:
            hint = hints[k][1:]
        else:
            hint = []
        paths[k] = getoptimalpath(graph.get_paths(pivot, destination), clues, hint)
        paths[k].insert(0, destinationvar)
    return paths
    

def getcluesasobjects(cluedict, objectlist, keywordlist):
    """Remove occurences of '-1' from the cluedict dictionary. Also resolve
    clashes: occurrences in two separate lists in cluedict of the same index.
    If such a list contains other indices, then remove that index from the list
    and keep it in the shorter list. If both lists only contain one identical
    index, then choose to keep it from the first and delete it from the
    second. Then replace the indices in the lists from cluedict with actual
    objects from objectlist and return the resulting dictionary.
    """
    # copy indices not equal to -1 from the cluedict into cluedictcleanup
    cluedictcleanup = {}
    for k in cluedict.keys():
        i = 0
        cluedictcleanup[k] = []
        while i < len(cluedict[k]):
            if cluedict[k][i] != -1:
                cluedictcleanup[k].append(cluedict[k][i])
            i += 1
    # see if there are any clashes in cluedictcleanup and resolve them
    clashes = getclashes(cluedictcleanup)
    for c in clashes.keys():
        for i in clashes[c]:
            if len(cluedictcleanup[i]) > 1:
                cluedictcleanup[i].remove(c)
    clashes = getclashes(cluedictcleanup)
    for c in clashes.keys():
        n = len(keywordlist)
        j = -1
        for i in clashes[c]:
            if n > abs(c - i):  ####
                n = abs(c - i)  ####
                j = i           ####
            # if clashes[c].index(i) + 1 != len(clashes[c]):
        for i in clashes[c]:    ####
            if i != j:          ####
                cluedictcleanup[i].remove(c)
    # now look for otrs and categorical vars that have not been assigned as a clue and distribute them
    k = 0
    while k < len(keywordlist):
        if keywordlist[k] == '<otr>' or keywordlist[k] == '<catvar>':
            found = False
            for i in cluedictcleanup.keys():
                if k in cluedictcleanup[i]:
                    found = True
            if not found:
                for i in cluedictcleanup.keys():
                    if objectlist[k].codomain == objectlist[i].codomain or graph.get_paths(objectlist[k].codomain, objectlist[i].codomain) != []:
                        cluedictcleanup[i].append(k)
        k += 1
    cluesasobjects = {}
    # copy related objects in cluesasobjects
    for k in cluedictcleanup.keys():
        cluesasobjects[k] = []
        for i in cluedictcleanup[k]:
            cluesasobjects[k].append(objectlist[i])
    return cluesasobjects

def getclashes(cluedict):
    """Collect a dictionary of clashes from the dictionary cluedict. A clash
    is a number c (which is an index for keywordlist) that occurs in both the
    list cluedict[k] and in the list cluedict[l] (with k != l). In such a case,
    getclashes() returns a dictionary clashes with clashes[c] = [k, l].
    """
    clashes = {} # stores for each clash the list of keys in cluedict responsible for the clash
    for k in cluedict.keys():
        i = 0
        while i < len(cluedict[k]):
            for l in cluedict.keys():
                if l != k and cluedict[k][i] in cluedict[l]: # clash discovered
                    if cluedict[k][i] not in clashes.keys():
                        clashes[cluedict[k][i]] = [k]
                    else:
                        clashes[cluedict[k][i]].append(k)
            i += 1
    return clashes

def getclues(k, keywordlist):
    """Get the context of index k in keywordlist: a list of four indices for
    keywordlist, two right before k and two right after k, to keywords that are
    not equal to '<unk>'. Match this context with a list of patterns and
    collect indices for keywordlist to a certain clue in each pattern. For
    instance, the pattern ['<otr>, '<prep>', '*'] with 0 as index to the clue,
    looks for the pattern '<otr><prep>' in keywordlist before k (discarding
    occurrences of '<unk>') and if this matches, it returns the index in
    keywordlist to the occurrence of the '<otr>' keyword. The special marker
    '*' indicates the position of k relative to the keywords in the pattern.
    """
    clues = []
    context = getcontext(k, keywordlist)
    clues.append(getclueindexfrompattern(['<otr>', '<prep>', '*'], 0, context, keywordlist))
    clues.append(getclueindexfrompattern(['<prep>', '*', '<otr>'], 2, context, keywordlist))
    clues.append(getclueindexfrompattern(['<catvar>', '*'], 0, context, keywordlist))
    clues.append(getclueindexfrompattern(['*', '<catvar>'], 1, context, keywordlist))
    clues.append(getclueindexfrompattern(['*', '<whowhat>', '<otr>'], 2, context, keywordlist)) # dubious
    return clues

def getkappa(objectlist, keywordlist, pivot, target, iota, paths, split):
    """If pivot does not equal target, a kappa term must be constructed out of
    a path connecting the two. A kappa term associated with, e.g., the pivot
    'baan' and the target 'persoon' (through the 'werknemer' object type
    relation) selects those objects from 'persoon' that have a job ('baan'),
    i.e., it selects the range of the object type relation 'werknemer'. If
    there are selection criteria applicable to pivot (i.e., iota is not equal
    to None) then iota must be appended to the path connecting pivot to target.
    In order to find the path connecting pivot and target, as a heuristic get
    all object types, object type relations and constants from objectlist and
    pass them as clues to the getoptimalpath() routine.
    """
    # if pivot == target:
    #     return iota
    # else:
    paths = appendvariablestopaths(paths)
    if pivot != target:
        clues = []
        i = 0
        while i < len(keywordlist):
            if keywordlist[i] == '<ot>' or keywordlist[i] == '<otr>' or keywordlist[i] == '<const>':
                clues.append(objectlist[i])
            # if keywordlist[i] == '<const>' and objectlist[i].codomain in overridetarget.keys():
            #     clues.append(overridetarget[objectlist[i].codomain])
            i += 1
        if split != None:
            path = getoptimalpath(graph.get_paths(pivot, split), clues, [])
            paths.insert(0, path)
        path = getoptimalpath(graph.get_paths(pivot, target), clues, [])
        paths.insert(0, path)
    selcsterm = makeselections(paths)
    if selcsterm != None and iota != None:
        u = makecomposition([selcsterm, iota])
    elif selcsterm == None:
        u = iota
    elif iota == None:
        u = selcsterm
    if pivot != target and u != None:
        u = makekappa([u])
    return u

def makeselections(paths):
    """From a list of paths originating from a common source, make a product
    of compositions.
    """
    selcs = []
    for path in paths:
        if path != []:
            arg = makecomposition(path)
            selcs.append(arg)
    selcsterm = makeproduct(selcs)
    return selcsterm