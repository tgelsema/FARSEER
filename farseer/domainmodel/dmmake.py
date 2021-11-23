from farseer.term.trm import Application, product, composition, cartesian_product
from farseer.kind.knd import Phenomenon, ObjectType, Variable, ObjectTypeRelation, DatasetDesign, Quantity, Constant, Operator, Level, one
from farseer.domainmodel.scmcodelookup import lookupscmcode
from farseer.domainmodel.maandlookup import lookupmaand
from farseer.domainmodel.interpretcodelists import addconsts, makescmcodedata, gemeenteconsts
import pickle

"""
Changes made:

- Removed datum as Quantity
- Added all Variables pointing to identifications to domainmodel, such that DatasetDesigns work with Graph

"""


lookup = {}

"""Personen, adressen, bedrijven, banen, gemeenten"""

# object types
persoon = ObjectType(name='persoon', altname='personen')
adres = ObjectType(name='adres', altname='adressen')
gemeente = ObjectType(name='gemeente', altname='gemeenten')
bedrijf = ObjectType(name='bedrijf', altname='bedrijven')
baan = ObjectType(name='baan', altname='banen')

# phenomena and quantities
getal = Quantity(name='getal')
datum = ObjectType(name='datum', altname='data')
tekst = Phenomenon(name='tekst')
gemeentenamen = Phenomenon(name='gemeentenamen')
straatnamen = Phenomenon(name='straatnamen')
geslachten = Phenomenon(name='geslachten')
huisnummers = Phenomenon(name='huisnummers')
namen = Phenomenon(name='namen')
identificaties = Phenomenon(name='identificatie')
activiteiten = Phenomenon(name='activiteiten')
beroepen = Phenomenon(name='beroepen')

# object type relations
woontop = ObjectTypeRelation(name='woont op', domain=persoon, codomain=adres)
ligtin = ObjectTypeRelation(name='ligt in', domain=adres, codomain=gemeente)
werknemer = ObjectTypeRelation(name='werknemer', domain=baan, codomain=persoon)
werkgever = ObjectTypeRelation(name='werkgever', domain=baan, codomain=bedrijf)
gevestigdop = ObjectTypeRelation(name='gevestigd op', domain=bedrijf, codomain=adres)
inwoner = ObjectTypeRelation(name='inwoner', constr=Application(composition, [ligtin, woontop]))

# variables
leeftijd = Variable(name='leeftijd', domain=persoon, codomain=getal, article='de')
inkomen = Variable(name='inkomen', domain=persoon, codomain=getal, article='het')
geslacht = Variable(name='geslacht', domain=persoon, codomain=geslachten, article='het')
naam = Variable(name='naam', domain=persoon, codomain=namen, article='de')
huisnummer = Variable(name='huisnummer', domain=adres, codomain=huisnummers, article='het')
straatnaam = Variable(name='straatnaam', domain=adres, codomain=straatnamen, article='de')
gemeentenaam = Variable(name='gemeentenaam', domain=gemeente, codomain=gemeentenamen, article='de')
gemeentecode = Variable(name='gemeentecode', domain=gemeente, codomain=gemeentenamen, article='de')
functie = Variable(name='functie', domain=baan, codomain=beroepen, article='de')
salaris = Variable(name='salaris', domain=baan, codomain=getal, article='het')
omzet = Variable(name='omzet', domain=bedrijf, codomain=getal, article='de')
economischehoofdactiviteit = Variable(name='economische hoofdactiviteit', domain=bedrijf, codomain=activiteiten, article='de')

# keys and foreign keys
persoonid = Variable(name='persoon_id', domain=persoon, codomain=identificaties)
adresid = Variable(name='adres_id', domain=adres, codomain=identificaties)
gemeenteid = Variable(name='gemeente_id', domain=gemeente, codomain=identificaties)
persoonadresid = Variable(name='woont_op', domain=persoon, codomain=identificaties)
adresgemeenteid = Variable(name='ligt_in', domain=adres, codomain=identificaties)
baanid = Variable(name='baan_id', domain=baan, codomain=identificaties)
bedrijfid = Variable(name='bedrijf_id', domain=bedrijf, codomain=identificaties)
baanpersoonid = Variable(name='werknemer', domain=baan, codomain=persoon)
baanbedrijfid = Variable(name='werkgever', domain=baan, codomain=persoon)
bedrijfadresid = Variable(name='gevestigd_op', domain=bedrijf, codomain=adres)

# nice to haves
eenpersoon = Variable(name='een(persoon)', domain=persoon, codomain=getal)
eenadres = Variable(name='een(adres)', domain=adres, codomain=getal)
eengemeente = Variable(name='een(gemeente)', domain=gemeente, codomain=getal)
eenbaan = Variable(name='een(baan)', domain=baan, codomain=getal)
eenbedrijf = Variable(name='een(bedrijf)', domain=bedrijf, codomain=getal)

allepersoon = Variable(name='alle(persoon)', domain=persoon, codomain=one)
alleadres = Variable(name='alle(adres)', domain=adres, codomain=one)
allegemeente = Variable(name='alle(gemeente)', domain=gemeente, codomain=one)
allebaan = Variable(name='alle(baan)', domain=baan, codomain=one)
allebedrijf = Variable(name='alle(bedrijf)', domain=bedrijf, codomain=one)

# constants
# cities
# denhaag = Constant(name='Den Haag', codomain=gemeentenamen)
# delft = Constant(name='Delft', codomain=gemeentenamen)
# rotterdam = Constant(name='Rotterdam', codomain=gemeentenamen)
# utrecht = Constant(name='Utrecht', codomain=gemeentenamen)
# leiden = Constant(name='Leiden', codomain=gemeentenamen)

# streets
aartvanderleeuwlaan = Constant(name='Aart van der Leeuwlaan', codomain=straatnamen)
prinsmauritsstraat = Constant(name='Prins Mauritsstraat', codomain=straatnamen)
westlandseweg = Constant(name='Westlandseweg', codomain=straatnamen)
meppelerweg = Constant(name='Meppelerweg', codomain=straatnamen)
lutherseburgwal = Constant(name='Lutherse Burgwal', codomain=straatnamen)
coolsingel = Constant(name='Coolsingel', codomain=straatnamen)
blaak = Constant(name='Blaak', codomain=straatnamen)
amsterdamsestraatweg = Constant(name='Amsterdamsestraatweg', codomain=straatnamen)
europalaan = Constant(name='Europalaan', codomain=straatnamen)
josephhaydnlaan = Constant(name='Joseph Haydnlaan', codomain=straatnamen)
rapenburg = Constant(name='Rapenburg', codomain=straatnamen)
wittesingel = Constant(name='Witte Singel', codomain=straatnamen)
haagweg = Constant(name='Haagweg', codomain=straatnamen)
klikspaanweg = Constant(name='Klikspaanweg', codomain=straatnamen)

# names
tjalling = Constant(name='Tjalling', codomain=namen)

#sexes
man = Constant(name='man', codomain=geslachten)
vrouw = Constant(name='vrouw', codomain=geslachten)

# occupations
kolonel = Constant(name='kolonel', codomain=beroepen)
wethouder = Constant(name='wethouder', codomain=beroepen)
griffier = Constant(name='griffier', codomain=beroepen)
seismoloog = Constant(name='seismoloog', codomain=beroepen)
watermanager = Constant(name='watermanager', codomain=beroepen)
oogarts = Constant(name='oogarts', codomain=beroepen)

# actitivities
industrie = Constant(name='industrie', codomain=activiteiten)
onderwijs = Constant(name='onderwijs', codomain=activiteiten)
bouwnijverheid = Constant(name='bouwnijverheid', codomain=activiteiten)
openbaarbestuur = Constant(name='openbaar bestuur', codomain=activiteiten)
zakelijkedienstverlening = Constant(name='zakelijke dienstverlening', codomain=activiteiten)
gezondheidszorg = Constant(name='gezondheidszorg', codomain=activiteiten)

# operators
gedeelddoor = Operator(name='(/)', domain=Application(cartesian_product,[getal, getal]), codomain=getal)

# domain model
domainmodel = [persoon, adres, gemeente, baan, bedrijf, getal, datum, tekst, gemeentenamen, straatnamen, geslachten, huisnummers,
      namen, beroepen, activiteiten, woontop, ligtin, werknemer, werkgever, gevestigdop, leeftijd, inkomen, geslacht, naam, huisnummer, straatnaam, gemeentenaam,
      salaris, functie, omzet, economischehoofdactiviteit, man, vrouw, gedeelddoor, persoonid, adresid, gemeenteid, baanid, bedrijfid, persoonadresid, adresgemeenteid, bedrijfid]

domainmodel.extend([
      kolonel, wethouder, griffier, seismoloog, watermanager, oogarts, industrie, onderwijs, bouwnijverheid, openbaarbestuur,
      zakelijkedienstverlening, gezondheidszorg, tjalling, aartvanderleeuwlaan, prinsmauritsstraat, westlandseweg,
      meppelerweg, lutherseburgwal, coolsingel, blaak, amsterdamsestraatweg, europalaan, josephhaydnlaan, rapenburg, wittesingel,
      haagweg, klikspaanweg, eenpersoon, eengemeente, eenadres, eenbaan, eenbedrijf, allepersoon, alleadres, allegemeente,
      allebaan, allebedrijf])

ones = [eenpersoon, eenadres, eengemeente, eenbaan, eenbedrijf]
alls = [allepersoon, alleadres, allegemeente, allebaan, allebedrijf]

# datasets
persoondata = DatasetDesign(name='persoon', constr=Application(product, [persoonid, naam, leeftijd, geslacht, inkomen, persoonadresid]))
adresdata = DatasetDesign(name='adres', constr=Application(product, [adresid, straatnaam, huisnummer, adresgemeenteid]))
gemeentedata = DatasetDesign(name='gemeente', constr=Application(product, [gemeenteid, gemeentenaam]))
baandata = DatasetDesign(name='baan', constr=Application(product, [baanid, functie, salaris, baanpersoonid, baanbedrijfid]))
bedrijfdata = DatasetDesign(name='bedrijf', constr=Application(product, [bedrijfid, economischehoofdactiviteit, omzet, bedrijfadresid]))

data = [persoondata, adresdata, gemeentedata, baandata, bedrijfdata]

# default variables
defaults = {
    persoon : [naam],
    adres : [straatnaam, huisnummer],
    gemeente : [gemeentenaam],
    baan : [baanid],
    bedrijf : [bedrijfid]
}

prefaggrmode = {
    leeftijd : 'avg',
    inkomen : 'sum',
    eenpersoon : 'sum',
    salaris : 'sum',
    omzet : 'sum'
}

prefvar = {
    namen : naam,
    huisnummers : huisnummer,
    geslachten : geslacht,
    gemeentenamen : gemeentenaam,
    straatnamen : straatnaam,
    beroepen : functie,
    activiteiten : economischehoofdactiviteit
}

orderedobjecttype = {
    adres : eenpersoon,
    gemeente : eenpersoon,
    bedrijf: omzet,
    baan : salaris
}

# lookup table
lookup = {
    'naam' : naam,
    'namen' : naam,
    'heet' : naam,
    'heten' : naam,
    'wonen' : woontop,
    'woont' : woontop,
    'persoon' : persoon,
    'personen' : persoon,
    'mens' : persoon,
    'mensen' : persoon,
    'adres' : adres,
    'adressen' : adres,
    'gemeente' : gemeente,
    'gemeenten' : gemeente,
    'gemeentenaam' : gemeentenaam,
    'huisnummers' : huisnummer,
    'huisnummer' : huisnummer,
    'nummer' : huisnummer,
    'leeftijd' : leeftijd,
    'inkomen' : inkomen,
    'oud' : leeftijd,
    'oudst' : [leeftijd, 'desc'],
    'oudste' : [leeftijd, 'desc'],
    'jongst' : [leeftijd, 'asc'],
    'jongste' : [leeftijd, 'asc'],
    'gezin' : adres,
    'gezinnen' : adres,
    'inwoner' : inwoner,
    'inwoners' : inwoner,
    'bewoner' : woontop,
    'bewoners' : woontop,
    'geslacht' : geslacht,
    'geslachten' : geslacht,
    'man' : man,
    'mannen' : man,
    'mannelijk' : man,
    'mannelijke' : man,
    'vrouw' : vrouw,
    'vrouwen' : vrouw,
    'vrouwelijk' : vrouw,
    'vrouwelijke' : vrouw,
    'ligt' : ligtin,
    'verdien' : inkomen,
    'verdient' : inkomen,
    'verdienen' : inkomen,
    'verdiend' : inkomen,
    'kolonel' : kolonel,
    'kolonels' : kolonel,
    'kolonellen' : kolonel,
    'wethouder' : wethouder,
    'wethouders' : wethouder,
    'griffier' : griffier,
    'griffiers' : griffier,
    'seismoloog' : seismoloog,
    'seismologen' : seismoloog,
    'watermanager' : watermanager,
    'watermanagers' : watermanager,
    'oogarts' : oogarts,
    'oogartsen' : oogarts,
    'industrie' : industrie,
    'industrieel' : industrie,
    'industriele' : industrie,
    'onderwijs' : onderwijs,
    'onderwijsinstelling' : onderwijs,
    'onderwijsinstellingen' : onderwijs,
    'school' : onderwijs,
    'scholen' : onderwijs,
    'bouwnijverheid' : bouwnijverheid,
    'bouwbedrijf' : bouwnijverheid,
    'bouwbedrijven' : bouwnijverheid,
    'openbaar bestuur' : openbaarbestuur,
    'zakelijke dienstverlening' : zakelijkedienstverlening,
    'zakelijke dienst' : zakelijkedienstverlening,
    'zakelijke diensten' : zakelijkedienstverlening,
    'gezondheidszorg' : gezondheidszorg,
    'werken' : werkgever,
    'werkt' : werkgever,
    'baan' : baan,
    'banen' : baan,
    'tjalling' : tjalling,
    'aart van der leeuwlaan' : aartvanderleeuwlaan,
    'prins mauritsstraat' : prinsmauritsstraat,
    'westlandseweg' : westlandseweg,
    'meppelerweg' : meppelerweg,
    'lutherse burgwal' : lutherseburgwal,
    'coolsingel' : coolsingel,
    'blaak' : blaak,
    'amsterdamsestraatweg' : amsterdamsestraatweg,
    'europalaan' : europalaan,
    'joseph haydnlaan' : josephhaydnlaan,
    'rapenburg' : rapenburg,
    'witte singel' : wittesingel,
    'haagweg' : haagweg,
    'klikspaanweg' : klikspaanweg,
    'werken' : werkgever,
    'werkt' : werkgever,
    'bedrijf' : bedrijf,
    'bedrijven' : bedrijf,
    'gevestigd' : gevestigdop,
    'vestiging' : gevestigdop,
    'salaris' : salaris,
    'activiteit' : economischehoofdactiviteit,
    'hoofdactiviteit' : economischehoofdactiviteit,
    'beroep' : beroepen,
    'beroepen' : beroepen,
    'functie' : functie,
    'functies' : functie,
    'woongemeente' : gemeente,
    'omzet' : omzet,
    'werknemer' : werknemer,
    'werkgever' : werkgever,
    'werknemers' : werknemer,
    'werkgevers' : werkgever
}

orientation = {
        werknemer : persoon,
        werkgever : bedrijf,
        woontop : persoon,
        gevestigdop : bedrijf,
        ligtin : adres,
        inwoner : persoon}

overridetarget = {
    beroepen : persoon,
    geslachten : persoon,
    activiteiten : bedrijf
}

optimalpathhelper = {
    werkgever : ["in", [gevestigdop]]
}

whichway = {
    baan : werkgever
}

interrogativepronouns = {
        persoon : 'wie',
        adres : 'waar',
        gemeente : 'waar'}

"""
    Delicten, buurten, data
"""

vocab = []

# object types
delict = ObjectType(name='delict', altname='delicten')
# buurt = ObjectType(name='buurt')
# gemeente = ObjectType(name='gemeente')
# datum = ObjectType(name='datum', altname='data') #moved to top

# phenomena and quantities
# getal = Quantity(name='getal')
# gemeentenamen = Phenomenon(name='gemeentenaam')
dagen = Phenomenon(name='dagen')
maanden = Phenomenon(name='maanden')
# buurtnamen = Phenomenon(name='buurtnaam')
# delictsoorten = Phenomenon(name='delictsoort')

# locatiesoorten = Phenomenon(name='locatiesoort')
identificaties = Phenomenon(name='identificatie')

# soorten delict
soortdelictlevel0 = Level("SCM code level 0")
soortdelictlevel1 = Level("SCM code level 1")
soortdelictlevel2 = Level("SCM code level 2")
soortdelictlevel3 = Level("SCM code level 3")

# object type relations
gepleegdin = ObjectTypeRelation(name='gepleegd in', domain=delict, codomain=gemeente)
# onderdeelvan = ObjectTypeRelation(name='onderdeel van', domain=buurt, codomain=gemeente)
gepleegdop = ObjectTypeRelation(name='gepleegd op', domain=delict, codomain=datum)

# variables
# gemeentenaam = Variable(name='gemeentenaam', domain=gemeente, codomain=gemeentenamen)
# buurtnaam = Variable(name='buurtnaam', domain=buurt, codomain=buurtnamen)
soortlevel0 = Variable(name='soort level 0', domain=delict, codomain=soortdelictlevel0, article='het')
soortlevel1 = Variable(name='soort level 1', domain=delict, codomain=soortdelictlevel1, article='het')
soortlevel2 = Variable(name='soort level 2', domain=delict, codomain=soortdelictlevel2, article='het')
soortlevel3 = Variable(name='soort level 3', domain=delict, codomain=soortdelictlevel3, article='het')
aantalverdachten = Variable(name='aantal verdachten', domain=delict, codomain=getal, article='het')
# soortlocatie = Variable(name='soort locatie', domain=delict, codomain=locatiesoorten)
dag = Variable(name='dag', domain=datum, codomain=dagen, article='de')
maand = Variable(name='maand', domain=datum, codomain=maanden, article='de')

# keys and foreign keys
delictid = Variable(name='delict_id', domain=delict, codomain=identificaties)
# gemeenteid = Variable(name='gemeente_id', domain=gemeente, codomain=identificaties)
# buurtid = Variable(name='buurt_id', domain=buurt, codomain=identificaties)
datumid = Variable(name='datum_id', domain=datum, codomain=identificaties)
# delictbuurtid = Variable(name='gepleegd_in', domain=delict, codomain=buurt)
delictdatumid = Variable(name='gepleegd_op', domain=delict, codomain=identificaties)
# buurtgemeenteid = Variable(name='onderdeel_van', domain=buurt, codomain=gemeente)
delictgemeenteid = Variable(name='gepleegd_in', domain=delict, codomain=identificaties)

# nice to haves
eendelict = Variable(name='een(delict)', domain=delict, codomain=getal)
# eenbuurt = Variable(name='een', domain=buurt, codomain=getal)
# eengemeente = Variable(name='een', domain=gemeente, codomain=getal)
eendatum = Variable(name='een(datum)', domain=datum, codomain=getal)

alledelict = Variable(name='alle(delict)', domain=delict, codomain=one)
alledatum = Variable(name='alle(datum)', domain=datum, codomain=one)

ones += [eendelict, eendatum]
alls += [alledelict, alledatum]


# operators
# gedeelddoor = Operator(name='(/)', domain=Application(cartesian_product,[getal, getal]), codomain=getal)


# domain model
domainmodel += [delict, dagen, maanden,
               identificaties, gepleegdin, gepleegdop,
               soortdelictlevel0, soortdelictlevel1, soortdelictlevel2, soortdelictlevel3,
               soortlevel0, soortlevel1, soortlevel2, soortlevel3,
               aantalverdachten, dag, maand, delictid, datumid,
               eendelict, eendatum, alledelict, alledatum]

lookupdm = {
        'delict' : delict,
        'misdrijf' : delict,
        'vergrijp' : delict,
        'overtreding': delict,
        'datum' : datum,
        'data' : datum,
        'dag': datum,
        'dagen' : datum,
        'maand' : maand,
        'maanden' : maand,
        'verdachten' : aantalverdachten,
        'hoeveel verdachten' : aantalverdachten,
        'aantal verdachten' : aantalverdachten
}

# constants
# cities

# neighborhoods

# locations
# addconsts('aardlocatie.xml', locatiesoorten, domainmodel)

# crimes
domainmodel += makescmcodedata([soortdelictlevel0, soortdelictlevel1, soortdelictlevel2, soortdelictlevel3])

# days
addconsts('./farseer/domainmodel/dag.xml', dagen, domainmodel, False)

# months
addconsts('./farseer/domainmodel/maand.xml', maanden, domainmodel, True)

# datasets
delictdata = DatasetDesign(name='delict', constr=Application(product, [delictid, soortlevel0, soortlevel1,
                                                                       soortlevel2, soortlevel3, aantalverdachten,
                                                                       delictdatumid, delictgemeenteid]))
# buurtdata = DatasetDesign(name='buurt', constr=Application(product, [buurtid, buurtnaam, buurtgemeenteid]))
# gemeentedata = DatasetDesign(name='gemeente', constr=Application(product, [gemeenteid, gemeentenaam]))
datumdata = DatasetDesign(name='datum', constr=Application(product, [datumid, dag, maand]))

data += [delictdata, datumdata]

# default variables
defaults[delict] = []
# defaults[buurt] = [buurtnaam]
defaults[datum] = [dag, maand]

prefaggrmode[aantalverdachten] = 'avg'

prefvar[maanden] = maand
prefvar[dagen] = dag
prefvar[soortdelictlevel0] = soortlevel0
prefvar[soortdelictlevel1] = soortlevel1
prefvar[soortdelictlevel2] = soortlevel2
prefvar[soortdelictlevel3] = soortlevel3
# prefvar[buurtnamen] = buurtnaam

orderedobjecttype[delict] = eendelict
orderedobjecttype[datum] = eendatum

# below is probably wrong
# prefvar[soortlevel0] = soortdelictlevel0
# prefvar[soortlevel1] = soortdelictlevel1
# prefvar[soortlevel2] = soortdelictlevel2
# prefvar[soortlevel3] = soortdelictlevel3

# prefvar[gemeentenamen] = gemeentenaam

# orderedobjecttype[delict] = None
# orderedobjecttype[buurt] = None
# orderedobjecttype[datum] = None


# lookup table

# lookup = {

# }

overridetarget[soortdelictlevel0] = delict
overridetarget[soortdelictlevel1] = delict
overridetarget[soortdelictlevel2] = delict
overridetarget[soortdelictlevel3] = delict


# optimalpathhelper = {
# }

# streets
# with open('straatnamen.txt') as f:
#     for line in f:
#         c = Constant(name=line.rstrip(), codomain=straatnamen)
#         domainmodel.append(c)
#         lookup[line.rstrip().lower()] = c
        

# if __name__ == '__main__':

gemconsts = gemeenteconsts(gemeentenamen)

for c in gemconsts:
    if not c.name.lower() in lookup.keys():
        lookup[c.name.lower()] = c
        if c.name.lower() == "'s-gravenhage":
            lookup['den haag'] = c

domainmodel += gemconsts

for k in lookupmaand.keys():
    for d in domainmodel:
        if lookupmaand[k] == d.name:
            lookup[k] = d
for k in lookupscmcode.keys():
    for d in domainmodel:
        if lookupscmcode[k] == d.name:
            lookup[k] = d
for k in lookupdm.keys():
    lookup[k] = lookupdm[k]
for k in lookup.keys():
    if isinstance(k, tuple):
        for l in k:
            if not l in vocab:
                vocab.append(l)
    else:
        if not k in vocab:
            vocab.append(k)
for d in domainmodel:
    if d.name == 'SCM code - level 1':
        prefvar[d] = soortlevel1
    if d.name == 'SCM code - level 2':
        prefvar[d] = soortlevel2
    if d.name == 'SCM code - level 3':
        prefvar[d] = soortlevel3
    if d.name == 'SCM code - level 0':
        prefvar[d] = soortlevel0

def savedomainmodel():
    dm = [lookup, domainmodel, prefvar, defaults, overridetarget, prefaggrmode,
          vocab, interrogativepronouns, whichway, optimalpathhelper, orientation,
          orderedobjecttype, data, getal, gedeelddoor, one, ones, alls]
    with open('./farseer/domainmodel/dm.pickle', mode='wb') as fw:
        pickle.dump(dm, fw, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    savedomainmodel()