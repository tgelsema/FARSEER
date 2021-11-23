#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 10:40:17 2019

@author: tgelsema

This package exposes many short routines used by the various interpret.intrprt
packages. Notably the package exposes graph.get_paths() and getoptimalpath() that,
respectively, return all paths from the knowledge graph, given two vertices,
and select from them a path that is 'optimal' in some sense, given 'clues' and
'hints', which act like 'pebbles' on a path.
The package also exposes the 'safe' make...() routines, e.g., makealpha(args)
returns an alpha term based on the arguments given by args. This is just a
convenient and safe way of calling Application(alpha, args), as makealpha()
returns a default of None if the list args is not of the appropriate length.
Other make...() routines behave similarly.
The interpret.intrprt_base package is also the appropriate entry point for
referencing the 'een(p)' and 'alle(p)' variables: these are retrieved from the
knowlegde graph, if they exist, and otherwise they are constructed. (Note: the
latter is not safe, as equality of variables is based on their ID, so make
sure they exist in the knowledge graph.)
"""

from farseer.graphdb.dm import whichway, getal, overridetarget, one
from farseer.term.trm import Application, product, composition, cartesian_product, projection, alpha, inverse, inclusion
from farseer.kind.knd import ObjectType, Variable
from farseer.graphdb.graphdb import graph

def getdomainlist(term):
    """Return the arguments of a Cartesian product as a list, if the domain of
    term is such a product. Return a list just containing the domain otherwise.
    Note that getdomainlist() works for a term that is a projection: in such a
    case, the domain is a Cartesian product (in contrast to a product: in that
    case the codomain is a Cartesian product).
    """
    if isinstance(term.type.args[0], Application):
        if term.type.args[0].op == cartesian_product:
            return term.type.args[0].args
    return [term.type.args[0]]

def align(term1, term2):
    """Align term1 with term2 in the case in which:
        - both have a domain consisting of a Cartesian product (i.e., they are
          projections, or products of projections), and
        - the domain of term1 is a 'subset' of the domain of term2.
        In that case, return an equivalent form of term1 that has the same
        domain as term2, by composing term1 with appropriate projections. As
        an example, consider:
            t1: <p(p1, p2, 1), p(p1, p2, 2)> : [(p1 x p2) -> (p1 x p2)]
            t2: <p(p1, p2, p3, 1), p(p1, p2, p3, 3)> : [(p1 x p2 x p3) -> (p1 x p3)]
            align(t1, t2): (<p(p1, p2, 1), p(p1, p2, 2)> o <p(p1, p2, p3, 1), p(p1, p2, p3, 2)>) : [(p1 x p2 x p3) -> (p1 x p2)].
        Some special attention is given in the case the domain of term1
        contains the type 'one': not sure though if align() is safe in these
        cases: perhaps rewrite when necessary.
    """
    t1domlist = getdomainlist(term1)
    t2domlist = getdomainlist(term2)
    if t1domlist == t2domlist:
        return term1
    args = []
    for d in t1domlist:
        if d != one:
            if not d in t2domlist:
                return None
            else:
                args.append(makeprojection(t2domlist + [t2domlist.index(d) + 1]))
        else:
            return makecomposition([term1, alle(makecartesianproduct(t2domlist))])
    return makecomposition([term1, makeproduct(args)])

def isprefix(p, q):
    """Return True iff the list p is a prefix of the list q.
    """
    return len(q) >= len(p) and q[:len(p)] == p

def ispostfix(p, q):
    """Return True iff the list p is a postfix of the list q.
    """
    return len(q) >= len(p) and q[len(q) - len(p):] == p

def getoptimalpath(paths, clues, hint):
    """From a list of paths (a list of lists) having common origin and common
    destination, select one path that is preferred, using 'clues' and a 'hint'.
    A hint is a path, and if this matches a prefix of a path p in 'paths',
    return the first such p in paths encountered. In this way, a hint can
    override a selection based on clues. Otherwise (i.e., if no hint applies)
    use heuristics based on the clues list. The clues list can contain both
    edges and vertices; if an edge in clues matches an edge in a path
    considered: reward that path with special points (10). If a vertice in
    clues matches a domain or a codomain in an edge in a path: reward 4 points.
    Also note that the getoptimalpath() routine makes use of the whichway list,
    in the domain model, that serves as extra clues.
    Return the paths with the highest points awarded. If two paths score the
    same number of points, select the longest of the two (?).
    """
    optimalpath = []
    n = -1
    for path in paths:
        if hint != []:
            if isprefix(hint, path):
                return path
        k = 0
        for edge in path:
            for clue in clues:
                if edge.equals(clue):
                    k += 10
                if edge.domain.equals(clue) or edge.codomain.equals(clue):
                    k += 4
                if clue.kind == 'element' and clue.domain.equals(one) and clue.codomain in overridetarget.keys():
                    otype = overridetarget[clue.codomain]
                    if edge.domain.equals(otype) or edge.codomain.equals(otype):
                        k += 2
            if edge.domain in whichway.keys():
                if edge == whichway[edge.domain]:
                    k += 1
        if k > n:
            n = k
            optimalpath = path
        elif k == n and len(optimalpath) < len(path):
            optimalpath = path
    return optimalpath

def makecomposition(args):
    """Make a composition term from the list of arguments args by calling
    term.Application(). Return None if args is empty and return args[0] if args
    contains just one element.
    """
    if len(args) == 0:
        return None
    elif len(args) == 1:
        return args[0]
    else:
        return Application(composition, args)
    
def makeproduct(args):
    """Make a product term from the list of arguments args by calling
    term.Application(). Return None if args is empty and return args[0] if args
    contains just one element.
    """
    if len(args) == 0:
        return None
    elif len(args) == 1:
        return args[0]
    else:
        return Application(product, args)
    
def makecartesianproduct(args):
    """Make a Cartesian product term from the list of arguments args by calling
    term.Application(). Return None if args is empty and return args[0] if args
    contains just one type.
    """
    if len(args) == 0:
        return None
    elif len(args) == 1:
        return args[0]
    else:
        return Application(cartesian_product, args)
    
def makealpha(args):
    """Make an alpha term from the list of arguments args by calling
    term.Application() or return None if args is not of appropriate length.
    """
    if len(args) != 2:
        return None
    else:
        return Application(alpha, args)
    
def makeprojection(args):
    """Make a projection term from the list of arguments args by calling
    term.Application() or return None if args is not of appropriate length.
    """
    if len(args) < 2:
        return None
    else:
        return Application(projection, args)
    
def makeprojectioneasy(arg, n):
    """Make the n-th projection term from the term arg in case arg is a product
    term (or rather: its codomain is a Cartesian product) and compose it with
    arg in that case. Otherwise, just return arg.
    """
    if not isinstance(arg.type.args[1], Application):
        return arg
    if arg.type.args[1].op != cartesian_product:
        return arg
    pargs = arg.type.args[1].args.copy()
    pargs.append(n)
    return makecomposition([makeprojection(pargs), arg])
    
def makekappa(args):
    """Make a range (kappa) term from the list of arguments args by calling
    term.Application() or return None if args is not of appropriate length.
    """
    if len(args) != 1:
        return None
    else:
        return Application(inverse, args)
    
def makeinclusion(args):
    """Make an inclusion term from the list of arguments args by calling
    term.Application() or return None if args is not of appropriate length.
    """
    if len(args) < 2:
        return None
    else:
        return Application(inclusion, args)
    
def terminlist(term, lst):
    """Return True iff (a copy of) term is present in the list lst. As
    matching criterium, use the string representation __repr__() of term.
    """
    for t in lst:
        if t.__repr__() == term.__repr__():
            return True
    return False

def een(p: ObjectType) -> Variable:
    """
    Return a variable with domain=p (with p an object type) and codomain=getal,
    named 'een(p)'. This variable should exist in the graph. 
    Otherwise, it is created and added to the domainmodel dictionary. 

    Args:
        p (ObjectType): ObjectType connected to 'getal' by een(p)

    Returns:
        Variable: variable connecting objecttype p to 'getal'
    """
    title = "een(%s)" % p.name
    een = graph.get_kind(title, 'Variable')
    if een:
        return een
    else:
        een = Variable(name=title, domain=p, codomain=graph.getal)
        graph.rebuilt_dm.update({title: een})
        return een

def alle(p: ObjectType) -> Variable:
    """
    Return a variable with domain=p (with p an object type) and codomain=one,
    named 'alle(p)'. This variable should exist in the graph. 
    Otherwise, it is created and added to the domainmodel dictionary. 

    Args:
        p (ObjectType): variable connecting objecttype p to 'getal' 

    Returns:
        Variable: alle(p)
    """
    
    title = "alle(%s)" % p.__repr__()
    a = graph.get_kind(title, 'Variable')
    if a:
        return a
    else:
        a = Variable(name=title, domain=p, codomain=graph.one)
        graph.rebuilt_dm.update({title: a})
        return Variable(name=title, domain=p, codomain=graph.one)


def lookforward(k, keywordlist):
    """In keywordlist at position k, return the index to the next keyword not
    equal to '<unk>'. Return len(keywordlist) if no such keyword exists.
    """
    n = k + 1
    while n < len(keywordlist) and keywordlist[n] == '<unk>':
        n += 1
    return n

def lookback(k, keywordlist):
    """In keywordlist at position k, return the index to the previous keyword
    not equal to '<unk>'. Return -1 if no such keyword exists.
    """
    n = k - 1
    while n >= 0 and keywordlist[n] == '<unk>':
        n -= 1
    return n

def getcontext(k, keywordlist):
    """In keywordlist indexed by k, get the two keywords (not equal to '<unk>')
    in the keywordlist ahead of index k (if they exist) as well as the two
    keywords (not equal to '<unk>') before k (if they exist). Return a list of
    the indices to these four keywords.
    """
    f1 = lookforward(k, keywordlist)
    f2 = lookforward(f1, keywordlist)
    b1 = lookback(k, keywordlist)
    b2 = lookback(b1, keywordlist)
    return [b2, b1, f1, f2]

def getclueindexfrompattern(pattern, clueidx, context, keywordlist):
    """Get the index in keywordlist to a clue, a keyword that is indexed by
    clueidx in pattern, if that pattern matches with context. Context is a list
    of four indices for keywordlist: two indices before a certain index k and
    two indices after k. Pattern is a list with a length not exceeding the
    length of context + 1 of keys, that contains a special marker '*'
    indicating the position for k.
    """
    centeroffset = pattern.index('*')
    match = True
    patternidx = 0
    pastcenter = 0
    while match and patternidx < len(pattern):
        if patternidx != centeroffset:
            if context[patternidx + len(context) // 2 - centeroffset - pastcenter] == None:
                match = False
            elif context[patternidx + len(context) // 2 - centeroffset - pastcenter] >= len(keywordlist):
                match = False
            elif context[patternidx + len(context) // 2 - centeroffset - pastcenter] < 0:
                match = False
            elif pattern[patternidx] != keywordlist[context[patternidx + len(context) // 2 - centeroffset - pastcenter]]:
                match = False  
        else:
            pastcenter = 1
        patternidx += 1
    if match:
        if clueidx > centeroffset:
            pastcenter = 1
        else:
            pastcenter = 0
        return context[clueidx + len(context) // 2 - centeroffset - pastcenter]
    else:
        return -1
    
def getindexfrompattern(pattern, patternidx, index, keywordlist, discardunk):
    """Match the first occurrence of pattern in keywordlist starting at index
    and return the index in keywordlist matching with patternidx in pattern.
    Discard occurrences of '<unk>' in keywordlist. Also: assume that pattern
    does not include occurrences of '<unk>'.
    """
    i = index
    while i < len(keywordlist) and i >= 0:
        j = match(pattern, patternidx, i, keywordlist, discardunk)
        if j != -1:
            return j
        i += 1
    return -1

def match(pattern, patternidx, index, keywordlist, discardunk):
    """Return True if pattern matches with keywordlist starting at index, else
    return False. Discard occurrences of '<unk>' in keywordlist, except if
    keywordlist[index] == '<unk>': in that case, return False.
    """
    foundindex = -1
    if index >= len(keywordlist) or index < 0 or keywordlist[index] == '<unk>':
        return -1
    if patternidx >= len(pattern) or patternidx < 0:
        return -1
    i = index
    j = 0
    while j < len(pattern):
        if i + j >= len(keywordlist) or i + j < 0:
            return -1
        if pattern[j] != keywordlist[i + j] and not discardunk:
            return -1
        if pattern[j] != keywordlist[i + j] and keywordlist[i + j] != '<unk>':
            return -1
        if j == patternidx:
            foundindex = i + j
        if keywordlist[i + j] == '<unk>' and discardunk:
            i += 1
        else:
            j += 1
    return foundindex

def insertsorted(lst, obj):
    """Insert into lst the argument obj, such that the list lst remains
    sorted. As sorting criterium use the string representation of obj,
    obtained by the .__repr__() method. Return the list lst with obj inserted.
    """
    i = 0
    while i < len(lst) and lst[i].__repr__() > obj.__repr__():
        i += 1
    lst.insert(i, obj)
    return lst