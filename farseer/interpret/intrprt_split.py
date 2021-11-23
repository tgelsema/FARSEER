#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 11:25:08 2019

@author: tgelsema

The routines that the package farseer.interpret.intrprt_split exposes, viz.
getsplit(), getsplitfromkappa() and getsplitfromobjectlist(), are all to serve
the intrprt.assembletermforclass5() routine only. There, a formula is built of
the general form
    a(v, w) / a(een(p), u) o c
and the split p is the object type counted in the denominator. For instance, in
the case 'gemiddeld aantal banen van griffiers van bedrijven in Delft', the
token 'bedrijven' (or rather: 'bedrijf') should be treated as a split, since a
ratio is requested of the number of 'griffier' jobs and the number of
'bedrijven' in 'Delft'. Note that a split should never be treated as a
dimension, and the routine farseer.interpret.intrprt_dims.getdimensionpaths()
has an option 'ignoresplit' to ignore an object type that serves as a split.

The getsplit(), getsplitfromkappa() and getsplitfromobjectlist() have different
strategies to detect a split from an objectlist and a keywordlist. In
intrprt.assembletermforclass5(), the first is the default, and the latter two
must be seen as cases of last resort, if the first does not succeed to come up
with a split. A pseudodimension (for class 6-11 requests) is never a split, so
in intrprt.assembletermforclass11() it is passed in the list 'nosplits'.
"""


from farseer.term.trm import Application
from farseer.graphdb.graphdb import graph

def getsplit(objectlist, keywordlist, target, paths, nosplits):
    """Return the 'split' of a query as represented by objectlist and
    keywordlist: an object type that occurs in objectlist and does not equal
    the target. Split must be an object type that occurs somewehere as a
    codomain in paths. As a heuristic, return the split 'closest' to
    target, if multiple splits are found.
    """
    potentialsplits = getpotentialsplits(objectlist, keywordlist, target, nosplits)
    split = None
    for p in potentialsplits:
        for path in paths:
            for d in path:
                if not isinstance(d, Application) and d.codomain.equals(p):
                    if split == None or (graph.get_paths(p, split) != [] and graph.get_paths(target, p) != []):
                        split = p
    return split

def getpotentialsplits(objectlist, keywordlist, target, nosplits):
    """Return a list of split candidates, excluding target and the object types
    that are passed as an argument in the nosplit list. Pick the object types
    from object list with the same index as occurrences of '<ot>' in
    keywordlist.
    """
    potentialsplits = []
    i = 0
    while i < len(keywordlist):
        if keywordlist[i] == '<ot>':
            if objectlist[i] != target and not objectlist[i] in nosplits:
                potentialsplits.append(objectlist[i])
        i += 1
    return potentialsplits

def getsplitfromkappa(objectlist, keywordlist, target, kappa, nosplits):
    """The routine getsplit() is usually called with the paths to dimensions as
    an argument. A different use of getsplit() is given when paths derived from
    kappa (or rather: iota) are used.
    """
    paths = getpathsfromkappa(kappa)
    return getsplit(objectlist, keywordlist, target, paths, nosplits)

def getsplitfromobjectlist(objectlist, keywordlist, target, nosplits):
    """Return the first object type, if it exists, from the list obtained by
    the getpotentialsplits() routine, otherwise return None.
    """
    potentialsplits = getpotentialsplits(objectlist, keywordlist, target, nosplits)
    if potentialsplits != []:
        return potentialsplits[0]
    else:
        return None
    
def getpathsfromkappa(kappa):
    """Return a list of paths derived from a iota term (possibly inside a kappa
    term). For each selection condition of the form 'v = c', where v represents
    (a path from pivot to) a variable, and c is (a term containing) a constant,
    take the (path to the) variable and collect it in a list, paths. Return
    paths.
    """
    if kappa == None:
        return []
    if kappa.op.name == 'inverse':
        c = kappa.args[0]
        iota = c.args[len(c.args) - 1]
    else:
        iota = kappa
    paths = []
    i = 0
    while i < len(iota.args):
        if i % 2 == 0:
            if iota.args[i].__class__.__name__ == 'Application':
                if iota.args[i].op.name == 'composition':
                    paths.append(iota.args[i].args)
            else:        
                paths.append([iota.args[i]])
        i += 1
    return paths