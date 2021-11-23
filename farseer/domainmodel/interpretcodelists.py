# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 15:04:55 2018

@author: tgelsema
"""

import xml.etree.ElementTree as et
from farseer.kind.knd import Constant, ObjectType
import re
import csv

def makescmcodemeta():
    writelabels('./farseer/domainmodel/SCMcode.xml', './farseer/domainmodel/scmcodelookup.txt')

def writelabels(xmlfile, outfile):
    e = et.parse(xmlfile).getroot()
    fw = open(outfile, 'w')
    for elt in e.findall('Code'):
        fw.write("    [''] : '")
        fw.write(elt.find('Label').text)
        fw.write("',")
        fw.write('\n')

def addconsts(xmlfile, cod, lst, labeleqcode):
    e = et.parse(xmlfile).getroot()
    for elt in e.findall('Code'):
        if labeleqcode:
            c = Constant(name=elt.find('Label').text, codomain=cod, code=elt.find('Label').text)
        else:
            c = Constant(name=elt.find('Label').text, codomain=cod, code=elt.find('Waarde').text)
        lst.append(c)
        
def makescmcodedata(codlst):
    xmlfile = './farseer/domainmodel/SCMcode.xml'
    datafile = './farseer/domainmodel/scmcode.txt'
    lst = []
    lst = addconstswithlevels(xmlfile, codlst, lst, datafile)
    return lst
    
def addconstswithlevels(xmlfile, codlst, lst, datafile):
    levellst = []
    keeplevel = -1
    e = et.parse(xmlfile).getroot()
    fw = open(datafile, 'w')
    for c in e.findall("Code"):
        l = c.find('Label').text
        w = c.find('Waarde').text
        level = getlevel(w)
        if keeplevel >= level:
            writelevel(levellst, fw)
            levellst = flushlevellst(levellst, level)
        levellst.append(w)
        keeplevel = level
        const = Constant(name=l, codomain=codlst[level], code=w)
        if not const in lst:
            lst.append(const)
    return lst
    
def flushlevellst(levellst, level):
    i = 0
    removes = []
    while i < len(levellst):
        if getlevel(levellst[i]) >= level:
            removes.append(levellst[i])
        i += 1
    for r in removes:
        levellst.remove(r)
    return levellst

def getlevel(w):
    if re.match('\d0{6}', str(w)) != None:
        return 0
    if re.match('\d\d\d0{4}', str(w)) != None:
        return 1
    if re.match('\d\d\d\d\d0{2}', str(w)) != None:
        return 2
    return 3
    
def writelevel(lst, fw):
    fulllst = lst
    lastlevel = fulllst[len(fulllst) - 1]
    while len(fulllst) < 4:
        fulllst.append(lastlevel)
    fw.write('\t'.join(fulllst))
    fw.write('\n')
    
def gemeenteconsts(cod):
    lst = []
    with open('./farseer/domainmodel/gemeenten-alfabetisch-2016.csv', 'r') as fr: # , encoding='utf-8'
        csvr = csv.reader(fr, delimiter=',')
        i = 0
        for row in csvr:
            if i != 0:
                # const = Constant(name=row[1], codomain=cod, code=row[1])
                # gemcode = 'GM' + '0' * (4 - len(row[0])) + row[0]
                const = Constant(name=row[1], codomain=cod, code=row[1])
                if not const in lst:
                   lst.append(const)
            i += 1
    const = Constant(name='Onbekend', codomain=cod, code='GM0999')
    lst.append(const)
    return lst

def test():
    lst = makescmcodedata()
    for c in lst:
        print(c.more())