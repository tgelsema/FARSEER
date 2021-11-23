from farseer.term.trm import *
from farseer.kind.knd import *

lookup = {}

# object types
persoon = ObjectType(name='persoon')
adres = ObjectType(name='adres')
gemeente = ObjectType(name='gemeente')
provincie = ObjectType(name='provincie')
bedrijf = ObjectType(name='bedrijf')
baan = ObjectType(name='baan')

# phenomena and quantities
getal = Quantity(name='getal')
datum = Quantity(name='datum')
tekst = Phenomenon(name='tekst')
gemeentenamen = Phenomenon(name='gemeentenamen')
provincienamen = Phenomenon(name='provincienamen')
straatnamen = Phenomenon(name='straatnamen')
geslachten = Phenomenon(name='geslachten')
huisnummers = Phenomenon(name='huisnummers')
namen = Phenomenon(name='namen')
identificator = Phenomenon(name='identificator')
activiteiten = Phenomenon(name='activiteiten')
beroepen = Phenomenon(name='beroepen')

# object type relations
woontop = ObjectTypeRelation(name='woont op', domain=persoon, codomain=adres)
ligtin = ObjectTypeRelation(name='ligt in', domain=adres, codomain=gemeente)
deelvan = ObjectTypeRelation(name='deel van', domain=gemeente, codomain=provincie)
werknemer = ObjectTypeRelation(name='werknemer', domain=baan, codomain=persoon)
werkgever = ObjectTypeRelation(name='werkgever', domain=baan, codomain=bedrijf)
gevestigdop = ObjectTypeRelation(name='gevestigd op', domain=bedrijf, codomain=adres)

# variables
leeftijd = Variable(name='leeftijd', domain=persoon, codomain=getal)
inkomen = Variable(name='inkomen', domain=persoon, codomain=getal)
lengte = Variable(name='lengte', domain=persoon, codomain=getal)
gewicht = Variable(name='gewicht', domain=persoon, codomain=getal)
geslacht = Variable(name='geslacht', domain=persoon, codomain=geslachten)
geboortedatum = Variable(name='geboortedatum', domain=persoon, codomain=datum)
naam = Variable(name='naam', domain=persoon, codomain=namen)
huisnummer = Variable(name='huisnummer', domain=adres, codomain=huisnummers)
straatnaam = Variable(name='straatnaam', domain=adres, codomain=straatnamen)
gemeentenaam = Variable(name='gemeentenaam', domain=gemeente, codomain=gemeentenamen)
provincienaam = Variable(name='provincienaam', domain=provincie, codomain=provincienamen)
functie = Variable(name='functie', domain=baan, codomain=beroepen)
salaris = Variable(name='salaris', domain=baan, codomain=getal)
omzet = Variable(name='omzet', domain=bedrijf, codomain=getal)
economischehoofdactiviteit = Variable(name='economische hoofdactiviteit', domain=bedrijf, codomain=activiteiten)

# keys and foreign keys
persoonid = Variable(name='persoon_id', domain=persoon, codomain=identificator)
adresid = Variable(name='adres_id', domain=adres, codomain=identificator)
gemeenteid = Variable(name='gemeente_id', domain=gemeente, codomain=identificator)
provincieid = Variable(name='provincie_id', domain=provincie, codomain=identificator)
persoonadresid = Variable(name='woont_op', domain=persoon, codomain=identificator)
adresgemeenteid = Variable(name='ligt_in', domain=adres, codomain=identificator)
gemeenteprovincieid = Variable(name='deel_van', domain=gemeente, codomain=identificator)
baanid = Variable(name='baan_id', domain=baan, codomain=identificator)
bedrijfid = Variable(name='bedrijf_id', domain=bedrijf, codomain=identificator)
baanpersoonid = Variable(name='werknemer', domain=baan, codomain=persoon)
baanbedrijfid = Variable(name='werkgever', domain=baan, codomain=persoon)
bedrijfadresid = Variable(name='gevestigd_op', domain=bedrijf, codomain=adres)

# nice to haves
eenpersoon = Variable(name='een(persoon)', domain=persoon, codomain=getal)
eenadres = Variable(name='een(adres)', domain=adres, codomain=getal)
eengemeente = Variable(name='een(gemeente)', domain=gemeente, codomain=getal)
eenbaan = Variable(name='een(baan)', domain=baan, codomain=getal)
eenbedrijf = Variable(name='een(bedrijf)', domain=bedrijf, codomain=getal)
allepersonen = Variable(name='alle(persoon)', domain=persoon, codomain=one)
allebanen = Variable(name='alle(baan)', domain=baan, codomain=one)

# constants
# cities
denhaag = Constant(name='Den Haag', codomain=gemeentenamen)
delft = Constant(name='Delft', codomain=gemeentenamen)
rotterdam = Constant(name='Rotterdam', codomain=gemeentenamen)
utrecht = Constant(name='Utrecht', codomain=gemeentenamen)
leiden = Constant(name='Leiden', codomain=gemeentenamen)

#provinces
zuidholland = Constant(name='Zuid-Holland', codomain=provincienamen)

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
maartje = Constant(name='Maartje', codomain=namen)
emma = Constant(name='Emma', codomain=namen)
john = Constant(name='John', codomain=namen)
hans = Constant(name='Hans', codomain=namen)
mirjam = Constant(name='Mirjam', codomain=namen)
petra = Constant(name='Petra', codomain=namen)
karsten = Constant(name='Karsten', codomain=namen)
thor = Constant(name='Thor', codomain=namen)
kirsten = Constant(name='Kirsten', codomain=namen)
marcel = Constant(name='Marcel', codomain=namen)
irene = Constant(name='Irene', codomain=namen)
robert = Constant(name='Robert', codomain=namen)
ellen = Constant(name='Ellen', codomain=namen)
chris = Constant(name='Chris', codomain=namen)
rachel = Constant(name='Rachel', codomain=namen)
jacob = Constant(name='Jacob', codomain=namen)
johanna = Constant(name='Johanna', codomain=namen)
jeroen = Constant(name='Jeroen', codomain=namen)
david = Constant(name='David', codomain=namen)
esther = Constant(name='Esther', codomain=namen)
diana = Constant(name='Diana', codomain=namen)
mathilde = Constant(name='Mathilde', codomain=namen)
jeroen = Constant(name='Jeroen', codomain=namen)
henriette = Constant(name='Henriette', codomain=namen)
sander = Constant(name='Sander', codomain=namen)
harry = Constant(name='Harry', codomain=namen)
barry = Constant(name='Barry', codomain=namen)
alex = Constant(name='Alex', codomain=namen)
samantha = Constant(name='Samantha', codomain=namen)
bob = Constant(name='Bob', codomain=namen)
richard = Constant(name='Richard', codomain=namen)
jack = Constant(name='Jack', codomain=namen)
jill = Constant(name='Jill', codomain=namen)
sandra = Constant(name='Sandra', codomain=namen)
peter = Constant(name='Peter', codomain=namen)
sabine = Constant(name='Sabine', codomain=namen)
ronald = Constant(name='Ronald', codomain=namen)
linda = Constant(name='Linda', codomain=namen)
tim = Constant(name='Tim', codomain=namen)
tom = Constant(name='Tom', codomain=namen)
selena = Constant(name='Selena', codomain=namen)
gerard = Constant(name='Gerard', codomain=namen)
aart = Constant(name='Aart', codomain=namen)
marjan = Constant(name='Marjan', codomain=namen)
erik = Constant(name='Erik', codomain=namen)
arnout = Constant(name='Arnout', codomain=namen)
thea = Constant(name='Thea', codomain=namen)
jacobiene = Constant(name='Jacobiene', codomain=namen)
ronaldo = Constant(name='Ronaldo', codomain=namen)
gaby = Constant(name='Gaby', codomain=namen)
guido = Constant(name='Guido', codomain=namen)

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
domainmodel = [persoon, adres, gemeente, provincie, baan, bedrijf, getal, datum, tekst, gemeentenamen, provincienamen, straatnamen, geslachten, huisnummers,
      namen, beroepen, activiteiten, woontop, ligtin, werknemer, werkgever, gevestigdop, leeftijd, inkomen, gewicht, lengte, geslacht, geboortedatum, naam, huisnummer, straatnaam, gemeentenaam,
      salaris, functie, omzet, economischehoofdactiviteit, man, vrouw, gedeelddoor, persoonid, adresid, gemeenteid, provincieid, baanid, bedrijfid]

#### persoonadresid, adresgemeenteid, bedrijfid, baanpersoonid, baanbedrijfid, bedrijfadresid

domainmodel.extend([denhaag, delft, rotterdam, utrecht,
      leiden, zuidholland, kolonel, wethouder, griffier, seismoloog, watermanager, oogarts, industrie, onderwijs, bouwnijverheid, openbaarbestuur,
      zakelijkedienstverlening, gezondheidszorg, tjalling, maartje, emma, john, hans, mirjam, petra, karsten, thor, kirsten,
      marcel, irene, robert, ellen, chris, rachel, jacob, johanna, david, esther, diana, mathilde, jeroen, henriette, sander,
      harry, barry, alex, samantha, bob, richard, jack, jill, sandra, peter, sabine, ronald, linda, tim, tom, selena, gerard,
      aart, marjan, erik, arnout, thea, jacobiene, ronaldo, gaby, aartvanderleeuwlaan, prinsmauritsstraat, westlandseweg,
      meppelerweg, lutherseburgwal, coolsingel, blaak, amsterdamsestraatweg, europalaan, josephhaydnlaan, rapenburg, wittesingel,
      haagweg, klikspaanweg])


# datasets
persoondata = DatasetDesign(name='persoon', constr=Application(product, [persoonid, naam, leeftijd, lengte, gewicht, geslacht, inkomen, persoonadresid]))
adresdata = DatasetDesign(name='adres', constr=Application(product, [adresid, straatnaam, huisnummer, adresgemeenteid]))
gemeentedata = DatasetDesign(name='gemeente', constr=Application(product, [gemeenteid, gemeentenaam, gemeenteprovincieid]))
provinciedata = DatasetDesign(name='provincie', constr=Application(product, [provincieid, provincienaam]))
baandata = DatasetDesign(name='baan', constr=Application(product, [baanid, functie, salaris, baanpersoonid, baanbedrijfid]))
bedrijfdata = DatasetDesign(name='bedrijf', constr=Application(product, [bedrijfid, economischehoofdactiviteit, omzet, bedrijfadresid]))

data = [persoondata, adresdata, gemeentedata, provinciedata, baandata, bedrijfdata]

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
    gemeente : eenpersoon
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
    'inwoner' : ObjectTypeRelation(name='inwoner', constr=Application(composition, [ligtin, woontop])),
    'inwoners' : ObjectTypeRelation(name='inwoner', constr=Application(composition, [ligtin, woontop])),
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
    'den haag' : denhaag,
    "'s-Gravenhage" : denhaag,
    'delft' : delft,
    'rotterdam' : rotterdam,
    'utrecht' : utrecht,
    'leiden' : leiden,
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
    'maartje' : maartje,
    'emma' : emma,
    'john' : john,
    'hans' : hans,
    'mirjam' : mirjam,
    'petra' : petra,
    'karsten' : karsten,
    'thor' : thor,
    'kirsten' : kirsten,
    'marcel' : marcel,
    'irene' : irene,
    'robert' : robert,
    'ellen' : ellen,
    'chris' : chris,
    'rachel' : rachel,
    'jacob' : jacob,
    'johanna' : johanna,
    'david' : david,
    'esther' : esther,
    'diana' : diana,
    'mathilde' : mathilde,
    'jeroen' : jeroen,
    'henriette' : henriette,
    'sander' : sander,
    'harry' : harry,
    'barry' : barry,
    'alex' : alex,
    'samantha' : samantha,
    'bob' : bob,
    'richard' : richard,
    'jack' : jack,
    'jill' : jill,
    'sandra' : sandra,
    'peter' : peter,
    'sabine' : sabine,
    'ronald' : ronald,
    'linda' : linda,
    'tim' : tim,
    'tom' : tom,
    'selena' : selena,
    'gerard' : gerard,
    'aart' : aart,
    'marjan' : marjan,
    'erik' : erik,
    'arnout' : arnout,
    'thea' : thea,
    'jacobiene' : jacobiene,
    'ronaldo' : ronaldo,
    'gaby' : gaby,
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
    'werkgever' : werkgever
}

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





