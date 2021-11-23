#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 11:13:43 2019

@author: tgelsema

This package exposes three similar routines, viz. getpathstonumvars(),
getpathstocatvars() and getpathstoobjecttypes() that return paths from the
target to all numerical variables, all categorical variables and all object
types in objectlist, respectively. These are used only once, viz. in the
beginning of the farseer.interpret.intrprt.interpret() routine, right after
which these paths are turned into proper compositions (i.e., formulas). The
getpathfromvar() routine is used only once, viz in assembletermforclass6(),
where a path from the domain of a variable to a pseudo dimension is sought.
"""

from farseer.interpret.intrprt_base import insertsorted, getoptimalpath
from farseer.graphdb.graphdb import graph

def getpathfromvar(objectlist, keywordlist, var, dest):
    """Return a path from the domain of var to target, using the
    getoptimalpath() routine, with all object type relations in objectlist as
    clues. The getpathfromvar() routine is only used by the
    farseer.interpret.intrprt.assembletermforclass6() routine, where dest is
    a pseudodimension.
    """
    i = 0
    clues = []
    while i < len(keywordlist):
        if keywordlist[i] == '<otr>':
            clues.append(objectlist[i])
        i += 1
    return getoptimalpath(graph.get_paths(var.domain, dest), clues, [])

def getpathstonumvars(objectlist, keywordlist, target):
    """Return paths from target to the domains of all numerical variables that
    occur in objectlist (pointed at by keywordlist, by the keyword '<numvar>').
    The getoptimalpath() routine is used to find these paths, and as clues, all
    object type relations in objectlist are taken. Exclude the numerical
    variables that have target as domain (since then the path is empty). Append
    the numerical variable to each path.
    """
    paths = []
    i = 0
    clues = []
    while i < len(keywordlist):
        if keywordlist[i] == '<otr>':
            clues.append(objectlist[i])
        i += 1
    i = 0
    while i < len(keywordlist):
        if keywordlist[i] == '<numvar>':
            if isinstance(objectlist[i], list):
                var = objectlist[i][0]
            else:
                var = objectlist[i]
            path = []
            if not var.domain.equals(target):
                path = getoptimalpath(graph.get_paths(target, var.domain), clues, [])
            path.insert(0, var)
            paths = insertsorted(paths, path)
        i += 1
    return paths

def getpathstocatvars(objectlist, keywordlist, target):
    """Similar to the getpathstonumvar() routine, but in getpathstocatvars(),
    paths from target to categorical variables are returned.
    """
    paths = []
    i = 0
    clues = []
    while i < len(keywordlist):
        if keywordlist[i] == '<otr>':
            clues.append(objectlist[i])
        i += 1
    i = 0
    while i < len(keywordlist):
        if keywordlist[i] == '<catvar>':
            var = objectlist[i]
            path = []
            if not var.domain.equals(target):
                path = getoptimalpath(graph.get_paths(target, var.domain), clues, [])
            path.insert(0, var)
            paths = insertsorted(paths, path)
        i += 1
    return paths

def getpathstoobjecttypes(objectlist, keywordlist, pivot, target):
    """Similar to the getpathstocatvars() and getpathstonumvars() routines, but
    getpathstoobjecttypes() returns paths from target to all object types in
    objectlist. Obviously, paths from target to the pivot are excluded (since
    nonexistent or empty).
    """
    paths = []
    i = 0
    clues = []
    while i < len(keywordlist):
        if keywordlist[i] == '<otr>':
            clues.append(objectlist[i])
        i += 1
    i = 0
    while i < len(keywordlist):
        if keywordlist[i] == '<ot>':
            if not objectlist[i].equals(pivot) and not objectlist[i].equals(target):
                path = getoptimalpath(graph.get_paths(target, objectlist[i]), clues, [])
                if path != None and path != []:
                    paths = insertsorted(paths, path)
        i += 1
    return paths