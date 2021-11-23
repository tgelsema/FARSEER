#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 12:35:16 2019

@author: tgelsema
"""

import pickle

with open('./farseer/domainmodel/dm.pickle', mode='rb') as fr:
    dm = pickle.load(fr)
lookup = dm[0]
domainmodel = dm[1]
prefvar = dm[2]
defaults = dm[3]
overridetarget = dm[4]
prefaggrmode = dm[5]
vocab = dm[6]
interrogativepronouns = dm[7]
whichway = dm[8]
optimalpathhelper = dm[9]
orientation = dm[10]
orderedobjecttype = dm[11]
data = dm[12]
getal = dm[13]
gedeelddoor = dm[14]
one = dm[15]
ones = dm[16]
alls = dm[17]