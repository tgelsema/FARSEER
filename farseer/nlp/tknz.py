# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 11:51:36 2018

@authors: Guido van den Heuvel, Tjalling Gelsema
"""

__package__ = 'farseer.nlp'

import re
from farseer.kind.knd import Constant
from farseer.domainmodel.dm import vocab
# from _jellyfish import damerau_levenshtein_distance
import pickle
import io
import os
import numpy as np
import time
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from farseer.nlp.tokenizer import tokenizer
from farseer.graphdb.graphdb import graph


vectors_filename = 'wiki.nl.vec' # file with word vectors from a corpus: the full corpus of Dutch wiki pages
vocab_size = 150000 # number of words to keep in a vocabulary from the corpus (corpus has over 600.000 words)
"""Rerun load_and_save_corpus() if either vectors_filename or vocab_size is changed
"""
cosine_threshold = 0.6 # if cosine_similarity exceeds cosine_threshold, treat corresponding word as a synonym
distance_threshold = 0.35 # if damerau_levenshtein_distance is below distance_threshold, treat corresponding word as synonym

"""Load the lists of words 'words' (partial vocabulary from a given corpus of
text) and 'words_in_vocab' (the intersection of 'words' with the domain model
vocab) and their corresponding word vectors 'X' and 'Y' respectively from a
pickle file. Rerun load_and_save_corpus() if vectors_filename is changed (i.e.,
a different corpus is required) or if vocab_size is changed (the number of
words taken from the corpus is changed).
"""
with open('./farseer/nlp/tknz.pickle', mode='rb') as fr:
    tkz = pickle.load(fr)
words = tkz[0]
X = tkz[1]
words_in_vocab = tkz[2]
Y = tkz[3]

"""Read lookup csv for use in named entity recognition"""
lookup_df = pd.read_csv(os.path.join('farseer','nlp','lookup.csv'), sep=';')
lookup = {lemma: (name, type) for (lemma, name, type) in zip(lookup_df['lemma'], lookup_df['name'], lookup_df['type']) }
"""A list of stop words. No synonyms will be sought for a stop word.
"""
stopwords = [
        'met',
        'bij',
        'op',
        'in',
        'van',
        'uit',
        'aantal',
        'aantallen',
        'hoeveel',
        'vaak',
        'totale',
        'totaal',
        'gemiddelde',
        'gemiddeld',
        'ieder',
        'iedere',
        'elk',
        'elke',
        'al',
        'alle',
        'welk',
        'welke',
        'wat',
        'wie',
        'waar',
        'hoe',
        'per',
        'naar',
        'voor',
        'over',
        'grootst',
        'grootste',
        'hoogst',
        'hoogste',
        'kleinst',
        'kleinste',
        'laagst',
        'laagste',
        'meest',
        'meeste',
        'minst',
        'minste',
        'de',
        'het',
        'een',
        'is',
        'zijn',
        'was',
        'waren',
        'heeft',
        'hebben',
        'had',
        'hadden',
        'worden',
        'wordt',
        'werd',
        'werden',
        'er',
        'en',
        'of',
        'aan',
        'dat',
        'die',
        'daar',
        'dan',
        'als',
        'zij',
        'hij',
        'haar',
        'hem',
        'hun',
        'hen',
        'ons',
        'onze',
        'door'
]

"""The list of key words that can appear in the keywordlist
"""
keywordvocab = {
        '<empty>' : 0,
        '<unk>' : 1,
        '<ot>' : 2,
        '<otr>' : 3,
        '<numvarsum>' : 4,
        '<numvaravg>' : 5,
        '<numvar>' : 6,
        '<catvar>' : 7,
        '<const>' : 8,
        '<num>' : 9,
        '<howmany>' : 10,
        '<sum>' : 11,
        '<tot>' : 12,
        '<avg>' : 13,
        '<all>' : 14,
        '<per>' : 15,
        '<prep>' : 16,
        '<whowhat>' : 17,
        '<most>' : 18,
        '<least>' : 19,
        '<with>' : 20,
        '<greatest>' : 21,
        '<smallest>' : 22,
        '<number>' : 23
}


def insertorder(tokenlist, objectlist, keywordlist):
    """A value in the domain model lookup table can be a list, consisting of
    an object in the domain model, and one of the words 'asc' or 'desc'. To
    keep the list of objects clean (i.e., free from such lists), a little trick
    is performed, inserting the keyword <smallest> or <greatest> at strategic
    positions in the keyword list. Tokenlist and objectlist are updated
    accordingly. For instance, a token 'oudst' is associated with the list
    [leeftijd, 'desc'] in the domain model lookup table. Then, just before the
    occurence of 'oudst' in the token list, the word 'grootste' is inserted,
    and the keyword '<greatest>' is inserted in the keywordlist at the
    corresponding position. At the position of the word 'oudst' in the
    objectlist, the object (variable) 'leeftijd' replaces the pair
    [leeftijd, 'desc']. The updated tokenlist, objectlist and keywordlist are
    returned.
    """
    i = 0
    while i < len(keywordlist):
        if type(objectlist[i]) is list:
            obj = objectlist[i][0]
            order = objectlist[i][1]
            if order == 'asc':
                keywordlist.insert(i, '<smallest>')
                tokenlist.insert(i, 'kleinste')
            if order == 'desc':
                keywordlist.insert(i, '<greatest>')
                tokenlist.insert(i, 'grootste')
            objectlist[i] = obj
            objectlist.insert(i, None)
        i += 1
    return (tokenlist, objectlist, keywordlist)

def getkeywordlist(tokenlist, objectlist):
    """From a list of tokens and a corresponding list of objects, construct a
    list of keywords by matching a token against occurrences of special words
    (such as 'aantal', 'naar', 'meest' etc.), and/or by inspecting the kind
    of corresponding object against special types (such as an object type, an
    object type relation, a variable or a constant). If no match is found,
    insert the special keyword '<unk>' (unknown). Keep a list of keywords
    and return it, once matching is finished.
    """
    keywords = []
    for t in tokenlist:
        i = tokenlist.index(t)
        o = objectlist[i]
        if t == 'met':
            t = '<with>'
        if t == 'bij' or t == 'op' or t == 'in' or t == 'van' or t == 'uit': #### over, van, met?
            t = '<prep>'
        if t == 'aantallen' or t == 'aantal':
            t = '<num>'
        if t == 'hoeveel' or t == 'vaak':
            t = '<howmany>'
        if t == 'totale' or t == 'totaal':
            t = '<tot>'
        if t == 'gemiddelde' or t == 'gemiddeld':
            t = '<avg>'
        if t == 'iedere' or t == 'elke' or t == 'elk' or t =='ieder' or t == 'alle' or t == 'al':
            t = '<all>'
        if t == 'welk' or t == 'wat' or t == 'welke' or t == 'wie' or t == 'waar':
            t = '<whowhat>'
        if t == 'per' or t == 'naar' or t == 'voor' or t == 'over': #### van, over?
            t = '<per>'
        if t == 'grootste' or t == 'grootst' or t == 'hoogst' or t == 'hoogste' or t == 'maximum' or t == 'maximaal' or t == 'maximale':
            t = '<greatest>'
        if t == 'kleinste' or t == 'kleinst' or t == 'laagst' or t == 'laagste' or t == 'minimum' or t == 'minimaal' or t == 'minimale':
            t = '<smallest>'
        if t == 'meest' or t == 'meeste':
            t = '<most>'
        if t == 'minst' or t == 'minste':
            t = '<least>'
        if o != None:
            if o.__class__.__name__ == 'ObjectTypeRelation':
                keywords.append('<otr>')
            elif o.__class__.__name__ == 'ObjectType':
                keywords.append('<ot>')
            elif o.__class__.__name__ == 'Constant':
                keywords.append('<const>')
            elif o.__class__.__name__ == 'Variable':
                if o.codomain.name == 'getal':
                    keywords.append('<numvar>')
                    #### if prefaggrmode[o] == 'avg':
                    ####     keywords.append('<numvaravg>')
                    #### else:
                    ####     keywords.append('<numvarsum>')
                else:
                    keywords.append('<catvar>')
            elif isinstance(o, list):
                if len(o) > 0:
                    if o[0].__class__.__name__ == 'Variable':
                        if o[0].codomain.name == 'getal':
                            keywords.append('<numvar>')
                        else:
                            keywords.append('<catvar>')
            elif o.name == 'getal':
                keywords.append('<number>')
        elif t in keywordvocab.keys():
            keywords.append(t)
        else: ####
            keywords.append('<unk>') ####
    return keywords


""" Main routine"""

def tokenize(s):
    tokens, object_names, keywords = tokenizer(s.lower())
    objects = [graph.get_kind(object_name) for object_name in object_names]
    objects, synonyms = named_entity_recognition(tokens, objects)
    keywords = add_synonym_keywords(objects, synonyms, keywords)
    return tokens, synonyms, objects, keywords

def add_synonym_keywords(objects, synonyms, keywords):
    #Quick function made to add missing keywords for synonyms, should be incorporated in tokenizer.py
    for index, (o, s) in enumerate(zip(objects, synonyms)):
        if o and s:
            if o.__class__.__name__ == 'ObjectTypeRelation':
                keywords[index] = '<otr>'
            elif o.__class__.__name__ == 'ObjectType':
                keywords[index] = '<ot>'
            elif o.__class__.__name__ == 'Constant':
                keywords[index] = '<const>'
            elif o.__class__.__name__ == 'Variable':
                if o.codomain.name == 'getal':
                    keywords[index] = '<numvar>'
                    #### if prefaggrmode[o] == 'avg':
                    ####     keywords.append('<numvaravg>')
                    #### else:
                    ####     keywords.append('<numvarsum>')
                else:
                    keywords.append('<catvar>')
            elif isinstance(o, list):
                if len(o) > 0:
                    if o[0].__class__.__name__ == 'Variable':
                        if o[0].codomain.name == 'getal':
                            keywords[index] = '<numvar>'
                        else:
                            keywords[index] = '<catvar>'
            elif o.name == 'getal':
                keywords[index] = '<number>'
    return keywords


def tokenize_old(s, token_list, is_use_number_token=False):
    """Tokenize a string s using a lookup table given by token_list, with an
    option for tokenizing numbers (as constants with codomain 'getal'). Find
    corresponding objects in the domain model lookup table. Keep a tokenlist and
    a corresponding object list of equal length. Find synonyms using the
    routine 'named_entity_recognition' and update the object list accordingly.
    Then look for tuples and triples in the tokenlist (or synonym list) and
    see if they are a key in the domain model lookup table. Update objectlist
    accordingly. Finally, keep a keyword list of length tokenlist and fill it
    with special keywords. Return the lists of tokens, objects and keywords.
    """
    (tokenlist, objectlist) = tknz(s, token_list, is_use_number_token)
    (objectlist, synonymlist) = named_entity_recognition(tokenlist, objectlist)
    objectlist = search_tuples_and_triples(tokenlist, synonymlist, objectlist)
    keywordlist = getkeywordlist(tokenlist, objectlist)
    (tokenlist, objectlist, keywordlist) = insertorder(tokenlist, objectlist, keywordlist)
    return (tokenlist, synonymlist, objectlist, keywordlist)

"""End main routine"""


"""Named entity recognition using word embeddings"""

def named_entity_recognition(tokenlist, objectlist):
    """Find synonyms in the domain model vocab for all tokens in
    tokenlist not in the stopwords list, using word embeddings and damerau-
    levenshtein distance from the maximum_similarity routine. Keep a list
    of synonyms and update objectlist if a synonym is found that is a key in
    the domain model lookup table. Return synonymlist and the updated
    objectlist.
    """
    synonymlist = [None] * len(tokenlist)
    i = 0
    while i < len(tokenlist):
        if objectlist[i] == None and not tokenlist[i] in stopwords and not tokenlist[i] in vocab:
            synonym = maximum_similarity(tokenlist[i])
            if synonym in lookup.keys():
                objectlist[i] = graph.get_kind(lookup[synonym][0], lookup[synonym][1])
            if synonym in vocab:
                synonymlist[i] = synonym
        i += 1
    return (objectlist, synonymlist)

def search_tuples_and_triples(tokenlist, synonymlist, objectlist):
    """As keys, the domain model lookup table may contain tuples or triples of
    words. This routine lists through all tuples and triples of words in
    sysnonymlist (and if a word is not found in synonymlist, then it takes the
    corresponding word from tokenlist). If a tuple or triple is a key in the
    domain model lookup table, it adjusts objectlist. The updates objectlist is
    returned.
    """
    i = 0
    while i < len(tokenlist):
        u = synonymlist[i] if synonymlist[i] != None else tokenlist[i]
        j = i + 1
        while j < len(tokenlist):
            v = synonymlist[j] if synonymlist[j] != None else tokenlist[j]
            if (u, v) in lookup.keys():
                objectlist[i] = lookup[(u, v)]
            if (v, u) in lookup.keys():
                objectlist[i] = lookup[(v, u)]
            k = j + 1
            while k < len(objectlist):
                w = synonymlist[k] if synonymlist[k] != None else tokenlist[k]
                if (u, v, w) in lookup.keys():
                    objectlist[i] = lookup[(u, v, w)]
                if (u, w, v) in lookup.keys():
                    objectlist[i] = lookup[(u, w, v)]
                if (v, u, w) in lookup.keys():
                    objectlist[i] = lookup[(v, u, w)]
                if (v, w, u) in lookup.keys():
                    objectlist[i] = lookup[(v, w, u)]
                if (w, u, v) in lookup.keys():
                    objectlist[i] = lookup[(w, u, v)]
                if (w, v, u) in lookup.keys():
                    objectlist[i] = lookup[(w, v, u)]
                k += 1
            j += 1
        i += 1
    return objectlist
        
"""End named entity recognition using word embeddings"""


"""Tokenization"""

def tknz(s, token_list, is_use_number_token = False):
    """
    This function tokenizes the input s, which is processed to only contain lowercase alphanumeric characters and spaces. 
    It returns a list of text fragments found that correspond to tokens in token_list, in the order that these 
    have been found. When multiple matches are possible it uses the longest one. E.g., if the tokens "aart" and
    "aart van der leeuwlaan" both exist, the input "aart van der leeuwlaan" is returned as a single token.

    Each word in the input that is not detected as being part of any token in token_list, is returned as a 
    separate fragment.

    The result also contains a second list, with the tokens found. Both lists have the same length, and the same
    position in both lists corresponds to the same token. Each token found in token_list has the token found as
    entry in the second list; for words not part of any token, the corresponding entry in the second list is set to None.

    If is_use_number_token == True, then the second list contains a constant with codomain "getal" for numbers not in token_list,
    in stead of None.
    """
    result = ([], [])

    s = re.sub('[?.!/;:,\n]', '', s)	# remove characters from query
    s = s.lower() # all lowercase
    words = s.split(" ")

    while words:
        for l in range(len(words), 0, -1):
            potential_token = " ".join(words[0:l])
            if potential_token in token_list.keys():
                result[0].append(potential_token)
                token = token_list[potential_token]
                result[1].append(token)
                words = words[l:]
                break
        else:
            result[0].append(potential_token)
            # rudimentary number detection. Can be switched on by setting is_use_number_token to True
            if is_use_number_token and re.fullmatch(r"\d+", potential_token):
                result[1].append(Constant(potential_token, getal))
            else:
                result[1].append(None)
            words = words[1:]

    return result

"""End tokenization"""


"""Word embeddings"""

def load_words_from_fasttext(fname, nwanted = 15):
    """Load a vocabulary from a given corpus of text and the corresponding
    word vectors from the file given by 'fname'. Get the first 'nwanted' words
    and vectors and store them in 'wordlist' and the 'X' np.array respectively.
    Return 'wordslist' and 'X'.
    """
    fin = io.open(fname, "r", encoding='utf-8', newline='\n', errors='ignore')
    n, d = map(int, fin.readline().split())
    wordlist = []
    X = np.empty((nwanted, d))
    for i, line in enumerate(fin):
        if i == nwanted:
            break
        tokens = line.rstrip().split(' ')
        wordlist.append(tokens[0])
        X[i, :] = list(map(float, tokens[1:]))
    return (wordlist, X)

def match_words_with_vocab(words, X):
    """Find the intersection of the word list given by 'words' with the words
    in the domainmodel vocab. Copy the corresponding word vectors in the 'Y'
    np.array. Return the intersection 'wordlist' and the vectors 'Y'.
    """
    wordlist = []
    Y = np.empty((0, X.shape[1]))
    for word in vocab:
        try:
            i = words.index(word)
            Y = np.append(Y, X[np.newaxis, i, :], axis = 0)
            wordlist.append(word)
        except ValueError:
            continue
    return (wordlist, Y)

def load_and_save_corpus():
    """Open a file of word vectors given by 'vectors_filename' and store the
    first 'vocab_size' words in the 'words' list. Store the vectors in the 'X'
    np.array. Then match 'words' with the vocab from the domain model. Store
    their intersection in the 'words_in_vocab' list and corresponding vectors
    in the 'Y' np.array. Finally save the four as a pickle file 'tknz.pickle'.
    This pickle file becomes automatically loaded once tknz.py is loaded.
    """
    (words, X) = load_words_from_fasttext(vectors_filename, vocab_size)
    (words_in_vocab, Y) = match_words_with_vocab(words, X)
    tkz = [words, X, words_in_vocab, Y]
    with open('./farseer/nlp/tknz.pickle', mode='wb') as fw:
        pickle.dump(tkz, fw, protocol=pickle.HIGHEST_PROTOCOL)

def maximum_similarity(word):
    """Find a word in the domainmodel vocab that matches a given 'word' best
    using cosine similarity between corresponding word vectors. If 'word' is
    not found in the corpus vocabulary, or if the cosine similarity does not
    meet a cosine_threshold, compute the damerau_levenshtein_distance between
    the given word and all words in the domainmodel vocab. Find the word with
    the least distance and return it if it is below a distance_threshold.
    Otherwise return the empty word.
    """
    try:
        i = words.index(word)
        U = X[np.newaxis, i]
        V = cosine_similarity(Y, U)
        max_similarity = max(V)
        max_i = np.argmax(V)
        if max_similarity >= cosine_threshold:
            return words_in_vocab[max_i]
    except ValueError:
       pass
    W = np.array([damerau_levenshtein_distance(word, w) / (max(len(word), len(w))) for w in words_in_vocab])
    min_distance = min(W)
    min_i = np.argmin(W)
    if min_distance <= distance_threshold:
        return words_in_vocab[min_i]
    return ""

"""End word embeddings"""

"""Switch off if jellyfish is installed """
def damerau_levenshtein_distance(word, w):
    return 10 # replace by 10
"""End switch off """


if __name__ == '__main__':
    # Returns (['24', vierentwintig])
    # Note that vierentwintig is a special token, and the only number, in the current token_list.
        # print(tokenize("24", lookup))

    # Returns (['hoeveel', 'mensen', 'wonen',  'er', 'op', 'aart van der leeuwlaan', '26'], 
    #          [None,      persoon,  woont op, None, None, aartvanderleeuwlaan,      None])
        # print(tokenize("hoeveel mensen wonen er op aart van der leeuwlaan 26", lookup, False))

    # Returns (['wonen',  'aart', 'en', 'ellen', 'op', 'aart van der leeuwlaan', '28',  'of', 'joseph haydnlaan', '132'], 
    #          [woont op, Aart,   None, Ellen,   None, aartvanderleeuwlaan,      getal, None, josephhaydnlaan,    getal])
        # print(tokenize("wonen aart en ellen op aart van der leeuwlaan 28 of joseph haydnlaan 132", lookup, True))
        
        #print(tokenize('Hoe vaak werd er verzet gepleegd in Leiden?', lookup))
        #print(tokenize('Hoe vaak werd er verzet gepleegd in Leiden?'))
        #start = time.perf_counter()
        #end = time.perf_counter()
        #print("took", end-start)
        #print(tokenize('aantal inbraken'))
        #print(tokenize('Hoe vaak was er sprake van wegrijden bij een ongeval?', lookup))
    print(tokenize('Delft'))