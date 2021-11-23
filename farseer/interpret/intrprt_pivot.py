#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 10:55:32 2019

@author: tgelsema

The main routines the farseer.interpret.intrprt_pivot package exposes are the
getpivot() and the gettarget() routines for establishing the pivot and target
of a request. Also, the getpseudodimension() and getnexttarget() routines are
used (by farseer.interpret.intrprt). The getnexttarget() routine is used in
interpreting requests in the case of classes 7, 8, 9, 10 or 11: in these cases
the key object in the request is obtained from getnexttarget(). As an example,
consider 'Op welk adres is het inkomen in totaal het grootst?'. The target here
is (derived from) 'inkomen' - which is the central variable in aggregation.
In this case, getnexttarget() will return 'adres', which is (in
intrprt.assembletermforclass8() in this case) subsequently treated as a
'pseudo dimension', i.e., the request is treated as a class 2/3 request much
like 'Per adres het totale inkomen'. The getpseudodimension() routine is used
only in the case of intrprt.assembletermforclass6() and may very well be
substituted for getnexttarget() in the future.
"""
from farseer.interpret.intrprt_base import getindexfrompattern
from farseer.graphdb.dm import prefvar, orderedobjecttype, overridetarget, interrogativepronouns, orientation
from farseer.kind.knd import ObjectType, Constant, Variable, ObjectTypeRelation
from farseer.learn.lrn import gettargetindexfrommodelandtokenizer
from farseer.graphdb.graphdb import graph

def getnexttarget(objectlist, keywordlist):
    """Using an ordered sequence of patterns that may or may not match
    infixes of keywordlist, derive an object (not necessarily in objectlist)
    that is in some way 'central' in class 6-11 requests. For example, in a
    class 7 request like 'In welke gemeente wonen de meeste personen?',
    'persoon' is both pivot and target, and the object returned by
    getnexttarget() is 'gemeente'. In handling class 6-11 requests, the object
    returned by getnexttarget() is (at least in this case) then treated as if
    it were a dimension, like 'aantal personen per gemeente'. Together with an
    ordering condition, this provides semantics for class 6-11 requests.
    Note that class 6 requests are served not by getnexttarget() but by a
    similar routine, viz. getpseudodimension(). In the future, the latter will
    be substituted for getnexttarget() and getpseudodimension() will become
    obsolete.
    """
    possibletargetlist = []
    possibletargetlist.append(getindexfrompattern(['<whowhat>', '<ot>'], 1, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<ot>', '<with>'], 0, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<const>', '<with>'], 0, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<ot>', '<whowhat>'], 0, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<whowhat>', '<ot>'], 1, 0, keywordlist, True))
    possibletargetlist.append(getindexfrompattern(['<whowhat>', '<const>', '<ot>'], 2, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<whowhat>', '<const>', '<const>'], 2, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<whowhat>', '<const>'], 1, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<const>', '<ot>'], 1, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<const>', '<const>'], 1, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<ot>'], 0, 0, keywordlist, False))
    possibletargetlist.append(getindexfrompattern(['<const>'], 0, 0, keywordlist, False))
    for p in possibletargetlist:
        if p != -1:
            obj = objectlist[p]
            if isinstance(obj, Constant):
                if obj.codomain in overridetarget.keys():
                    obj = overridetarget[obj.codomain]
            if not isinstance(obj, Constant):
                return obj
    return None

def getpivot(objectlist, keywordlist):
    """Given a list of objects from the domain model, return the object (not
    neccessarily in the list) from the domain model that is the 'origin' of all
    objects in the list, in the sense that there exist paths in the domain
    model originating from the pivot to all elements in the list. Correct for
    occurrences of keywords '<greatest>' or '<smallest>', as e.g., the query
    'wat is de grootste gemeente?' expects (according to the domain model) the
    object type 'persoon' to be the subject of counting. Therefore 'persoon' is
    the pivot in that case.
    """
    pivot = None
    for o in objectlist:
        candidate = None
        if o != None:
            if o.__class__.__name__ == 'ObjectType':
                candidate = o
            elif o.__class__.__name__ == 'ObjectTypeRelation' or o.__class__.__name__ == 'Variable':
                candidate = o.domain
            elif o.__class__.__name__ == 'Constant':
                if o.codomain in prefvar.keys():
                    candidate = prefvar[o.codomain].domain
            elif isinstance(o, list):
                if len(o) > 0:
                    if o[0].__class__.__name__ == 'Variable':
                        candidate = o[0].domain
            else:
                candidate = None
            possiblepivot = graph.get_origin(pivot, candidate)
            if possiblepivot != None:
                pivot = possiblepivot
    orderedobjecttypelist = []
    orderedobjecttypelist.append(getindexfrompattern(['<greatest>', '<ot>'], 1, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<smallest>', '<ot>'], 1, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<greatest>', '<const>', '<ot>'], 2, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<smallest>', '<const>', '<ot>'], 2, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<ot>', '<greatest>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<ot>', '<smallest>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<geatest>', '<const>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<smallest>', '<const>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<const>', '<greatest>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<const>', '<smallest>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<ot>', '<const>', '<greatest>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<ot>', '<const>', '<smallest>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<ot>', '<prep>', '<const>', '<greatest>'], 0, 0, keywordlist, True))
    orderedobjecttypelist.append(getindexfrompattern(['<ot>', '<prep>', '<const>', '<smallest>'], 0, 0, keywordlist, True))
    for p in orderedobjecttypelist:
        if p != -1:
            if isinstance(objectlist[p], ObjectType):
                if pivot == objectlist[p]:
                    if pivot in orderedobjecttype.keys():
                        return orderedobjecttype[pivot].domain
            if isinstance(objectlist[p], Constant):
                if objectlist[p].codomain in prefvar.keys():
                    obj = prefvar[objectlist[p].codomain]
                    if pivot == obj:
                        if obj in orderedobjecttype.keys():
                            return orderedobjecttype[obj].domain
    return pivot

def hasorderedotorconst(keywordlist):
    """Return true iff a keywordlist from a request matches some (unordered) 
    pattern in a list of patterns. For instance, hasorderedotorconst() (which
    should be read as: HasOrderedObjectTypeOrConstant and which includes object
    type relations as well) applied to the request 'wat is de grootste
    gemeente' returns true, since ['<whowhat>', '<unk>', '<unk>', '<greatest>',
    '<ot>'] is the keywordlist associated with it. hasorderedotorconst()
    indicates that there is an object type (constant or object type relation)
    that is ordered by the keyword <greatest> or <smallest>.
    """
    orderedlist = []
    orderedlist.append(getindexfrompattern(['<greatest>', '<ot>'], 1, 0, keywordlist, False))
    orderedlist.append(getindexfrompattern(['<smallest>', '<ot>'], 1, 0, keywordlist, False))
    orderedlist.append(getindexfrompattern(['<greatest>', '<const>'], 1, 0, keywordlist, False))
    orderedlist.append(getindexfrompattern(['<smallest>', '<const>'], 1, 0, keywordlist, False))
    orderedlist.append(getindexfrompattern(['<greatest>', '<otr>'], 1, 0, keywordlist, False))
    orderedlist.append(getindexfrompattern(['<smallest>', '<otr>'], 1, 0, keywordlist, False))
    orderedlist.append(getindexfrompattern(['<ot>', '<greatest>'], 0, 0, keywordlist, True))
    orderedlist.append(getindexfrompattern(['<ot>', '<smallest>'], 0, 0, keywordlist, True))
    orderedlist.append(getindexfrompattern(['<const>', '<greatest>'], 0, 0, keywordlist, True))
    orderedlist.append(getindexfrompattern(['<const>', '<smallest>'], 0, 0, keywordlist, True))
    orderedlist.append(getindexfrompattern(['<otr>', '<greatest>'], 0, 0, keywordlist, True))
    orderedlist.append(getindexfrompattern(['<otr>', '<smallest>'], 0, 0, keywordlist, True))
    ordered = False
    for o in orderedlist:
        if o >= 0:
            ordered = True
    return ordered

def gettarget(tokenlist, objectlist, keywordlist, model, tokenizer, pivot):
    """Return the so called target of a request, which may or may not be equal
    to the pivot. For instance, in a request like 'Hoeveel verdienen
    griffiers?', the pivot is 'baan', since job title is a variable with domain
    'baan'. The target in this case however, is 'persoon' since the numbers
    returned are numbers (on income) that reflect attributes of 'personen'. The
    relation between a request and its target (or rather, the index in
    objectlist from which a target can be derived) is stored in the routine
    gettargetindexfrommodelandtokenizer() which is subject to machine learning.
    In a total of over 2200 handwriten and hand-labeled requests, the expected
    target index is learned from supervised training (see the farseer.learn
    package). The expected target index for the request 'Hoeveel verdienen
    griffiers' is 1: this points at the token 'verdienen' and at the object
    'inkomen'. The target in this case is then the domain of 'inkomen', which
    is 'persoon'; this is derived and returned by converttotarget().
    """
    ordered = hasorderedotorconst(keywordlist)
    k = gettargetindexfrommodelandtokenizer(model, tokenizer, keywordlist)
    target = converttotarget(objectlist, keywordlist, tokenlist, k, ordered)
    if not isinstance(target, ObjectType):
        target = pivot # last resort
    return target

def getpseudodimension(objectlist, keywordlist):
    """Will soon be deprecated and replaced by getnextarget(). See the use of
    getpseudodimension() in farseer.interpret.intrprt.assembletermforclass6(),
    which is its only use.
    """
    pseudodimensionlist = []
    pseudodimensionlist.append(getindexfrompattern(['<whowhat>', '<ot>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<whowhat>', '<const>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<most>', '<ot>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<greatest>', '<ot>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<ot>', '<most>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<ot>', '<greatest>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<least>', '<ot>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<smallest>', '<ot>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<ot>', '<least>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<ot>', '<smallest>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<most>', '<const>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<greatest>', '<const>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<const>', '<most>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<const>', '<greatest>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<least>', '<const>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<const>', '<least>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<smallest>', '<const>'], 1, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<const>', '<smallest>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<ot>'], 0, 0, keywordlist, True))
    pseudodimensionlist.append(getindexfrompattern(['<const>'], 0, 0, keywordlist, True))
    for p in pseudodimensionlist:
        if p != -1:
            obj = objectlist[p]
            if isinstance(obj, Constant):
                if obj.codomain in overridetarget.keys():
                    obj = overridetarget[obj.codomain]
            if not isinstance(obj, Constant):
                return obj
    return None

def converttotarget(objectlist, keywordlist, tokenlist, k, ordered):
    """Return an object that is considered the 'target' of a request, specified
    by objectlist, keywordlist and tokenlist, based on a target index k for
    these lists. A target returned by converttotarget() should always be an
    object type (or None, if no suitable object type can be found). Per
    default, the target is the k'th object in objectlist (if k is a valid
    index, otherwise target is None). This object however might not be an
    object type but could also be an object type relation, a constant or a
    numerical variable. (k is asserted to point at an object type, an object
    type relation, a constant, or a numerical variable in objectlist by
    farseer.learn.lrn.gettargetindexfrommodelandtokenizer(), or k equals -1 if
    no such object can be found.) If k points at a numerical variable, then the
    target is the domain of that variable. If k points at a constant, then the
    overridetarget dictionary from the domainmodel is consulted: for instance,
    a constant like 'griffier' which has codomain 'beroepen', should be treated
    as a person, and therefore the entry 'beroepen : persoon' is part of
    overridetarget. For object type relations, the interrogativepronouns
    dictionary (also from the domainmodel) is consulted: in a request like
    'waar woont Tjalling?', k points at 'woont' and because 'adres : 'waar'' is
    an entry in interrogativepronouns, 'adres' becomes the target. Without
    tokens like 'wie' or 'waar', in the case of an object type relation, the
    target is found via orientation, also part of the domain model.
    """
    target = None
    if k != -1:
        target = objectlist[k]
        if isinstance(target, ObjectTypeRelation):
            if (k > 0) and keywordlist[k - 1] == '<whowhat>':
                if target.domain in interrogativepronouns.keys():
                    if interrogativepronouns[target.domain] == tokenlist[k - 1]:
                        target = target.domain
                elif target.codomain in interrogativepronouns.keys():
                    if interrogativepronouns[target.codomain] == tokenlist[k - 1]:
                        target = target.codomain
            elif (k + 1 < len(keywordlist)) and keywordlist[k + 1] == '<whowhat>':
                if target.domain in interrogativepronouns.keys():
                    if interrogativepronouns[target.domain] == tokenlist[k + 1]:
                        target = target.domain
                elif target.codomain in interrogativepronouns.keys():
                    if interrogativepronouns[target.codomain] == tokenlist[k + 1]:
                        target = target.codomain
        if isinstance(target, ObjectTypeRelation):
            if target in orientation.keys():
                target = orientation[target]
            else:
                target = target.domain
        if isinstance(target, Constant):
            if target.codomain in overridetarget.keys():
                target = overridetarget[target.codomain]
        if isinstance(target, ObjectType):
            if ordered:
                if target in orderedobjecttype.keys():
                    target = orderedobjecttype[target].domain
        if keywordlist[k] == '<numvar>':
            if isinstance(target, Variable):
                target = target.domain
            else:
                target = target[0].domain
    return target
