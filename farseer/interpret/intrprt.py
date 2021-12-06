#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 10:40:17 2019

@author: tgelsema

This package exposes the main entry point for the semantic analysis stage of
the Farseer framework: the interpret() routine. (Other routines that are
exposed in this package should only be addressed from interpret() and not by
themselves.) Given the lists 'tokenlist', 'objectlist' and 'keywordlist' and
the estimations for the target and the class (from the
farseer.intrprt_pivot.gettarget() routine and the appropriate routines of the
'learn' package) of a request from the early NLP stages of Farseer,
interpret() returns a formula that forms the semantics of the request.

Note that interpret() returns a term (as defined by the farseer.term and
farseer.kind packages) or a list consisting of a term, a variable (according to
farseer.kind) and an order condition ('asc' or 'desc'); the latter appear as a
result of interpret() in the case of a request of class 6, 7, 8, 9, 10, or 11.
In all other cases, a single term is returned.
"""

from farseer.interpret.intrprt_iota import getiota, getkappa, getiotapaths, makeiota
from farseer.interpret.intrprt_pivot import getpivot, getpseudodimension, getnexttarget
from farseer.interpret.intrprt_dims import getdimensionpaths, appendvariablestopaths
from farseer.interpret.intrprt_base import een, alle, makecomposition, makeproduct, makealpha, makeprojectioneasy, align
from farseer.interpret.intrprt_split import getsplit, getsplitfromkappa, getsplitfromobjectlist
from farseer.interpret.intrprt_vars import getpathstonumvars, getpathstocatvars, getpathstoobjecttypes, getpathfromvar
from farseer.graphdb.dm import gedeelddoor, defaults, orderedobjecttype
from farseer.term.trm import InvalidApplication
from farseer.graphdb.graphdb import graph

def interpret(tokenlist, objectlist, keywordlist, target, cls):
    """From the output of the first stage of Farseer, i.e., the lists
    tokenlist, objectlist and keywordlist that are the result of the
    tokenize routine, together with the estimated class of a request (cls) and
    the estimated target, compute a term that forms the semantics of the
    request. After computing the pivot and some general purpose information,
    divert the computation of the term to one of several routines, according
    to the 11 classes currently considered.
    Note that the output of interpret can be a single term, or a list
    consisting of a term, a variable that is the subject of ordering, and an
    indication of order ('asc' or 'desc').
    """
    pivot = getpivot(objectlist, keywordlist)
    if pivot == None:
        return None
    if not pivot.equals(target):
        if graph.get_paths(pivot, target) == []:
            return None
    pathstonumvars = getpathstonumvars(objectlist, keywordlist, target)
    pathstoclassvars = getpathstocatvars(objectlist, keywordlist, target)
    pathstootypes = getpathstoobjecttypes(objectlist, keywordlist, pivot, target)
    pathstootypes = appendvariablestopaths(pathstootypes)
    order = getorder(keywordlist)
    numvars = []
    classvars = []
    otypes = []
    for path in pathstonumvars:
        numvars.append(makecomposition(path))
    for path in pathstoclassvars:
        classvars.append(makecomposition(path))
    for path in pathstootypes:
        otypes.append(makecomposition(path))
    iota = getiota(objectlist, keywordlist, pivot, target)
    if cls == 1:
        kappa = getkappa(objectlist, keywordlist, pivot, target, iota, [], None)
        return assembletermforclass1(target, numvars, classvars, otypes, kappa, True)
    elif cls == 2:
        (pathsfrompivot, ignore) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
        return assembletermforclass2and3(objectlist, keywordlist, pivot, target, pathsfrompivot, [], iota, None)
    elif cls == 3:
        (pathsfrompivot, ignore) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
        return assembletermforclass2and3(objectlist, keywordlist, pivot, target, pathsfrompivot, numvars, iota, None)
    elif cls == 4:
        (pathsfrompivot, ignore) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
        return assembletermforclass4(objectlist, keywordlist, pivot, target, pathsfrompivot, numvars, iota)
    elif cls == 5:
        (pathsfrompivot, ignore) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
        kappa = getkappa(objectlist, keywordlist, pivot, target, iota, pathsfrompivot, None)
        return assembletermforclass5(objectlist, keywordlist, pivot, target, pathsfrompivot, kappa, [])
    elif cls == 6:
        return assembletermforclass6(objectlist, keywordlist, target, iota, order)
    elif cls == 7:
        return assembletermforclass7(objectlist, keywordlist, tokenlist, target, pivot, iota, order)
    elif cls == 8:
        return assembletermforclass8(objectlist, keywordlist, tokenlist, target, pivot, numvars, iota, order)
    elif cls == 9:
        return assembletermforclass9(objectlist, keywordlist, tokenlist, target, pivot, numvars, iota, order)
    elif cls == 10:
        kappa = getkappa(objectlist, keywordlist, pivot, target, iota, [], None)
        return assembletermforclass10(objectlist, keywordlist, tokenlist, target, numvars, otypes, kappa, order)
    elif cls == 11:
        kappa = getkappa(objectlist, keywordlist, pivot, target, iota, [], None)
        return assembletermforclass11(objectlist, keywordlist, tokenlist, target, pivot, kappa, order)
    elif cls == 0:
        return None
    return None

def getorder(keywordlist):
    """Simple routine to detect whether '<most>' or '<greatest>' occurs in
    keywordlist, in which case 'desc' is returned, or whether '<least>' or
    '<smallest>' occurs in keywordlist, in which case 'asc' is returned. When
    neither occurs in keywordlist, return ''.
    """
    i = 0
    while i < len(keywordlist):
        if keywordlist[i] == '<most>' or keywordlist[i] == '<greatest>':
            return 'desc'
        if keywordlist[i] == '<least>' or keywordlist[i] == '<smallest>':
            return 'asc'
        i += 1
    return ''

def insertpseudodimension(objectlist, keywordlist, tokenlist, pseudodimension):
    """For class 7 - 11 queries, say of the form
        'Welke gemeente heeft gemiddeld het grootste aantal personen op een
        adres?'
    which have an object type ('gemeente', a pseudodimension),
    that has to act as a dimension in the resulting term. A little trick is
    used to let the routine getdimenionpaths() detect this dimension: just in
    front of the object type (the pseudodimension) the word 'per' is inserted
    in tokenlist and suitable other terms are inserted in keywordlist and
    tokenlist. If the pseudodimension is not found (as in the case that
    pseudodimension is 'persoon', but that has been derived from a constant,
    'griffier' say) the words 'per persoon' are inserted at the end of
    tokenlist.
    """
    i = 0
    while i < len(keywordlist) and objectlist[i] != pseudodimension:
        i += 1
    if i != len(keywordlist):
        keywordlist.insert(i, '<per>')
        objectlist.insert(i, None)
        tokenlist.insert(i, 'per')
    else:
        keywordlist.insert(i, '<per>')
        keywordlist.insert(i + 1, '<ot>')
        objectlist.insert(i, None)
        objectlist.insert(i + 1, pseudodimension)
        tokenlist.insert(i, 'per')
        tokenlist.insert(i + 1, pseudodimension.__repr__())
    return (objectlist, keywordlist, tokenlist)

def assembletermforclass11(objectlist, keywordlist, tokenlist, target, pivot, kappa, order):
    """Build a term for class 11 queries, which are of the general form
        'Welke gemeente heeft gemiddeld het grootste aantal personen op
        een adres?'
    which requires calculating an average and a total. Queries of class 11 are
    thus ditributed to class 5, after a (pseudo-) dimension is inserted into
    objectlist, keywordlist and tokenlist. In the example above, the average
    number of persons per 'adres' is calculated for each 'gemeente', so
    'gemeente' forms the (pseudo-) dimension here.
    """
    pseudodimension = getnexttarget(objectlist, keywordlist)
    if pseudodimension == None:
        return None
    (objectlist, keywordlist, tokenlist) = insertpseudodimension(objectlist, keywordlist, tokenlist, pseudodimension)
    (paths, ignoredict) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
    return [assembletermforclass5(objectlist, keywordlist, pivot, target, paths, kappa, [pseudodimension]), een(target), order]

def assembletermforclass10(objectlist, keywordlist, tokenlist, target, numvars, otypes, kappa, order):
    """Build a term for class 10 queries, which are of the form
        'In welke gemeente wordt het meeste verdiend'
    and which does not require aggregation. (Note that this differs from a
    query of the form
        'In welke gemeente wordt in totaal het meeste verdiend'
    which is of type 8). Type 10 queries are thus distributed to class 1, where
    all object types (and variables) in the query (objectlist) are treated as
    variables.
    """
    pseudodimension = getnexttarget(objectlist, keywordlist)
    if pseudodimension == None:
        return None
    includetargetdefaults = False
    if pseudodimension == target:
        includetargetdefaults = True
    return [assembletermforclass1(target, numvars, [], otypes, kappa, includetargetdefaults), numvars[0], order]

def assembletermforclass9(objectlist, keywordlist, tokenlist, target, pivot, numvars, iota, order):
    """Build a term for class 9 queries, which are of the form
        'Welke gemeente heeft de kleinste gemiddelde leeftijd?'
    which requires calculating an average. Class 9 queries are thus distributed
    to class 4, after a (pseudo-) dimension is inserted into objectlist,
    keywordlist and tokenlist. In the example above, the average 'leeftijd' is
    calculated for each 'gemeente', so 'gemeente' forms the dimension for the
    class 4 query.
    """
    pseudodimension = getnexttarget(objectlist, keywordlist)
    if pseudodimension == None:
        return None
    (objectlist, keywordlist, tokenlist) = insertpseudodimension(objectlist, keywordlist, tokenlist, pseudodimension)
    (paths, ignoredict) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
    return [assembletermforclass4(objectlist, keywordlist, pivot, target, paths, numvars, iota), numvars[0], order]

def assembletermforclass8(objectlist, keywordlist, tokenlist, target, pivot, numvars, iota, order):
    """Build a term for class 8 queries, which are of the form
        'Op welk adres wordt het meeste verdiend in totaal?'
    which requires summing over a numerical variable. Class 8 queries are thus
    distributed to class 3, after a (pseudo-) dimension is inserted into
    objectlist, keywordlist and tokenlist. In the example above, the sum
    over 'inkomen' (verdiend) is calculated for each 'adres', so 'adres' forms
    the dimension for the class 3 query.
    """
    pseudodimension = getnexttarget(objectlist, keywordlist)
    if pseudodimension == None:
        return None
    (objectlist, keywordlist, tokenlist) = insertpseudodimension(objectlist, keywordlist, tokenlist, pseudodimension)
    (paths, ignoredict) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
    return [assembletermforclass2and3(objectlist, keywordlist, pivot, target, paths, numvars, iota, None), numvars[0], order]

def assembletermforclass7(objectlist, keywordlist, tokenlist, target, pivot, iota, order):
    """Build a term for class 7 queries, which are of the form
        'In welke gemeente wonen de meeste (minste) personen?'
    and which require counting. Class 7 queries are thus distributed
    to class 2, after a (pseudo-) dimension is inserted in objectlist,
    keywordlist and tokenlist. In the example above, 'gemeente' is the
    object type that is marked (by inserting 'per' just in front of it) as
    a dimension. In this way, 'personen' are counted for each 'gemeente'.
    """
    pseudodimension = getnexttarget(objectlist, keywordlist)
    if pseudodimension == None:
        return None
    (objectlist, keywordlist, tokenlist) = insertpseudodimension(objectlist, keywordlist, tokenlist, pseudodimension)
    (paths, ignoredict) = getdimensionpaths(objectlist, keywordlist, pivot, target, None, {})
    return [assembletermforclass2and3(objectlist, keywordlist, pivot, target, paths, [een(target)], iota, None), een(target), order]

def assembletermforclass6(objectlist, keywordlist, target, iota, order):
    """Build a term for class 6, which expresses a query of the form
        'Welke gemeente is het grootst (kleinst)?'
    or variants like
        'Wat is de grootste (kleinste) gemeente?'
    by distributing it to other classes (class 1 or class 3) depending on
    whether calculating the biggest (smallest) such cases requires
    aggregation. In case the variable associated with calculating the biggest
    (smallest) is a variable defined for target, aggregation is not necessary,
    as in the case
        'wat is het grootste bedrijf in Delft'
    depends on 'omzet' only, which is defined for 'bedrijf'. In the two cases
    above the calculation of the largest (smallest) 'gemeente' depends on
    aggregating over 'een(persoon)'.
    Consider using getnexttarget() instead of getpseudodimension(), as the
    latter is (almost) deprecated and functionally (probably) similar to
    getnexttarget().
    """
    pseudodimension = getpseudodimension(objectlist, keywordlist)
    if pseudodimension == None:
        return None
    if pseudodimension in orderedobjecttype.keys():
        var = orderedobjecttype[pseudodimension]
        print("found var: " + var.name)
        print("found pseudodimension: " + pseudodimension.name)
    else:
        return None
    if var.domain == pseudodimension:
        return [assembletermforclass1(target, [var], [], [], iota, True), var, order]
    else:
        path = getpathfromvar(objectlist, keywordlist, var, pseudodimension)
        return [assembletermforclass2and3(objectlist, keywordlist, var.domain, target, [path], [var], iota, None), var, order]   

def assembletermforclass1(target, numvars, classvars, otypes, kappa, includetargetdefaults):
    """Build a term for class 1, which expresses a number of variables for
    target, with or without selection criteria given by kappa. The resulting
    term is thus of the form
            v
    with v possibly a product of variables, or it is of the form
            v o i(y)
    or
            v o k(y)
    depending on whether or not pivot equals target. Return the resulting term
    thus constructed.
    """
    args = []
    if includetargetdefaults:
        if target in defaults.keys():
            for d in defaults[target]:
                if not d in args:
                    args.append(d)
    for n in numvars:
        if not n in args:
            args.append(n)
    for c in classvars:
        if not c in args:
            args.append(c)
    for o in otypes:
        if not o in args:
            args.append(o)
    if args != []:
        v = makeproduct(args)
    else:
        return None
    if kappa != None:
        v = makecomposition([v, kappa])
    return v

def assembletermforclass2and3(objectlist, keywordlist, pivot, target, paths, numvars, iota, split):
    """Build a class 2 term, which is of the form
            a(v, w).
    In the simplest case, v = een(target) and w = alle(target), when no
    selections and dimensions apply and when pivot = target. When selections
    apply, the above case turns into
            a(een(target) o z, alle(target) o z)
    where z is a iota term. When also dimensions apply, v and w generally
    become
            v = een(target) o z
    and
            w = <n(a1,..,an,1)o<u1,..,un>oz,..,n(a1,..,an,n)o<u1,..,un>oz>
    which, after some rewriting is just
            w = <u1,..,un> o z.
    In the case a kappa term applies (i.e., when pivot does not equal target)
    we have in general
            z = k(<u1,..,un> o i(---))
    where '---' indicate proper arguments for a iota term, and we have
            v = een(target) o n(a1,..,an,1) o z
    and
            w = <n(a1,..,an,2) o z, ..., n(a1,..,an,n) o z>
    which in general cannot be simplified. Return the term thus composed.
    
    Class 2 terms are meant to express requests like:
            'Aantal banen'
            'Aantal banen in Leiden'
            'Aantal banen per functie in Leiden'
            'Aantal werknemers per bedrijf per functie in Leiden'
    Only in the last example the general case applies.
    
    A class 3 term is built in just the same way, only then v is of the form
          v = <v1, ..., vk> o z
    where the vi are numerical variables, or v is of the more general form in
    the case a kappa term applies.
    
    Class 3 terms are meant to express requests like:
          'totale omzet in de bouwnijverheid'
          'in Den Haag op de Meppelerweg wat is het totale inkomen?'
          'in Leiden bij bedrijven wat is het totale salaris naar functie?'
          'van personen naar gemeente en geslacht het totale inkomen'
          'de totale omzet van alle bedrijven naar activiteit en gemeente van
           vestiging'
          'het totale inkomen van werknemers in de zorg in Leiden'
    Only in the last example the general case applies.
    """
    # default case: assume pivot equals target and no selections or dimensions apply
    kappa = getkappa(objectlist, keywordlist, pivot, target, iota, paths, split)
    if numvars != []:
        v = makeproduct(numvars)
    else:
        v = een(target)
    w = alle(target)
    z = None
    if iota != None and pivot == target:
        w = makecomposition([w, iota]) 
        v = makecomposition([v, iota])
    # the cases below are the ones in which kappa is critical
    i = 0
    if pivot != target:
        z = makeprojectioneasy(kappa, 1)
        w = makecomposition([w, z])
        i = 1
        if split != None:
            i += 1
    if paths != [] and paths != [[]]:
        if i == 0 and len(paths) == 1:
            w = kappa
        else:
            j = 0
            zs = []
            while j < len(paths):
                try:
                    zs.append(makeprojectioneasy(kappa, i + 1))
                except InvalidApplication: # something's wrong, perhaps due to a bad targetindex
                    return None
                i += 1
                j += 1
            w = makeproduct(zs)
    if z != None:
        if v.type.args[0].equals(z.type.args[1]):
            v = makecomposition([v, z])
        else: # something's wrong, perhaps due to an error in estimation of target
            return None
    return makealpha([v, w])

def assembletermforclass4(objectlist, keywordlist, pivot, target, paths, numvars, iota):
    """Build a class 4 term which is of the general form
            a(x(p), w) / a(een(p), w)
    by building seperate terms for nominator and demoninator, using routine
    'assembleforclass2and3()'. See there for the more general forms the
    term returned can assume.
    
    Note that denominator and nominator both reference to the same target 'p'.
    This might not be what is expected from, e.g., a query of the form
    'gemiddeld inkomen op een adres naar geslacht en gemeente'
    where the nominator sums over 'inkomen(persoon)' and the denominator
    sums over 'een(persoon)', thereby ignoring the reference to 'adres'. In
    future implementations, one might allow denominator and nominator to
    reference to different targets. See also the implementation of
    'assembletermforclass5', where a split is extracted from the query. One
    must observe that, e.g., a query like 'gemiddelde leeftijd op een adres
    naar geslacht en gemeente' becomes dubious.
    """
    if numvars == []:
        return None
    x = numvars[0]
    
    z1 = assembletermforclass2and3(objectlist, keywordlist, pivot, target, paths, [x], iota, None)
    z2 = assembletermforclass2and3(objectlist, keywordlist, pivot, target, paths, [], iota, None)

    if z1 != None and z2 != None:
        return makecomposition([gedeelddoor, makeproduct([z1, z2])])
    else: # something's wrong, perhaps due to a wrong target estimation
        return None

def assembletermforclass5(objectlist, keywordlist, pivot, target, paths, kappa, nosplits):
    """Build a class 5 term, which expresses an average, i.e., a numerator and
    a denominator, which are both aggregate terms for counting objects. The
    numerator counts the objects associated with the target. The code below
    first tries to find the type of objects the denominator counts (the split).
    If no split is found, None is returned. Then dimensions associated with
    the numerator and the denominator are discovered: they need not be the
    same, as even their number may differ, but they must be aligned later.
    In short, the dimensions for the numerator are paths that have the pivot
    as origin and the dimensions for the denominator have the split as origin.
    To ensure both numerator and denominator can be put together in a product
    construction, a correction term for the denominator must be found in the
    general case in order to connect the dimensions for the numerator with
    those for the denominator ('alignment'). The term returned is of the form
            a(x, w) / a(y, u) o c
    where c is the correction term and the a's represent alpha (aggregation)
    terms, and where x counts target objects individually - i.e.,
    x=een(target) - and y counts split objects individually - i.e.,
    y=een(split). The construction of both denominator and numerator is
    diverted to the routine 'assembletermforclass2and3()' Selection criteria as
    well as kappa correction or iota selection may apply to both x and w,
    i.e., x might also be a composition of een(target) with a iota or kappa
    term, and w might also be a composition of dimensions with a iota or kappa
    term. Kappa does not apply to y and u, but iota might. This routine also
    serves terms that have the simple form above, without any iota or kappa
    terms.
    """
    split = None
    if paths != []:
        split = getsplit(objectlist, keywordlist, target, paths, nosplits)
    if kappa != None and split == None:
        split = getsplitfromkappa(objectlist, keywordlist, target, kappa, nosplits)
    if split == None:
        split = getsplitfromobjectlist(objectlist, keywordlist, target, nosplits)
    if split == None:
        return None
    (numdimpaths, pathsdict) = getdimensionpaths(objectlist, keywordlist, split, split, split, {})
    (denomdimpaths, ignore) = getdimensionpaths(objectlist, keywordlist, pivot, target, split, pathsdict)
    iotanumpaths = getiotapaths(objectlist, keywordlist, split, split, {})
    iotadenompaths = getiotapaths(objectlist, keywordlist, pivot, target, iotanumpaths)
    iotadenom = makeiota(iotadenompaths, objectlist, pivot)
    iotanum = makeiota(iotanumpaths, objectlist, split)
    z1 = assembletermforclass2and3(objectlist, keywordlist, pivot, target, denomdimpaths, [], iotadenom, split)
    z2 = assembletermforclass2and3(objectlist, keywordlist, split, split, numdimpaths, [], iotanum, None)
    if z1 != None and z2 != None:
        z2 = align(z2, z1)
    else: # something's wrong, perhaps due to a bad targetindex
        return None
    if z2 != None:
        return makecomposition([gedeelddoor, makeproduct([z1, z2])])
    return None