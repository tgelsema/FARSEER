#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 12:35:16 2021

@author: tgelsema
"""

from farseer.kind.knd import Application, Operator, Variable, Constant, ObjectTypeRelation, Phenomenon

class Condition():
    def __init__(self, var, rels, const):
        self.var = var
        self.rels = rels
        self.const = const
        
    def __repr__(self):
        attrstring = ""
        for rel in self.rels:
            attrstring += " van een " + rel.domain.name
        return self.var.name + " van een " + self.var.domain.name + attrstring + " = " + self.const.name
        
    def __eq__(self, other):
        if isinstance(other, Condition):
            return self.var.name == other.var.name and self.rels == other.rels and self.const.name == other.const.name
        else:
            return False
            
    def __hash__(self):
        return hash(self.__repr__())
        
class Dimension():
    def __init__(self, var):
        self.var = var
        
    def __repr__(self):
        return "per " + self.var.name
        
    def __eq__(self, other):
        if isinstance(other, Dimension):
            return self.var.name == other.var.name
        else:
            return False
            
    def __hash__(self):
        return hash(self.__repr__())
        
class Subject():
    def __init__(self, var, rels):
        self.var = var
        self.rels = rels
        
    def __repr__(self):
        if self.var.name.startswith("een"):
            return self.var.domain.altname
        else:
            attrstring = ""
            for rel in self.rels:
                attrstring += " van een " + rel.domain.name
            return self.var.name + " van een " + self.var.domain.name + attrstring
        
    def __eq__(self, other):
        if isinstance(other, Subject):
            return self.var.name == other.var.name and self.rels == other.rels
        else:
            return False
            
    def __hash__(self):
        return hash(self.__repr__())
        
class Denominator():
    def __init__(self, var):
        self.var = var
        
    def __repr__(self):
        if self.var.name.startswith("een"):
            return self.var.domain.name
        else:
            return self.var.name + " van een " + self.var.domain.name
            
    def __eq__(self, other):
        if isinstance(other, Denominator):
            return self.var.name == other.var.name
        else:
            return False
            
    def __hash__(self):
        return hash(self.__repr__())

def inform(term, cls, result, order):
    report = ([], [], [])
    conditions = set()
    extractconditions(term, conditions)
    dimensions = set()
    extractdimensions(term, dimensions)
    rels = []
    subjects = []
    extractsubjects(term, subjects, rels)
    if cls == 1:
        report = informforcls1(conditions, subjects)
    elif cls == 2 or cls == 3 or cls == 4:
        report = informforcls2and3and4(cls, conditions, dimensions, subjects)
    elif cls == 5:
        denominators = set()
        extractdenominators(term, denominators)
        report = informforcls5(conditions, dimensions, subjects, denominators)
    elif cls == 6:
        report = informforcls6(conditions, dimensions, subjects, order)
    elif cls == 7:
        report = informforcls7(conditions, dimensions, subjects, order)
    elif cls == 8:
        report = informforcls8and9(cls, conditions, dimensions, subjects, order)
    elif cls == 9:
        report = informforcls8and9(cls, conditions, dimensions, subjects, order)
    elif cls == 10:
        report = informforcls10(conditions, subjects, order)
    elif cls == 11:
        denominators = set()
        extractdenominators(term, denominators)
        report = informforcls11(conditions, dimensions, subjects, denominators, order)
    return report

def informforcls1(conditions, subjects):
    return (makelistreport(subjects), [], makelistreport(list(conditions)))
    
def makelistreport(l):
    rprtlst = []
    i = 0
    while i < len(l):
        rprtlst.append(l[i].__repr__())
        i += 1
    return rprtlst

def informforcls2and3and4(cls, conditions, dimensions, subjects):
    subjreport = ""
    if subjects != []:
        if cls == 2:
            subjreport = "aantal " + subjects[0].__repr__()
        if cls == 3:
            if subjects[0].var.article == "het":
                subjreport += "totaal "
            else:
                subjreport += "totale "
            subjreport += subjects[0].__repr__()
        if cls == 4:
            if subjects[0].var.article == "het":
                subjreport += "gemiddeld "
            else:
                subjreport += "gemiddelde "
            subjreport += subjects[0].__repr__()
    return ([subjreport], makelistreport(list(dimensions)), makelistreport(list(conditions)))
    
def informforcls5(conditions, dimensions, subjects, denominators):
    subjreport = ""
    if subjects != []:
        subjreport += "gemiddeld aantal " + subjects[0].__repr__() + " per " + denominators.pop().__repr__()
    return ([subjreport], makelistreport(list(dimensions)), makelistreport(list(conditions)))
    
def informforcls6(conditions, dimensions, subjects, order):
    subjreport = ""
    d = list(dimensions)
    if subjects != [] and order != None:
        if order == "asc":
            subjreport += "de kleinste 5 "
        else:
            subjreport += "de grootste 5 "
        if d != []:
            subjreport += d[0].var.domain.altname
        else:
            subjreport += subjects[0].var.domain.altname
        subjreport += " volgens "
        if subjects[0].var.name.startswith("een") and d != []:
            subjreport += "aantal " + subjects[0].__repr__() + " van een " + d[0].var.domain.name
        else:
            subjreport += subjects[0].__repr__()
    return ([subjreport], [], makelistreport(list(conditions)))
    
def informforcls7(conditions, dimensions, subjects, order):
    subjreport = ""
    d = list(dimensions)
    if subjects != [] and order != None and d != []:
        subjreport += "de 5 " + d[0].var.domain.altname
        subjreport += " met het "
        if order == "asc":
            subjreport += "kleinste aantal "
        else:
            subjreport += "grootste aantal "
        subjreport += subjects[0].var.domain.altname
    return ([subjreport], [], makelistreport(list(conditions)))
    
def informforcls8and9(cls, conditions, dimensions, subjects, order):
    subjreport = ""
    d = list(dimensions)
    if subjects != [] and order != None and d != []:
        subjreport += "de 5 " + d[0].var.domain.altname
        subjreport += " met "
        if cls == 8:
            subjreport += "in totaal "
        elif cls == 9:
            subjreport += "gemiddeld "
        subjreport += subjects[0].var.article
        if order == "asc":
            subjreport += " laagste "
        else:
            subjreport += " hoogste "
        subjreport += subjects[0].__repr__()
    return ([subjreport], [], makelistreport(list(conditions)))
    
def informforcls10(conditions, subjects, order):
    subjreport = ""
    if subjects != [] and order != None:
        if len(subjects) > 1:
            subjreport += "de 5 " + subjects[1].var.domain.altname
        else:
            subjreport += "de 5 " + subjects[0].var.domain.altname
        subjreport += " met " + subjects[0].var.article
        if order == "asc":
            subjreport += " laagste "
        else:
            subjreport += " hoogste "
        subjreport += subjects[0].__repr__()
    return ([subjreport], [], makelistreport(list(conditions)))
    
def informforcls11(conditions, dimensions, subjects, denominators, order):
    subjreport = ""
    d = list(dimensions)
    if subjects != [] and order != None and d != []:
        subjreport += "de 5 " + d[0].var.domain.altname
        subjreport += " met gemiddeld het "
        if order == "asc":
            subjreport += "laagste aantal "
        else:
            subjreport += "hoogste aantal "
        subjreport += subjects[0].__repr__() + " per " + denominators.pop().__repr__()
    return ([subjreport], [], makelistreport(list(conditions)))
       
def extractconditions(term, conditions):
    if isinstance(term, Application):
        args = term.args
        if term.op.name == 'inclusion':
            i = 0
            while i < len(args):
                variables = set()
                extractfreevariables(args[i], variables)
                var = variables.pop()
                rels = []
                extractrels(args[i], rels)
                constants = set()
                extractconstants(args[i + 1], constants)
                const = constants.pop()
                conditions.add(Condition(var, rels, const))
                i += 2
        else:
            for arg in args:
                extractconditions(arg, conditions)
                
def extractrels(term, rels):
    if isinstance(term, Application):
        args = term.args
        if term.op.name == 'composition' and isinstance(args[0], Operator) and args[0].name == '(/)':
            extractrels(args[1].args[0], rels)
        elif term.op.name != 'inclusion':
            if term.op.name == 'aggregation':
                extractrels(args[0], rels)
            else:   
                for arg in args:
                    extractrels(arg, rels)
    elif isinstance(term, ObjectTypeRelation):
        rels.append(term)
                
def extractdimensions(term, dimensions):
    if isinstance(term, Application):
        args = term.args
        if term.op.name == 'composition' and isinstance(args[0], Operator) and args[0].name == '(/)':
            extractdimensions(args[1].args[0], dimensions)
        elif term.op.name == 'aggregation':
            extractfreedimensions(args[1], dimensions)
        else:
            for arg in args:
                extractdimensions(arg, dimensions)

def extractfreevariables(term, variables):
    if isinstance(term, Application):
        args = term.args
        if term.op.name != 'inclusion':
            for arg in args:
                extractfreevariables(arg, variables)
    elif isinstance(term, Variable):
        if not term.name.startswith("alle"):
            variables.add(term)
            
def extractfreedimensions(term, variables):
    if isinstance(term, Application):
        args = term.args
        if term.op.name != 'inclusion':
            for arg in args:
                extractfreedimensions(arg, variables)
    elif isinstance(term, Variable):
        if not term.name.startswith("alle"):
            variables.add(Dimension(term))

def extractconstants(term, constants):
    if isinstance(term, Application):
        args = term.args
        for arg in args:
            extractconstants(arg, constants)
    elif isinstance(term, Constant):
        constants.add(term)
        
def extractsubjects(term, subjects, rels):
    if isinstance(term, Application):
        args = term.args
        if term.op.name == 'composition' and isinstance(args[0], Operator) and args[0].name == '(/)':
            extractsubjects(args[1].args[0], subjects, rels)
        elif term.op.name != 'inclusion':
            if term.op.name == 'aggregation':
                extractsubjects(args[0], subjects, rels)
            else:
                if term.op.name == 'composition':
                    rels = []
                    extractinnerrels(term, rels)
                for arg in args:
                    extractsubjects(arg, subjects, rels)
    elif isinstance(term, Variable):
        subjects.append(Subject(term, rels))
                
def extractinnerrels(term, rels):
    if isinstance(term, Application):
        args = term.args
        if term.op.name != 'inclusion' and term.op.name != 'product':
            for arg in args:
                extractinnerrels(arg, rels)
    elif isinstance(term, ObjectTypeRelation):
        if term not in rels:
            rels.append(term)

def extractdenominators(term, denominators):
    if isinstance(term, Application):
        args = term.args
        if term.op.name == 'composition' and isinstance(args[0], Operator) and args[0].name == '(/)':
            extractdenominators(args[1].args[1], denominators)
        elif term.op.name != 'inclusion':
            if term.op.name == 'aggregation':
                extractdenominators(args[0], denominators)
            else:
                for arg in args:
                    extractdenominators(arg, denominators)
    elif isinstance(term, Variable) and not term.name.startswith("alle"):
        denominators.add(Denominator(term))
 