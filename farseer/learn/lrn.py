# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from farseer.domainmodel.dm import lookup, gedeelddoor, getal
from farseer.nlp.tknz import tokenize
# from intrprt_old import interpret
from farseer.kind.knd import *
from farseer.term.trm import *
from json import dumps, load
# from xml.etree import ElementTree
from keras_preprocessing.text import Tokenizer
from keras_preprocessing import text
from keras_preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, model_from_json
from tensorflow.keras import layers
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.utils import to_categorical
import numpy as np
import sys
import pickle

def testtrainingdata():
    """Test whether in 'trainingdata.txt' every query is preceded by a word
    that is found in the query (its expected pseudotarget). If not,
    'trainingdata.txt' is corrupted and should not be used for training. Print
    the query - pseudotarget pairs that do not match.
    """
    with open('trainingdata.txt', 'r') as fr:
        lines = fr.readlines()
    for line in lines:
        line.rstrip()
        if line != '' and len(line) != 1 and len(line) != 2:
            split = line.split()
            if len(split) == 1:
                target = split[0]
            else:
                (tokenlist, synonymlist, objectlist, keywordlist) = tokenize(line, lookup)
                if target not in tokenlist:
                    print(tokenlist)
                    print(target)

# def extractqueries():
#     fr = open("ask.py", 'r')
#     fw = open('queries.txt', 'w')
#     for line in fr:
#         if 'ask' in line:
#             if line[line.find('ask(') + 5 : line.find(")") - 1] != '':
#                 fw.write(line[line.find('ask(') + 5 : line.find(')') - 1])
#                 fw.write('\n')

def train_targetindex():    
    (numlabels, numfeatures, xtrain, ytrain, xval, yval, tokenizer) = gettrainingtensors_targetindex()
    
    print(ytrain.shape)
    
    # ytrain = to_categorical(ytrain, num_classes=numlabels, dtype='int32')
    ytrain = to_categorical(ytrain, num_classes=numlabels)

    # yval = to_categorical(yval)
    
    model = Sequential()
    model.add(layers.Embedding(numfeatures + 1, 32)) # original parameters: numfeatures + 1, 32 (16 seemed to perform just less)
    # model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Conv1D(32, 7, padding='valid', activation='relu')) # original parameters: 32, 7, padding='valid', activation='relu'
    # model.add(layers.MaxPooling1D(3)) ####
    # model.add(layers.Conv1D(16, 3, activation='relu')) ####
    model.add(layers.GlobalMaxPooling1D())
    model.add(layers.Dense(numlabels, activation='softmax')) # or: activation='sigmoid'
    
    model.summary()
    
    model.compile(optimizer=RMSprop(lr=1e-3),
                  loss='categorical_crossentropy',
                  metrics=['acc'])
    
    history = model.fit(xtrain, ytrain, epochs=80, batch_size=20, validation_split=0.2)
    
    model_json = model.to_json()
    with open('./farseer/learn/model_targetindex.json', 'w') as json_file:
        json_file.write(model_json)
    json_file.close()
    model.save_weights('./farseer/learn/model_targetindex.h5')

def gettrainingtensors_targetindex():
    maxlen = 20 # cuts off sentences after 20 tokens - original: 16
    numtrainingsamples = 2155 # number of traing samples
    numvalidationsamples = 0 # number of validation samples
    numlabels = 20 # number of classes equals maximum length of sentence
    
    print('starting...')
    (texts, labels) = preparetrainingdata_targetindex()
    
    tokenizer = Tokenizer(num_words=None)
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    wordindex = tokenizer.word_index
    print('number of unique tokens: %s' % len(wordindex))
    
    data = pad_sequences(sequences, maxlen=maxlen)
    
    labels = np.asarray(labels)
    print('shape of data tensor: ', data.shape)
    print('shape of label tensor: ', labels.shape)
    
    sys.stdout.flush()
    
    # print(labels[:10])
    # return
    
    indices = np.arange(data.shape[0])
    np.random.shuffle(indices)
    data = data[indices]
    labels = labels[indices]
    
    xtrain = data[:numtrainingsamples]
    ytrain = labels[:numtrainingsamples]
    xval = data[numtrainingsamples: numtrainingsamples + numvalidationsamples]
    yval = labels[numtrainingsamples: numtrainingsamples + numvalidationsamples]
    
    print('\n')
    print('ready.')
    
    sys.stdout.flush()
    
    with open('./farseer/learn/tokenizer_targetindex.pickle', 'wb') as f:
        pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)
    # tokenizerasjson = tokenizer.to_json()
    # with open('./farseer/learn/tokenizer_targetindex.json', 'w', encoding='utf-8') as f:
    #     f.write(dumps(tokenizerasjson, ensure_ascii=False))
    
    return (numlabels, len(wordindex), xtrain, ytrain, xval, yval, tokenizer)

def preparetrainingdata_targetindex():
    fr = open('./farseer/learn/trainingdata.txt', 'r')
    n = 0
    stats = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    labels = []
    texts = []
    maxlen = 0
    for line in fr:
        line = line.rstrip()
        if line != '' and len(line) > 2:
            if len(line.split()) == 1:
                target = line
            else:
                (tokenlist, synonymlist, objectlist, keywords) = tokenize(line, lookup)
                if tokenlist.index(target) >= 0:
                    if maxlen < len(keywords):
                        maxlen = len(keywords)
                    texts.append(' '.join(keywords))
                    label = tokenlist.index(target)
                    labels.append(label)
                    stats[label] = stats[label] + 1
                    n += 1
    print('\n')
    print('total number of queries: %s'% n)
    print('number of queries per class: %s' % stats)
    print('maximum sentence length: %s' % maxlen)
    sys.stdout.flush()
    # print(texts[:20], labels[:20])
    return (texts, labels)

def train_classes():    
    (numlabels, numfeatures, xtrain, ytrain, xval, yval, tokenizer) = gettrainingtensors_classes()
    
    print(ytrain.shape)
    
    # ytrain = to_categorical(ytrain, num_classes=numlabels, dtype='int32')
    ytrain = to_categorical(ytrain, num_classes=numlabels)
    # yval = to_categorical(yval)
    
    model = Sequential()
    model.add(layers.Embedding(numfeatures + 1, 32)) # original parameters: numfeatures + 1, 32 (16 seemed to perform just less)
    # model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Conv1D(32, 7, padding='valid', activation='relu')) # original parameters: 32, 7, padding='valid', activation='relu'
    # model.add(layers.MaxPooling1D(3)) ####
    # model.add(layers.Conv1D(16, 3, activation='relu')) ####
    model.add(layers.GlobalMaxPooling1D())
    model.add(layers.Dense(numlabels, activation='softmax')) # or: activation='sigmoid'
    
    model.summary()
    
    model.compile(optimizer=RMSprop(lr=1e-3),
                  loss='categorical_crossentropy',
                  metrics=['acc'])
    
    history = model.fit(xtrain, ytrain, epochs=80, batch_size=20, validation_split=0.2)
    
    model_json = model.to_json()
    with open('./farseer/learn/model_classes.json', 'w') as json_file:
        json_file.write(model_json)
    json_file.close()
    model.save_weights('./farseer/learn/model_classes.h5')
    

def gettrainingtensors_classes():
    maxlen = 20 # cuts off sentences after 20 tokens - original: 16
    numtrainingsamples = 2155 # number of traing samples
    numvalidationsamples = 0 # number of validation samples
    numlabels = 12 # number of classes - used to be 16
    
    print('starting...')
    (texts, labels) = preparetrainingdata_classes()
    
    tokenizer = Tokenizer(num_words=None)
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    wordindex = tokenizer.word_index
    print('number of unique tokens: %s' % len(wordindex))
    
    data = pad_sequences(sequences, maxlen=maxlen)
    
    labels = np.asarray(labels)
    print('shape of data tensor: ', data.shape)
    print('shape of label tensor: ', labels.shape)
    
    sys.stdout.flush()
    
    indices = np.arange(data.shape[0])
    np.random.shuffle(indices)
    data = data[indices]
    labels = labels[indices]
    
    xtrain = data[:numtrainingsamples]
    ytrain = labels[:numtrainingsamples]
    xval = data[numtrainingsamples: numtrainingsamples + numvalidationsamples]
    yval = labels[numtrainingsamples: numtrainingsamples + numvalidationsamples]
    
    print('\n')
    print('ready.')
    
    sys.stdout.flush()
    
    with open('./farseer/learn/tokenizer_classes.pickle', 'wb') as f:
        pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)
    # tokenizerasjson = tokenizer.to_json()
    # with open('./farseer/learn/tokenizer_classes.json', 'w', encoding='utf-8') as f:
    #     f.write(dumps(tokenizerasjson, ensure_ascii=False))
    
    return (numlabels, len(wordindex), xtrain, ytrain, xval, yval, tokenizer)

def preparetrainingdata_classes():
    fr = open('./farseer/learn/trainingdata.txt', 'r')
    n = 0
    stats = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    labels = []
    texts = []
    newchapter = False
    maxlen = 0
    for line in fr:
        line = line.rstrip()
        if line == '':
            newchapter = True
        else:
            if newchapter:
                label = int(line)
                newchapter = False
            else:
                if len(line.split()) != 1:
                    (tokenlist, synonymlist, objectlist, keywords) = tokenize(line, lookup)
                    if maxlen < len(keywords):
                        maxlen = len(keywords)
                    texts.append(' '.join(keywords))
                    labels.append(label)
                    stats[label] = stats[label] + 1
                    n += 1
    print('\n')
    print('total number of queries: %s'% n)
    print('number of queries per class: %s' % stats)
    print('maximum sentence length: %s' % maxlen)
    sys.stdout.flush()
    # print(texts[:20], labels[:20])
    return (texts, labels)

def getsavedmodelandtokenizer_classes():
    json_file = open('./farseer/learn/model_classes.json', 'r')
    model_json = json_file.read()
    json_file.close()
    model = model_from_json(model_json)
    model.load_weights('./farseer/learn/model_classes.h5')
    with open('./farseer/learn/tokenizer_classes.pickle', 'rb') as f:
        tokenizer = pickle.load(f)
    # with open('./farseer/learn/tokenizer_classes.json') as f:
    #     tokenizerasjson = load(f)
    #     tokenizer = text.tokenizer_from_json(tokenizerasjson)
    return (model, tokenizer)

def getsavedmodelandtokenizer_targetindex():
    json_file = open('./farseer/learn/model_targetindex.json', 'r')
    model_json = json_file.read()
    json_file.close()
    model = model_from_json(model_json)
    model.load_weights('./farseer/learn/model_targetindex.h5')
    with open('./farseer/learn/tokenizer_targetindex.pickle', 'rb') as f:
        tokenizer = pickle.load(f)
    # with open('./farseer/learn/tokenizer_targetindex.json') as f:
    #     tokenizerasjson = load(f)
    #     tokenizer = text.tokenizer_from_json(tokenizerasjson)
    return (model, tokenizer)

def getclassfrommodelandtokenizer(model, tokenizer, keywordlist):
    text = ' '.join(keywordlist)
    texts = [text]
    sequences = tokenizer.texts_to_sequences(texts)
    inputs = pad_sequences(sequences, maxlen=20)
    return model.predict_classes(inputs)[0]

def getclass(keywordlist):
    (model, tokenizer) = getsavedmodelandtokenizer_classes()
    return getclassfrommodelandtokenizer(model, tokenizer, keywordlist)

def gettargetindexfrommodelandtokenizer(model, tokenizer, keywordlist):
    text = ' '.join(keywordlist)
    texts = [text]
    sequences = tokenizer.texts_to_sequences(texts)
    inputs = pad_sequences(sequences, maxlen=20)
    potentialtargetindex = model.predict_classes(inputs)[0]
    if potentialtargetindex >= len(keywordlist):
        potentialtargetindex = len(keywordlist) - 1
    if potentialtargetindex < 0:
        potentialtargetindex = 0
    if keywordlist[potentialtargetindex] in ['<ot>', '<const>', ' <otr>', '<numvar>']:
        return potentialtargetindex
    else:
        return around(potentialtargetindex, keywordlist)
    
def gettargetindex(keywordlist):
    (model, tokenizer) = getsavedmodelandtokenizer_targetindex()
    return gettargetindexfrommodelandtokenizer(model, tokenizer, keywordlist)

def around(targetindex, keywordlist):
    # assume: targetindex < len(keywordlist) and targetindex >= 0
    t = targetindex
    k = 1
    while t + k < len(keywordlist) or t - k >= 0:
        if t + k < len(keywordlist):
            if keywordlist[t + k] in ['<ot>', '<const>', '<otr>', '<numvar>']:
                return t + k
        if t - k >= 0:
            if keywordlist[t - k] in ['<ot>', '<const>', '<otr>', '<numvar>']:
                return t - k
        k += 1
    return -1

def test():
    (model, tokenizer) = getsavedmodelandtokenizer_classes()
    line = 'het gemiddeld aantal banen bij een bedrijf per gemeente'
    # line = 'het gemiddeld aantal banen per gemeente'
    (tokenlist, objectlist, keywords) = tokenize(line, lookup)
    text = ' '.join(keywords)
    texts = [text]
    sequences = tokenizer.texts_to_sequences(texts)
    inputs = pad_sequences(sequences, maxlen=20)
    print("query: '", line, "' receives class: ", model.predict_classes(inputs)[0])

"""Should be called only when queries.txt is altered
def maketrainingdata():
    fr = open('queries.txt', 'r')
    fw = open('trainingdata.txt', 'w')
    n = 0
    stats = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    newchapter = False
    for line in fr:
        line = line.rstrip()
        if line == '':
            newchapter = True
        else:
            (tokenlist, objectlist) = tokenize(line, lookup)
            if newchapter:
                (term, order) = interpret(tokenlist, objectlist)
                label = classify(term)
                fw.write('\n')
                fw.write(str(label))
                fw.write('\n')
            newchapter = False
            fw.write(line)
            fw.write('\n')
            stats[label] = stats[label] + 1
            n += 1
    print('\n')
    print('total number of queries: %s'% n)
    print('number of queries per class: %s' % stats)
    sys.stdout.flush()
    return True
"""
    
"""Should be called only when queries.txt has changed.
def classify(term):
    # global varmap
    # varmap = {}
    if match(term, somesumvw): # simple sum
        v = varmap[someelementv]
        w = varmap[someelementw]
        if match(v, onep):
            if match(w, allp):
                return 3
            return 5
        if v.__class__.__name__ == 'Application' and w.__class__.__name__ == 'Application':
            if v.op.name == 'composition' and w.op.name == 'composition':
                v1 = v.args[0]
                v2 = v.args[1]
                w1 = w.args[0]
                w2 = w.args[1]
                if match(w1, allp):
                    if match(v1, onep):
                        return 4
                    else:
                        return 8
                return 7
        else:
            return 6
    if match(term, someavgvwuz): # simple or complex average
        v = varmap[someelementv]
        w = varmap[someelementw]
        u = varmap[someelementu]
        z = varmap[someelementz]
        if match(u, onep):
            if match(v, onep):
                return 11
            elif w.equals(z):
                return 9
            elif v.__class__.__name__ == 'Application' and w.__class__.__name__ == 'Application':
                if v.op.name == 'composition' and w.op.name == 'composition':
                    v1 = v.args[0]
                    v2 = v.args[1]
                    w1 = w.args[0]
                    w2 = w.args[1]
                    if match(v1, onep):
                        if v2.equals(w2):
                            return 12
            else:
                return 10
        if w.equals(z):
            if v.__class__.__name__ == 'Application' and w.__class__.__name__ == 'Application' and u.__class__.__name__ == 'Application' and z.__class__.__name__ == 'Application':
                if v.op.name == 'composition' and w.op.name == 'composition' and u.op.name == 'composition' and z.op.name == 'composition':
                    v1 = v.args[0]
                    v2 = v.args[1]
                    w1 = w.args[0]
                    w2 = w.args[1]
                    u1 = u.args[0]
                    u2 = u.args[1]
                    z1 = z.args[0]
                    z2 = z.args[1]
                    if v2.equals(w2) and v2.equals(u2) and v2.equals(z2):
                        if match(u1, onep) and match(w1, allp) and match(z1, allp):
                            return 13
        if v.__class__.__name__ == 'Application' and w.__class__.__name__ == 'Application' and u.__class__.__name__ == 'Application' and z.__class__.__name__ == 'Application':
            if v.op.name == 'composition' and w.op.name == 'composition' and u.op.name == 'composition' and z.op.name == 'composition':
                v1 = v.args[0]
                v2 = v.args[1]
                w1 = w.args[0]
                w2 = w.args[1]
                u1 = u.args[0]
                u2 = u.args[1]
                z1 = z.args[0]
                z2 = z.args[1]
                if match(v1, onep) and match(u1, onep) and match(w1, allp) and match(z1, allp) and v2.equals(w2) and u2.equals(z2):
                    return 14
                if match(u1, onep) and v2.equals(w2) and v2.equals(u2) and v2.equals(z2) and w1.equals(z1):
                    return 15
    if term.__class__.__name__ == 'Application' and term.op.name == 'composition':
        if term.args[1].__class__.__name__ == 'Application' and (term.args[1].op.name == 'inclusion' or term.args[1].op.name == 'inverse'):
            return 2
    if (term.__class__.__name__ == 'Application' and term.op.name == 'product') or term.__class__.__name__ == 'Variable':
        return 1
    return 0
"""


def match(cterm, oterm):
    global varmap
    varmap = {}
    return recmatch(cterm, oterm)
    
def recmatch(cterm, oterm):
    global varmap
    if cterm.__class__.__name__ == 'Application':
        return matchapplication(cterm, oterm)
    else:
        return matchkind(cterm, oterm)
        
def matchapplication(cterm, oterm):
    global varmap
    if oterm.__class__.__name__ == 'Gap':
        if oterm in varmap.keys():
            if varmap[oterm].equals(cterm):
                return True
        else:
            varmap[oterm] = cterm
            return True
    if oterm.__class__.__name__ == 'Application':
        if cterm.__class__.__name__ == 'Application' and cterm.op == oterm.op:
            if len(cterm.args) == len(oterm.args):
                for i in range(len(oterm.args)):
                    if not recmatch(cterm.args[i], oterm.args[i]):
                        return False
                return True
    return False
                    
def matchkind(cterm, oterm):
    global varmap
    if cterm.__class__.__name__ == oterm.__class__.__name__: # both are kinds
        if cterm.name == oterm.name:
            if cterm.kind == 'element' and match(cterm.domain, oterm.domain) and match(cterm.codomain, oterm.codomain):
                return True
            if cterm.kind == 'type':
                return True
    elif oterm.__class__.__name__ == 'Gap':
        if oterm in varmap.keys():
            if varmap[oterm].equals(cterm):
                return True
        else:
            varmap[oterm] = cterm
            return True
    return False


somedomainp = Gap(name='p', kindix=0)
# somedomainq = Gap(name='q', kindix=0)
somedomainr = Gap(name='r', kindix=0)
somedomains = Gap(name='s', kindix=0)
# somedomaint = Gap(name='t', kindix=0)

onep = Variable(name='een', domain=somedomainp, codomain=getal)
allp = Variable(name='alle', domain=somedomainp, codomain=one)

someelementv = Gap(name='v', kindix=1, type=Application(functional_type, [somedomainp, getal]))
someelementw = Gap(name='w', kindix=1, type=Application(functional_type, [somedomainp, somedomainr]))
someelementu = Gap(name='u', kindix=1, type=Application(functional_type, [somedomains, getal]))
someelementz = Gap(name='z', kindix=1, type=Application(functional_type, [somedomains, somedomainr]))

somesumvw = Application(alpha, [someelementv, someelementw])
somesumuz = Application(alpha, [someelementu, someelementz])

someavgvwuz = Application(composition, [gedeelddoor, Application(product, [somesumvw, somesumuz])])

# someelementz = Gap(name='z', kindix=1, type=Application(functional_type, [somedomainp, somecodomainq]))
# someelementw = Gap(name='w', kindix=1, type=Application(functional_type, [somedomainr, somecodomainq]))
# someelementx = Gap(name='x', kindix=1, type=Application(functional_type, [somedomainp, getal]))
# someelementy = Gap(name='y', kindix=1, type=Application(functional_type, [somedomainp, getal]))
# someelementv = Gap(name='v', kindix=1, type=Application(functional_type, [somedomainr, getal]))
# someaggregatex = Application(alpha, [someelementx, someelementz])
# someaggregatey = Application(alpha, [someelementy, someelementz])
# someaggregateu = Application(alpha, [someelementv, someelementw])
# gemiddelde = Application(composition, [gedeelddoor, Application(product, [someaggregatex, someaggregatey])])
# complexgemiddelde = Application(composition, [gedeelddoor, Application(product, [someaggregatex, someaggregateu])])
