# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 11:07:00 2021

@author: tgelsema

The test Python module basically exposes two routines, viz. test() and
do_baseline_test(), that must be used in conjunction. First, do_baseline_test()
computes intermediate output for the interpret stage of Farseer and stores
this in the file './farseer/test/testcases_baseline.pickle', based on the
requests (and expected output) that are stored in the file
'./farseer/test/testdata.txt'. Unexpected results are reported in the file
'./farseer/test/baseline_report.txt' upon completion of do_baseline_test().

Then, when code for various routines of the interpret stage is changed, test()
can be run to see what effect the change has on intermediate output, by
computing the various intermediate results again for each request found in
'./farseer/test/testdata.txt' and reporting every change from the intermediate
results that were previously computed when do_baseline_test() was last run. The
report for test() can be found in the file './farseer/test/test_report.txt'.

If the contents of the file './farseer/test/test_report.txt' are changed, run
do_baseline_test() before running test().

The intermediate output that is stored in
'./farseer/test/testcases_baseline.pickle' are exactly the attributes of the
Testcase class (also exposed by the test Python module), i.e.,
'./farseer/test/testcases_baseline.pickle' is a list of Testcases when
unpickled.

Finally, the test Python module contains a routine
equals_as_objectlist(lst1, lst2) that returns True iff lst1 and lst2 are equal
as lists of objects of the Kind class.
"""

from farseer.domainmodel.dm import lookup
from farseer.nlp.tknz import tokenize
from farseer.interpret.intrprt import interpret
from farseer.learn.lrn import getsavedmodelandtokenizer_classes, getsavedmodelandtokenizer_targetindex, getclassfrommodelandtokenizer, gettargetindexfrommodelandtokenizer
from farseer.interpret.intrprt_pivot import gettarget, getpivot
import pickle
import sys

class Testcase:
    """Basic data structure to capture intermediate results of the interpret
    stage, i.e., the results of tokenize(), getpivot(), gettarget(),
    getclassfrommodelandtokenizer() and interpret() applied to a request (line).
    """
    def __init__(self, line, tokenlist, synonymlist, objectlist, keywordlist, pivot, target, cls, term):
        self.line = line
        self.tokenlist = tokenlist
        self.synonymlist = synonymlist
        self.objectlist = objectlist
        self.keywordlist = keywordlist
        self.pivot = pivot
        self.target = target
        self.cls = cls
        self.term = term
        
def test():
    """Read the file 'testdata.txt' one line at a time and compute the
    intermediate results of the interpret stage for each line that represents a
    request. Then compare these results with those precomputed and stored in
    the file 'testcases_baseline.pickle'. Report each mismatch in the file
    'test_report.txt'.
    
    Use test() in conjunction with do_baseline_test(): the last creates a new
    baseline consisting of intermediate results. Then use test() when there is
    a need for comparing the effects of altered code of the interpret stage
    with the situation as it was when do_baseline_test() was last run.
    
    Intermediate results are results from the routines reported in the Testcase
    class.
    
    test() will create or overwrite the file './farseer/test/test_report.txt'.
    """
    # first, count the number of test cases in the file 'testdata.txt'
    fr = open('./farseer/test/testdata.txt', 'r')
    noofcases = 0
    for line in fr:
        if len(line.split()) > 1:
            noofcases += 1
    fr.close()
    (classmodel, classtokenizer) = getsavedmodelandtokenizer_classes()
    (targetmodel, targettokenizer) = getsavedmodelandtokenizer_targetindex()
    with open('./farseer/test/testcases_baseline.pickle', mode='rb') as fr:
        testcases_baseline = pickle.load(fr)
    fr.close()
    fr = open('./farseer/test/testdata.txt', 'r')
    fw = open('./farseer/test/test_report.txt', 'w')
    n = 0
    newchapter = False
    for line in fr:
        line = line.rstrip()
        if line == '':
            newchapter = True
        else:
            if newchapter:
                newchapter = False
            else:
                if len(line.split()) != 1:
                    (tokenlist, synonymlist, objectlist, keywordlist) = tokenize(line, lookup)
                    pivot = getpivot(objectlist, keywordlist)
                    target = gettarget(tokenlist, objectlist, keywordlist, targetmodel, targettokenizer, pivot)
                    cls = getclassfrommodelandtokenizer(classmodel, classtokenizer, keywordlist)
                    term = interpret(tokenlist, objectlist, keywordlist, target, cls)
                    if isinstance(term, list):
                        term = term[0]
                    if line != testcases_baseline[n].line:
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "' differs from line '" + testcases_baseline[n].line + "' in baseline test cases." + "\n")
                    if tokenlist != testcases_baseline[n].tokenlist:
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "': tokenlist '" + str(tokenlist) + "' differs from tokenlist '" + str(testcases_baseline[n].tokenlist) + "' in baseline test cases." + "\n")
                    if synonymlist != testcases_baseline[n].synonymlist:
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "': synonymlist '" + str(synonymlist) + "' differs from synonymlist '" + str(testcases_baseline[n].synonymlist) + "' in baseline test cases." + "\n")
                    if not equals_as_objectlist(objectlist, testcases_baseline[n].objectlist):
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "': objectlist '" + str(objectlist) + "' differs from objectlist '" + str(testcases_baseline[n].objectlist) + "' in baseline test cases." + "\n")
                    if keywordlist != testcases_baseline[n].keywordlist:
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "': keywordlist '" + str(keywordlist) + "' differs from keywordlist '" + str(testcases_baseline[n].keywordlist) + "' in baseline test cases." + "\n")
                    if not pivot.equals(testcases_baseline[n].pivot):
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "': pivot '" + pivot.__repr__() + "' differs from pivot '" + testcases_baseline[n].pivot.__repr__() + "' in baseline test cases." + "\n")
                    if not target.equals(testcases_baseline[n].target):
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "': target '" + target.__repr__() + "' differs from target '" + testcases_baseline[n].target.__repr__() + "' in baseline test cases." + "\n")
                    if cls != testcases_baseline[n].cls:
                        fw.write("Case no. " + str(n + 1) + ", line '" + line + "': class '" + str(cls) + "' differs from class '" + str(testcases_baseline[n].cls) + "' in baseline test cases." + "\n")
                    if term != None:
                        if not term.equals(testcases_baseline[n].term):
                            fw.write("Case no. " + str(n + 1) + ", line '" + line + "': term '" + term.more() + "' differs from term '" + testcases_baseline[n].term.more() if testcases_baseline[n].term != None else "None" + "' in baseline test cases." + "\n")
                    else:
                        if testcases_baseline[n].term != None:
                            fw.write("Case no. " + str(n + 1) + ", line '" + line + "': term '" + "None" + "' differs from term '" + testcases_baseline[n].term.more() + "' in baseline test cases." + "\n")
                    n += 1
                    print("Computing test case no. " + str(n) + " of " + str(noofcases))
    sys.stdout.flush()
    fr.close()
    fw.close()

def equals_as_objectlist(lst1, lst2):
    """Return True if, as lists of objects of the Kind class, lst1 and lst2
    are equal, otherwise return False.
    """
    if len(lst1) != len(lst2):
        return False
    i = 0
    while i < len(lst1):
        if lst1[i] == None and lst2[i] != None:
            return False
        if lst1[i] != None and lst2[i] == None:
            return False
        if lst1[i] != None and lst2[i] != None:
            if not lst1[i].equals(lst2[i]):
                return False
        i += 1
    return True

def do_baseline_test():
    """Read the file 'testdata.txt' line by line and for each request perform
    the various steps in the interpret stage mentioned in the comments of the
    class Testcase. Make a testcase for each request; store all testcases in
    the file 'testcases_baseline.pickle'. Note that 'testdata.txt' is organized
    into chapters; each request in the same chapter should have the same
    semantics, i.e., interpret() should yield the same term for each. Report
    (in the file 'baseline_report.txt') the requests for which this is not the
    case, i.e., report those requests that yield a different term than the term
    that is the result of interpret() for the first request in each chapter.
    Also, report cases in which the computed target (from gettargetindex...())
    is different from the expected target, as indicated in 'testdata.txt'
    (i.e., each request in 'testdata.txt' is preceded by a pseudo target, from
    which the expected target index can be derived). Finally, report cases in
    which the computed class (the result of getclassfrommodelandtokenizer())
    differs from the expected class indicated at the top of each chapter in
    'testdata.txt'.
    
    do_baseline_test() creates or overwrites
    './farseer/test/testcases_baseline.pickle' and
    './farseer/test/baseline_report.txt'.
    
    Running test() will compare the intermediate outcomes of a rerun of
    'testdata.txt' with the outcomes in 'testcases_baseline.pickle'. This
    reports the effects of changes in the code for the interpret stage, when
    compared to the situation in which do_baseline_test() was last run.
    
    If 'testdata.txt' is changed, rerun do_baseline_test() before running
    test().
    """
    # first, count the number of test cases in the file 'testdata.txt'
    fr = open('./farseer/test/testdata.txt', 'r')
    noofcases = 0
    for line in fr:
        if len(line.split()) > 1:
            noofcases += 1
    fr.close()
    (classmodel, classtokenizer) = getsavedmodelandtokenizer_classes()
    (targetmodel, targettokenizer) = getsavedmodelandtokenizer_targetindex()
    fr = open('./farseer/test/testdata.txt', 'r')
    fw1 = open('./farseer/test/baseline_report.txt', 'w')
    n = 0
    testcases = []
    newchapter = False
    firstcase = False
    for line in fr:
        line = line.rstrip()
        if line == '':
            newchapter = True
        else:
            if newchapter:
                expectedcls = int(line)
                newchapter = False
                firstcase = True
            else:
                if len(line.split()) != 1:
                    n += 1
                    print("Creating baseline case no. " + str(n) + " of " + str(noofcases) + ": '" + line + "'")
                    (tokenlist, synonymlist, objectlist, keywordlist) = tokenize(line, lookup)
                    pivot = getpivot(objectlist, keywordlist)
                    targetindex = gettargetindexfrommodelandtokenizer(targetmodel, targettokenizer, keywordlist)
                    target = gettarget(tokenlist, objectlist, keywordlist, targetmodel, targettokenizer, pivot)
                    cls = getclassfrommodelandtokenizer(classmodel, classtokenizer, keywordlist)
                    term = interpret(tokenlist, objectlist, keywordlist, target, cls)
                    if isinstance(term, list):
                        term = term[0]
                    if targetindex != tokenlist.index(expectedpseudotarget):
                        fw1.write("Case no. " + str(n) + ", line '" + line + "': target '" + target.name + "' does not match expected pseudo target '" + expectedpseudotarget + "'." + "\n")
                    if cls != expectedcls:
                        fw1.write("Case no. " + str(n) + ", line '" + line + "': class '" + str(cls) + "' does not match expected class '" + str(expectedcls) + "'." + "\n")
                    if firstcase:
                        expectedterm = term
                        firstcase = False
                    else:
                        if term != None:
                            if not term.equals(expectedterm):
                                fw1.write("Case no. " + str(n) + ", line '" + line + "': term '" + term.more() + "' does not match expected term '" + expectedterm.more() if expectedterm != None else "None" + "'." + "\n")
                        else:
                            if expectedterm != None:
                                fw1.write("Case no. " + str(n) + ", line '" + line + "': term '" + term.more() if term != None else "None" + "' does not match expected term '" + expectedterm.more() + "'." + "\n")
                    testcase = Testcase(line, tokenlist, synonymlist, objectlist, keywordlist, pivot, target, cls, term)
                    testcases.append(testcase)
                else:
                    expectedpseudotarget = line
    with open('./farseer/test/testcases_baseline.pickle', mode='wb') as fw2:
        pickle.dump(testcases, fw2, protocol=pickle.HIGHEST_PROTOCOL)
    sys.stdout.flush()
    fr.close()
    fw1.close()
    fw2.close()