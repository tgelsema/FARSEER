# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 11:48:24 2018

@author: tgelsema
"""

from farseer.graphdb.dm import data
from farseer.nlp.tknz import tokenize
from farseer.interpret.intrprt import interpret
from farseer.learn.lrn import getsavedmodelandtokenizer_classes, getsavedmodelandtokenizer_targetindex, getclassfrommodelandtokenizer, gettargetindexfrommodelandtokenizer
from farseer.interpret.intrprt_pivot import gettarget, getpivot
from farseer.compile.cmpl import cmpl
from farseer.exec.exc import execute, present, columntitles
from farseer.inform.infrm import inform
import time
import tensorflow as tf
import os
from log import logger
# from prsnt import present

LOCAL = True # For debugging in environment without access to SQL database with answers to questions

def readnask(filename="./testcases_delicten.txt"):
    (classmodel, classtokenizer, targetmodel, targettokenizer) = prepare()
    fr = open(filename, 'r')
    fw = open("./execution_times.txt", 'w')
    for line in fr:
        report(line, classmodel, classtokenizer, targetmodel, targettokenizer, fw)
        print()
        input("Press <ENTER>")
        print()
    fr.close()
    fw.close()

def prepare():
    (classmodel, classtokenizer) = getsavedmodelandtokenizer_classes()
    (targetmodel, targettokenizer) = getsavedmodelandtokenizer_targetindex()
    return (classmodel, classtokenizer, targetmodel, targettokenizer)
        
def ask(s="De gemeente met het grootste aantal verdachten van brandstichting"):
    (classmodel, classtokenizer, targetmodel, targettokenizer) = prepare()
    fw = open("./execution_times.txt", 'w')
    term = report(s, classmodel, classtokenizer, targetmodel, targettokenizer, fw)
    fw.close()
    return term

def report(s, classmodel, classtokenizer, targetmodel, targettokenizer, fw):
    start_time = time.time()
    (tokenlist, synonymlist, objectlist, keywordlist) = tokenize(s)
    message =  '\n' + \
               'line:             %s\n' % s + \
               'tokens:           %s\n' % tokenlist + \
               'synonyms:         %s\n' % synonymlist + \
               'objects:          %s\n' % objectlist + \
               'keywords:         %s\n' % keywordlist
    t = round(time.time() - start_time, 4)
    message += '                                        --- %s seconds ---' % t
    fw.write(str(t) + ";")
    start_time = time.time()
    pivot = getpivot(objectlist, keywordlist)
    message += 'pivot:            %s\n' % pivot
    k = gettargetindexfrommodelandtokenizer(targetmodel, targettokenizer, keywordlist)
    cls = getclassfrommodelandtokenizer(classmodel, classtokenizer, keywordlist)
    target = gettarget(tokenlist, objectlist, keywordlist, targetmodel, targettokenizer, pivot)
    message += 'class:            %s\n' % cls + \
               'targetindex:      %s\n' % k + \
               'target:           %s\n' % target
    if target:
        message += 'target id: %s' % target.id
    t = round(time.time() - start_time, 4)
    message += '                                        --- %s seconds ---\n' % t
    fw.write(str(t) + ";")
    start_time = time.time()
    term = interpret(tokenlist, objectlist, keywordlist, target, cls)
    if isinstance(term, list):
        message += 'order variable:   %s \n' % term[1].more() + \
                   'order:            %s \n' % term[2]
        var = term[1]
        order = term[2]
        term = term[0]
    else:
        var = None
        order = ""
    if term != None:
        message += 'term:             %s\n' % term.more()
        t = round(time.time() - start_time, 4)
        message += '                                        --- %s seconds ---\n' % t
        fw.write(str(t) + ";")
        start_time = time.time()
        c = cmpl(data, term, var, order)
        message += 'sql query:        \n' + \
                   f'{c.gen_sql(dialect="T-SQL")}\n'
        print('sql query:        \n' + \
                   f'{c.gen_sql(dialect="T-SQL")}\n')
        t = round(time.time() - start_time, 4)
        message += '                                        --- %s seconds ---\n' % t
        fw.write(str(t) + ";")
        start_time = time.time()
        cols = []
        columntitles(term.type, cols)
        for col in cols:
            message += f'{col}\t'
        if not LOCAL:
            e = execute(c.gen_sql(dialect="T-SQL"))
            present(e)
            message += str(e) + '\n'
            if len(e) == 20:
                message += "(maximaal 20 rijen)"
            t = round(time.time() - start_time, 4)
            message += '                                        --- %s seconds ---\n' % t
            fw.write(str(t) + "\n")
            start_time = time.time()
        else:
            e = None
        print(message)    
        i = inform(term, cls, None, order)
        message += str(i) + '\n'
        t = round(time.time() - start_time, 4)
        message += '                                        --- %s seconds ---\n' % t
        fw.write(str(t) + "\n")
        print(message)
        
    else:
        message += 'term:             None'
        i = None
        e = None
    # print('\n')
    # if term != None:
    #     c = cmpl(term, order)
    #     print(c)
    #     e = execute(c)
    #     present(e)
    if LOCAL:
        e = [('1', 'Amsterdam'), ('2', "Rotterdam")]
        cols = ['getal', '1']
    logger.info(message)
    i = [['onderwerp'], ['dimensie'], ['conditie']]
    return i, e, cols
        
if __name__ == '__main__':
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    os.environ["CUDA_VISIBLE_DEVICES"] = '-1'
    #ask('hoeveel banen zijn er in Rotterdam?')
    # ask('inkomen van griffiers')
    # ask('gemiddeld inkomen van oogartsen')
    # ask('hoeveel vrouwelijke oogartsen werken er in het openbaar bestuur?') # answer: 0
    # ask('hoeveel oogartsen werken er in het openbaar bestuur?') # answer: 0
    # ask('hoeveel vrouwen zijn oogarts?') # answer: 3
    # ask('hoeveel personen zijn kolonel?') # answer: 5
    # ask('hoeveel mannen werken er in het openbaar bestuur?') # answer: 7
    # ask('hoeveel personen werken er in de industrie?') # answer: 11
    # ask('hoeveel banen zijn er in de industrie?') # answer: 13
    # ask('hoeveel personen werken er?') # answer: 33
    # ask('mannen met banen') # Baan is a street name
    # ask('vrouwen die werken') # number of men and women counts to 33
    # ask('hoeveel oogartsen werken er?') # getfirstobj fails: solved; answer: 7
    # ask('hoeveel oogartsen zijn er?') # perfect
    # ask('hoeveel griffiers zijn er in de industrie?') # answer: 3
    # ask('hoeveel mensen werken in Rotterdam?') # answer: 9
    # ask('hoeveel mensen wonen in Leiden en werken in Rotterdam?') # answer: 2
    # ask('hoeveel mannelijke oogartsen wonen er in Delft en werken er in Den Haag?') # answer : 1
    # ask('inkomen van oogartsen die in Delft wonen en in Den Haag werken') # not entirely correct - i think its ok, on second thoughts
    # ask('gemiddeld inkomen per adres van oogartsen in Leiden') # note: inner join on tmp_person will yield different result when placed at the end
    #### yields Klispaanweg 101 4000.0000 and Rapenburg 1 44000.0000
    # ask('aantal mannen en vrouwen in Den Haag') # disregard 'vrouwen'; answer: 9
    # ask('gemeente met het hoogste inkomen')
    # ask('gemeente met het hoogste gemiddelde inkomen') # fantastic
    # ask('wie verdient het meeste?')
    # ask('welke oogarts verdient het meeste?') # gets an error - solved
    # ask('op welk adres wordt het meeste verdiend?') # great
    # ask('hoeveel verdienen oogartsen?') # does the job
    # ask('hoeveel verdienen oogartsen in totaal') # why are the number of persons counted?
    # ask('hoeveel verdienen oogartsen gemiddeld?') # why does this include the total?
    # ask('wie heeft het hoogste inkomen?')
    # ask('wat is het grootste adres?') # peculiar
    # ask('wat is de grootste gemeente?')
    # ask('wat is de kleinste gemeente?') # note: does not include Lisse with 0 inhabitants
    # ask('totaal aantal inwoners per gemeente') # again: does not include Lisse
    # ask('wie is het oudst?')
    # ask('gemeente met de oudste inwoner') # not entirely correct, possibly add new aggregation mode: MAX
    # ask('inkomen van personen') # perhaps switch 'inkomen' and 'naam': done
    # ask('wie woont er op Aart van der Leeuwlaan nummer 1016 in Delft?') # a bit funny, because '1016' is not recognized as 'huisnummer' yet
    # ask('gemiddelde leeftijd op een adres per gemeente') # notice difference with next query
    # ask('gemiddeld inkomen op een adres per gemeente') # does include Lisse
    # ask('gemiddeld aantal personen op een adres per gemeente') # does include Lisse
    #### ask(' gemiddeld aantal personen op een adres in Den Haag') # contains an error when compiling
    #### ask('gemiddeld aantal vrouwen op een adres in Den Haag') # contains an error when compiling
    # ask('gemiddeld aantal mannen op een adres per gemeente') # is this correct? Yes, it is now
    # ask('gemiddeld aantal oogartsen op een adres per gemeente')
    # ask('hoeveel mensen wonen er op de Meppelerweg in Den Haag?') # answer: 8
    # ask('hoeveel vrouwen wonen er op de Aart van der Leeuwlaan in Delft?') # answer: 3
    # ask('wat is het totale inkomen per adres van alle adressen op de Meppelerweg in Den Haag?') # something odd but consistent with intrprt; fixed but inconsistent now
    # ask('wat is het inkomen per adres naar geslacht op de Meppelerweg in Den Haag?') # same: some combinations that yield 0 are missing. inconsistent with intrprt
    # ask('hoeveel adressen heeft Den Haag?') # answer: 9
    # ask('waar woont Tjalling?') # 
    # ask('alle adressen')
    # ask('hoeveel gemeenten zijn er?') # answer: 6
    # ask('wat is het gemiddelde inkomen in Den Haag?')
    # ask('wat is het totaal inkomen op de Meppelerweg in Den Haag?')
    # ask('totaal inkomen en gemiddelde leeftijd naar geslacht in Den Haag')
    # ask('gemiddeld inkomen en gemiddelde leeftijd naar geslacht in Leiden')
    # ask('gemiddelde leeftijd in alle gemeenten') # note: Lisse not present
    # ask('inkomen naar geslacht') # yields sum of incomes
    # ask('gemiddeld inkomen naar geslacht')
    # ask('leeftijd naar geslacht') # yields average age
    # ask('inkomen en leeftijd naar geslacht op de Meppelerweg in Den Haag')
    # ask('hoeveel mensen heten Tjalling op de Meppelerweg in Den Haag?') # answer: 0
    # ask('aantal personen op Meppelerweg 24 in Den Haag') # note: 24 is not recognized as a house number; answer: 8
    # ask('aantal personen naar geslacht en leeftijd') # note that 'leeftijd' does not count as a dimension
    # ask('aantal personen naar geslacht en leeftijd op de Meppelerweg in Den Haag') # note that 'leeftijd' does not count as a dimension
    # ask('adressen in Den Haag')
    # ask('gemiddeld inkomen naar gemeente en geslacht') # note: Lisse is missing
    # ask('personen en hun adressen')
    # ask('mannen en hun adressen') # bit curiuous when compared to last query: fixed
    # ask('griffiers en hun adressen')
    # ask('welke vrouwen zijn griffier?')
    # ask("Wat is het gemiddeld aantal verdachten per maand")
    #ask('In welke gemeente zijn de meeste inbraken in totaal?')
    #ask("Op welke dag zijn er de meeste gevallen van inbraak in Den Haag gepleegd?")
    ask("gemiddeld aantal delicten op een adres in een gemeemte")
    #ask("aantal gevallen brandstichting")
    #readnask("testcases_delicten.txt")