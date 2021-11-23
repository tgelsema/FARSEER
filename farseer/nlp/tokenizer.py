import pandas as pd
import os
import spacy
from spacy.matcher import PhraseMatcher, DependencyMatcher
from spacy.tokens import Doc, Span, Token
from spacy.symbols import LOWER, LEMMA, ORTH
from spacy.language import Language
from spacy.util import filter_spans

@Language.factory('keywords_component')
def create_keywords_component(nlp, name, keyword_file):
    return KeywordsComponent(nlp, keyword_file)

class KeywordsComponent:
    
    def __init__(self, nlp, keyword_file):
        keywordlist = pd.read_csv(keyword_file, sep=';')
        self.keywordlist = {c['term'].lower(): c['keyword'] for i, c in keywordlist.iterrows()}
        patterns = [nlp(c) for c in self.keywordlist.keys()]
        self.matcher = PhraseMatcher(nlp.vocab, LEMMA)
        self.matcher.add('keywords', None, *patterns)
        # Token.set_extension('keyword', default='<unk>', force=True)
        
    def __call__(self, doc):
        matches = self.matcher(doc, as_spans=True)
        spans = []
        for entity in matches:
            # entity = Span(doc, start, end, label='keyword')
            for token in entity:
                token._.set('keyword', self.keywordlist[token.text])
            doc.ents = [entity] + [ent for ent in doc.ents if not self.overlapping(ent, entity)]
            spans.append(entity)
        with doc.retokenize() as retokenizer:
            for span in spans:
                retokenizer.merge(span)
        return doc
        
    def overlapping(self, s1, s2):
        return len(set(range(s1.start,s1.end)).intersection(set(range(s2.start,s2.end)))) > 0


@Language.factory('tuples_component')
def create_tuples_component(nlp, name, tuple_file):
    return TuplesComponent(nlp, tuple_file)

class TuplesComponent:
    
    def __init__(self, nlp, tuple_file):
        tuples = pd.read_csv(tuple_file, sep=';')
        tuples['left'] = tuples['tuple'].apply(lambda x: x.split('__SEP__')[0])
        tuples['right'] = tuples['tuple'].apply(lambda x: x.split('__SEP__')[1:])
        patterns = tuples.groupby(['description']).agg({'left': lambda x: list(set(x)), 'right': lambda x: list(x.values[0])}).reset_index()
        self.matcher = DependencyMatcher(nlp.vocab)
        self.add_patterns(self.matcher, patterns)
        # Token.set_extension('objectname', default=None, force=True)
        # Token.set_extension('type', default=None, force=True)
        # Token.set_extension('keyword', default='<unk>', force=True)
        
    def __call__(self, doc):
        matches = self.matcher(doc)
        for m in matches:
            match_id, token_ids = m
            _, pattern = self.matcher.get(match_id)
            doc[token_ids[0]]._.set('objectname', pattern[0][0]["DESCRIPTION"])
            doc[token_ids[0]]._.set('keyword','<const>')
        return doc

        
    def add_patterns(self, matcher, patterns):
        for i, p in patterns.iterrows():
            for j, relation in enumerate(['<<', '>>', '$++', '$--']):
                res = []
                left = {}
                left["RIGHT_ID"] = f'p{i}_{j}'
                left["RIGHT_ATTRS"] = {'LEMMA': {"IN": p['left']}}
                left["DESCRIPTION"] = p['description']
                res.append(left)
                for p_right in p['right']:
                    right = {}
                    right["LEFT_ID"] = f'p{i}_{j}'
                    right["REL_OP"] = relation
                    right["RIGHT_ID"] = f'p{i}_{j}_subject'
                    right["RIGHT_ATTRS"] = {'LEMMA': {"IN": [p_right]}}
                    res.append(right)
                matcher.add(f'p{i}_{j}', [res])


@Language.factory('lookup_component')
def create_lookup_component(nlp, name, lookup_file):
    return LookupComponent(nlp, lookup_file)
        
class LookupComponent:
    
    def __init__(self, nlp, lookup_file):
        lookup = pd.read_csv(lookup_file, sep=';')
        self.lookup = {c['lemma']: self.create_order(c) for i, c in lookup.iterrows()}
        patterns = [nlp(c) for c in self.lookup.keys()]
        self.matcher = PhraseMatcher(nlp.vocab, attr=LEMMA)
        self.matcher.add('lookups', None, *patterns)

    def __call__(self, doc):
        matches = self.matcher(doc, as_spans=True)
        spans = []
        for entity in matches:
            # entity = Span(doc, start, end, label='lookup')
            spans.append(entity)
            # print(entity)

            for token in entity:
                text = self.lookup.get(entity.text.lower(), None)
                if text is None:
                    token._.set('objectname', self.lookup[entity.lemma_]['name'])
                    token._.set('type', self.lookup[entity.lemma_]['type'])
                    typename = self.lookup[entity.lemma_]['type']
                else:
                    if text.lemma == token.text.lower():
                        token._.set('objectname', text['name'])
                        token._.set('type', self.lookup[entity.text]['type'])
                        typename = self.lookup[entity.text]['type']
                    else:
                        token._.set('objectname', self.lookup[entity.text]['name'])
                        token._.set('type', self.lookup[entity.text]['type'])
                        typename = self.lookup[entity.text]['type']

                if typename == 'NumericalVariable':
                    token._.set('keyword', '<numvar>')
                if typename == 'CategoricalVariable': 
                    token._.set('keyword', '<catvar>')
                elif typename == 'ObjectTypeRelation':
                    token._.set('keyword', '<otr>')
                elif typename == 'ObjectType':
                    token._.set('keyword', '<ot>')
                elif typename == 'Constant':
                    token._.set('keyword', '<const>')
                else:
                    pass

            doc.ents = [ent for ent in doc.ents if not self.overlapping(ent, entity)] + [entity]
        
        spans = filter_spans(spans)
        with doc.retokenize() as retokenizer:
            for span in spans:
                retokenizer.merge(span)
        return doc
    
    def overlapping(self, s1, s2):
        return len(set(range(s1.start,s1.end)).intersection(set(range(s2.start,s2.end)))) > 0
    
    def create_order(self, s):
        if '__SEP__' in s['name']:
            s['name'] = s['name'].split('__SEP__')
        return s

class Tokenizer(object):
    
    def __init__(self, model, lookup, tuples, keywords):
        path = os.path.dirname(__file__)
        self.nlp = spacy.load(model)
        self.nlp.add_pipe('lookup_component', config={'lookup_file': os.path.join(path, lookup)})
        self.nlp.add_pipe('tuples_component', config={'tuple_file': os.path.join(path, tuples)}, after='lookup_component')
        self.nlp.add_pipe('keywords_component', config={'keyword_file': os.path.join(path, keywords)}, after='tuples_component')
        Token.set_extension('objectname', default=None, force=True)
        Token.set_extension('type', default=None, force=True)
        Token.set_extension('keyword', default='<unk>', force=True)
        
    def __call__(self, text, is_use_number_token=False):
        doc = self.nlp(text)
        res = pd.DataFrame([{
            'token':t.text.lower(),
            'objectname': t._.objectname,
            'keyword': t._.keyword,
            'pos': t.pos_,
            'number': t.like_num
        } for t in doc if t.pos_ != 'PUNCT'])
        
        if is_use_number_token:
            mask = res['number']
            res.loc[mask,'objectname'] = res.loc[mask,'token']
            res.loc[mask,'keyword'] = '<const>'

        tokenlist, objectlist, keywordlist = insertorder(res['token'].values, res['objectname'].values, res['keyword'].values)
        
        return tokenlist, objectlist, keywordlist          

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
    t, o, k = ([], [], []) 
    for i in range(len(keywordlist)):
        if type(objectlist[i]) is list:
            obj = objectlist[i][0]
            order = objectlist[i][1]
            if order == 'asc':
                k.append('<smallest>')
                t.append('kleinste')
            if order == 'desc':
                k.append('<greatest>')
                t.append('grootste')
            objectlist[i] = obj
            o.append(None)
        t.append(tokenlist[i])
        o.append(objectlist[i])
        k.append(keywordlist[i])
    return (t, o, k)

tokenizer = Tokenizer('nl_core_news_md', 'lookup.csv', 'tuples.csv', 'keywords.csv')


if __name__ == '__main__':
    # tekst = "Klaas woonde in Aa en Hunze maar is maart 2019 verhuisd naar 's-Gravenhage."
    # tekst = 'hoeveel wordt er per geslacht in Den Haag verdiend in totaal?'
    # tekst = 'welke gemeente heeft het kleinste aantal inwoners?'
    # tekst = 'Wat is de leeftijd van de oudste inwoner van Nederland'
    tekst = 'wat is het gemiddelde aantal personen op het adres in den haag' # goed
    # tekst = 'Hoe vaak werd er verzet gepleegd in Leiden?'
    # tekst = 'Hoe vaak pleegde men verzet in Leiden?'
    # tekst = "Hoe vaak was er sprake van wegrijden bij een ongeval." # goed
    # tekst = "Waar werden de meeste auto's gestolen?" # goed    
    t, o, k = tokenizer(tekst.lower())
    print(t, '\n', o, '\n', k)