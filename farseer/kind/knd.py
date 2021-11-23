__package__ = 'farseer.kind'

"""The kind Python module exposes a number of classes that represent pieces of
metadata that are statistically meaningful. The Kind class is the abstract base
class for all other classes the kind module exposes. From Kind, the abstract
classes Type and Element are derived. A Type can be thought of as a set of
things; an Element can be thought of as a function from one set (its domain) to
another (its codomain). Operations acting on Types and Elements are given in
the term Python module. These operations can be used to construct a Term (see
the term Python module) that represents the internal structure of a Kind
instance, for instance: the internal structure of a dataset design

Functionality for translating the formal internal structure of a Kind (see also
the documentation of the term Python module) to xml form is also provided.

In an informal way, a Kind instance may (also) be associated with other Kind
instances; these are stored in an ordered dictionary which can be accessed as
the Kind instance attribute 'uses'. If a formal internal structure in xml
format of a Kind instance is required, the uses dictionary matches with it in
a natural way, preserving the order in which kind-id's occur in the xml string.

Functionality for constructing the formal structure (i.e., the 'constr' and the
'type' attributes of a Kind instance) from xml form is also provided.

Classes:
    Kind(Term):                  abstract base class for the hierarchy of Type
                                 and Element subclasses
    Type(Kind):                  abstract base class for metadata subclasses
                                 that can be thought of as sets
    Element(Kind):               abstract base class for metadata subclasses
                                 that can be thought of as functions 
    ObjectType(Type):            metadata class representing a set of entities
                                 of statistical interest. Examples: 'person'
                                 (a set of persons), 'household' (a set of
                                 households), 'business' (a set of businesses)
    Phenomenon(Type):            metadata class representing a set of similar,
                                 but abstract, observations of statistical
                                 interest; abstract in the sense that these
                                 observations come without data. Examples:
                                 'economic activity', 'duration', 'well-being'
    ObjectTypeRelation(Element): metadata class representing a functional
                                 relationship between two object types.
                                 Examples: 'member of' (between a 'person' and
                                 a 'household'), 'has father' (between a
                                 'person' and a 'person')
    Variable(Element):           metadata class representing a set of
                                 (abstract) measurements on entities from an
                                 object type, that take their abstract
                                 observations, or their values, from a
                                 phenomenon (including subslasses), a measure
                                 (including subclasses), or a representation.
                                 Examples: 'main economic activity of a
                                 business', 'age of a person', 'well-being of a
                                 person'
    DatasetDesign(Element):      metadata class representing an ordered list of
                                 variables that are 'connected through a common
                                 object type'. Examples: 'age and income of a
                                 person', 'composition and income of a
                                 household'
    Quantity(Phenomenon):        a quantity in the scientific sense,
                                 irrespective of the unit of measure. Examples:
                                 'length', 'mass', 'energy'
    Measure(Type):               abstract metadata class for recording the way
                                 a variable is measured, given either by a unit
                                 of measure, a code list or a level
    Unit(Measure):               metadata class for supplementing a (n
                                 abstract) variable that has a quantity as a
                                 codomain, with a unit of measure. Examples:
                                 'meter', 'microgram', 'joule'
    CodeList(Measure):           metadata class for supplementing a (n
                                 abstract) variable that has an arbitrary
                                 phenomenon as a codomain, with a finite set of
                                 categories, which act as the 'observables' for
                                 the variable: the values that the variable can
                                 take. Examples: 'combination of NACE level 1
                                 and level 2', 'the 'male', 'female' and
                                 'total' categories'
    Level(CodeList):             metadata class for recording a special kind of
                                 code list: categories in a level must be
                                 mutually disjoint. Examples: 'Nace level 2',
                                 'the 'male and 'female' categories'
    Representation(Type):        metadata class for recording technical aspects
                                 of observed data, such as the format of the
                                 data, or the data type. Examples: 'yyyymmdd',
                                 '32 bits integer'
    ObjectTypeInclusion
        (ObjectTypeRelation):    represents the inclusion of one object type
                                 into another. Examples: 'male->person
                                 inclusion', 'financial business->business
                                 inclusion'
    DatasetDescription(Element): metadata class for recording information about
                                 a single data set. Examples: 'income and age
                                 of a person (Jan.1 2010, All working persons)'
    PhenomenonMeasureMapping
        (Element):               metadata element for associating a phenomenon
                                 with a measure: this expresses that the
                                 measure provides meaningful extra information
                                 to the phenomenon. Examples: 'length->meter
                                 mapping', 'economic activity->Nace level 1
                                 mapping'.
    MeasureRepresentationMapping
        (Element):               metadata element for associating a
                                 representation with a measure: this expresses
                                 that the measure can be meaningfully
                                 supplemented with information from the
                                 representation. Examples: 'date->yyyymmdd
                                 mapping', 'meter->32 bit integer mapping'
    Constant(Element):           expresses that a value has a certain type.
                                 Examples: 'August 5, 2010' (as a value of type
                                 'date'), '2040' (as a value of type 'euro')
    One(Type):                   singleton class, the only instance of which
                                 represents an arbitrary, but fixed, set with
                                 one member
    Operator(Element):           Not implemented yet

Exception classes:
    InvalidKind(Exception): instances of InvalidKind are raised when an attempt
                            is made to construct an invalid Kind instance. See
                            the __init__() member functions of the Type and
                            Element classes for the conditions under which an
                            InvalidKind instance is raised.

Module level instances:
    one (One): represents an arbitrary, but fixed, set with one member and is
               used, e.g., as the domain of a Constant

Note: use the kind Python module in combination with the term Python module.
See the code at the bottom of this module for code examples, or or execute
this code by importing the kind module in a Python console.

"""

from ..term.trm import Term, Application, functional_type, product
import xml.etree.ElementTree as ET
import uuid
import collections

class Kind(Term):
    """Abstract class for Types and Elements, itself derived from the Term
    class.

    Attributes:
        name (str):    the name of a Kind instance
        altname (str): an alternative name, e.g., a plural form
        article (str): either 'de' or 'het'
        kind (str):    equals either 'element' or 'type'
        sort (str):    the name of an actual (non abstract) Kind instance (like
                       'object type' or 'variable')
        type (Term):   the structure of the functional type of a Kind instance.
                       Equals 'None' if kind is 'type' and is optional if kind
                       is 'element'
        info (str):    additional information for a Kind instance
        constr (Term): the structure of a Kind instance; optional if the Kind
                       instance is elementary (e.g., an elementary 'object
                       type')
        id (str):      a UUID for a Kind instance
        uses (dict):   an ordered dictionary of (id (str), kind (Kind)) pairs
                       a Kind instance uses. Note that the uses dictionary can
                       be manually filled by calling the appenduse() member
                       function, or it can be filled automatically, as a side
                       effect of calling the getxml() member function. If
                       manually filled, the order of the (id, kind) pairs
                       follow the order in which the uses dictionary was
                       filled. If filled as side effect of getxml(), the order
                       of the uses dictionary follows the order of the id's
                       that occur in the xml.
    
    """
    def __init__(self, name, kindix, sortix, type=None, info=None, constr=None,
                 id=None, altname=None, article=None):
        """Construct a Kind instance and generate a UUID for the Kind instance,
        if none is given.

        Args:
            kindix (int): an index for the Term.kind list (see the Term class
                          documentation of the term module)
            sortix (int): an index for the Term.sort list (see the Term class
                          documentation of the term module)
        
        See the Kind class documentation for the meaning and types of the other
        arguments.

        """
        self.name = name
        self.info = info
        self.constr = constr
        self.uses = collections.OrderedDict()
        Term.__init__(self, Term.kind[kindix], Term.sort[sortix], type)
        if id == None:
            self.id = str(uuid.uuid1())
        else:
            self.id = id
        self.altname = altname
        self.article = article

    def appenduse(self, kind):
        """Add a Kind instance to the uses dictionary, if not already present.

        Args:
            kind (Kind): the Kind instance that is added to the dictionary.

        """
        if not kind.id in self.uses:
            self.uses[kind.id] = kind

    def more(self):
        """Return the name and the sort of a Kind instance, used for pretty
        printing.

        """
        return '%s : %s' % (self.name, self.sort)

    def __repr__(self):
        """Return the name of a Kind instance, used for printing.

        """
        return self.name

    def equals(self, term):
        """Return True if a Kind instance equals an arbitrary Term instance. To
        yield True, the Term instance must be an instance of a concrete class
        derived from the Kind class.

        Args:
            term (Term): The Term instance to test for equality with a Kind
                         instance.

        Note: equality is based on equality of the id's (as UUIDs) of the Kind
        instances.
        
        """
        if not term.__class__.__name__ in ['ObjectType', 'Phenomenon',
                                           'ObjectTypeRelation', 'Variable',
                                           'DatasetDesign', 'Quantity',
                                           'Measure', 'Unit', 'CodeList',
                                           'Level', 'Representation',
                                           'ObjectTypeInclusion',
                                           'DatasetDescription',
                                           'PhenomenonMeasureMapping',
                                           'MeasureRepresentationMapping',
                                           'Constant', 'One', 'Operator']:
            return False
        elif self.id != term.id:
            return False
        return True

    def getreturntype(self):
        """Return the type attribute of the Kind instance.

        Note: this method is inherited from the Term class.

        """
        return self.type

    def appendxml(self, elt, kind):
        """Append an xml element with tag name 'use' to a given xml element,
        that corresponds with the 'self' Kind instance: the id of the 'self'
        Kind instance is stored as an xml attribute.

        Note: a side effect of appendxml() is that to the uses dictionary of
        another given Kind instance, the 'self' Kind instance is added.

        Args:
            elt (xml.etree.ElementTree.Element): The xml element to which the
                                                 'use' xml element is added as
                                                 a child
            kind (Kind)                        : The kind instance that uses
                                                 'self' Kind instance

        """
        kindelement = ET.Element('use')
        kindelement.set('id', self.id)
        kind.appenduse(self)
        elt.append(kindelement)
        return

    def getxml(self):
        """Return the xml tree structure of 'self', recording an xml structure
        for its domain and codomain (if applicable), as well as an xml
        structure for its 'constr' attribute (if applicable).

        Note: a side effect of getxml() is that to the uses dictionary of
        'self', all other Kind instances found in the domain, codomain and
        constr, are added.

        """
        root = ET.Element('structure')
        root.set('kind', self.kind)
        tree = ET.ElementTree(root)
        if self.kind == 'element':
            if self.domain != None:
                domainelement = ET.Element('domain')
                root.append(domainelement)
                self.domain.appendxml(domainelement, self)
            if self.codomain != None:
                codomainelement = ET.Element('codomain')
                root.append(codomainelement)
                self.codomain.appendxml(codomainelement, self)
        if self.constr != None:
            constructionelement = ET.Element('construction')
            root.append(constructionelement)
            self.constr.appendxml(constructionelement, self)
        return tree

    def parsexml(self, root):
        """Reconstruct the self.constr and the self.type attributes from an xml
        structure rooted by 'root'.

        Note: parsexml() assumes that the self.uses dictionary of Kind
        instances is in correspondence with the xml elements tagged 'use' found
        in the xml structure. That is: the 'id' attributes of these xml
        elements should be keys in the dictionary. Calling parsexml() should
        therefore be done after calling getxml(), which also fills the uses
        dictionary appropriately. It is also assumed that the xml structure
        rooted by 'root' has been created before, using getxml(). Unexpected
        xml elements in the structure will therefore return an (unknown) error.

        Args:
            root (ET.Element): the root element of the xml structure
            
        """
        if root.get('kind') == 'element':
            domainelement = root.find('domain')
            codomainelement = root.find('codomain')
        constructionelement = root.find('construction')
        if constructionelement != None:
            self.constr = Term.parsexml(constructionelement[0], self.uses)
            if root.get('kind') == 'element':
                self.type = self.constr.type
                self.domain = self.type.args[0]
                self.codomain = self.type.args[1]
        else:
            if domainelement != None:
                self.domain = Term.parsexml(domainelement[0], self.uses)
            if codomainelement != None:
                self.codomain = Term.parsexml(codomainelement[0], self.uses)
            if domainelement != None and codomainelement != None:
                self.type = Application(functional_type,
                                        [self.domain, self.codomain])
        return

class Type(Kind):
    """Abstract subclass of the Kind class.

    Attributes:
        kind (str):  always yields 'type'
        type (Term): always yields None
    
    See the Kind class documentation for the description of other attributes.

    """
    def __init__(self, name, sortix, info=None, constr=None, id=None, altname=None, article=None):
        """Construct a Type instance.

        If the constr argument does not represent a Type, an InvalidKind
        exception is raised. A UUID id for the Type is generated, if none is
        given as an argument.

        Args:
            sortix (int): an index for the Term.sort list (see the Term class
                          documentation)
        
        See the Kind class documentation for the meaning and types of the other
        arguments.

        """
        # check if construction corresponds with a type
        if constr != None and constr.kind == 'element':
            raise InvalidKind(self)
        Kind.__init__(self, name, 0, sortix, None, info, constr, id, altname, article)

    def more(self):
        """Return the name and the sort of a Type instance, used for pretty
        printing.

        """
        return '{%s}' % (Kind.more(self))

class Element(Kind):
    """Abstract subclass of the Kind class.

    Attributes:
        kind (str):      always yields 'element'
        domain (Term):   the term that represents the domain of an Element
                         instance
        codomain (Term): the term that represents the codomain of an Element
                         instance
        type (Term):     the functional type of an Element instance
    
    See the Kind class documentation for the description of other attributes.

    """
    def __init__(self, name, sortix, domain=None, codomain=None, info=None,
                 constr=None, id=None, altname=None, article=None):
        """Construct an Element instance.

        If constr is passed as an argument, then the domain and codomain
        attributes of an Element instance are derived and possible domain
        and codomain arguments are ignored. Without a constr argument,
        __init__() copies the domain and codomain arguments as Element
        instance attributes. It is also possible to construct an Element
        instance without either domain, codomain or constr arguments, or with
        just a domain or codomain argument.
        
        If provided, domain and codomain must both represent a 'type',
        otherwise an InvalidKind exception is raised. Also, the constr
        attribute (if provided) must correspond with an 'element', otherwise an
        InvalidKind exception is raised.
        
        A UUID id for the Element is generated, if none is given as an
        argument. A functional type (i.e., a value for the attribute 'type') is
        constructed, either from the domain-codomain pair (if present) or from
        the constr argument (if provided).

        Args:
            sortix (int): an index for the Term.sort list (see the Term class
                          documentation of the term module)
        
        See the Kind class documentation for the meaning and types of the other
        arguments.

        """
        # check if domain and codomain are types
        if (domain != None and domain.kind == 'element') or (codomain != None
        and codomain.kind == 'element'):
            raise InvalidKind(Term.sort[sortix])
        # check if construction corresponds with an element
        if constr != None and constr.kind == 'type':
            raise InvalidKind(Term.sort[sortix])
        self.domain = domain
        self.codomain = codomain
        type = None
        if constr != None:
            type = constr.getreturntype()
            self.domain = type.args[0]
            self.codomain = type.args[1]
        elif domain != None and codomain != None:
            type = Application(functional_type, [domain, codomain])
        Kind.__init__(self, name, 1, sortix, type, info, constr, id, altname, article)

    def more(self):
        """Return the name of an Element instance, and the names of its domain
        and codomain, for pretty printing purposes.

        """
        domainstr = '.'
        codomainstr = '.'
        if self.domain != None:
            domainstr = self.domain.more()
        if self.codomain != None:
            codomainstr = self.codomain.more()
        return '%s ---%s--> %s' % (domainstr, Kind.more(self),
                                   codomainstr)

class InvalidKind(Exception):
    """Exception class, instances of which are raised when trying to construct
    an invalid Type or an invalid Element.

    Attributes:
        sort (str): the sort of invalid Type or Element that is tried to
                    construct.
        
    """
    
    def __init__(self, sort):
        """Construct an InvalidKind instance and record the sort of Type or
        Element that is invalid.

        Args:
            sort (str): the sort of invalid Type or Element that has been tried
                        to construct.
        """
        self.sort = sort

    def __str__(self):
        """Return the text dispayed in a Python interpreter, when an instance
        of InvalidKind is raised.

        """
        return 'Invalid construction of element or type: %s' % (self.sort)

class ObjectType(Type):
    """Concrete subclass of the Type class.

    Attributes:
        sort (str): always yields 'object type'
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, info=None, constr=None, id=None, altname=None):
        """Construct an ObjectType instance.

        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        Type.__init__(self, name, 0, info, constr, id, altname)
        
class Phenomenon(Type):
    """Concrete subclass of the Type class.

    Attributes:
        sort (str): always yields 'phenomenon'
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, sortix=1, info=None, constr=None, id=None):
        """Construct a Phenomenon instance.

        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        Type.__init__(self, name, sortix, info, constr, id)

class ObjectTypeRelation(Element):
    """Concrete subclass of the Element class.

    Attributes:
        sort (str):      always yields 'object type relation'
        domain (Term):   should be of sort 'object type'
        codomain (Term): should be of sort 'object type'
    
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, sortix=2, domain=None, codomain=None, info=None,
                 constr=None, id=None):
        """Construct an ObjectTypeRelation instance.

        Args:
            domain (Term):   should be of sort 'object type' (not checked)
            codomain (Term): should be of sort 'object type' (not checked)

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        Element.__init__(self, name, sortix, domain, codomain, info,
                         constr, id)

class Variable(Element):
    """Concrete subclass of the Element class.

    Attributes:
        sort (str):      always yields 'variable'
        domain (Term):   should be of sort 'object type'
        codomain (Term): should be of sort 'phenomenon', 'measure', 'unit (of
                         measure)', 'level', 'code list' or 'representation'
                         (not checked)
    
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, domain=None, codomain=None, info=None,
                 constr=None, id=None, article=None):
        """Construct a Variable instance.

        Args:
            domain (Term):   should be of sort 'object type' (not checked)
            codomain (Term): should be of sort 'phenomenon', 'measure', 'unit
                             (of measure)', 'level', 'code list' or
                             'representation' (not checked)

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        Element.__init__(self, name, 3, domain, codomain, info, constr, id, None, article)

class DatasetDesign(Element):
    """Concrete subclass of the Element class.

    A DatasetDesign instance is preferably constructed by providing a 'constr'
    argument, instead of providing domain and codomain arguments.

    Attributes:
        sort (str):      always yields 'data set design'
        domain (Term):   should be of sort 'object type'
        codomain (Term): should not neccessarily have a sort
    
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, domain=None, codomain=None, info=None,
                 constr=None, id=None):
        """Construct a DatasetDesign instance, preferably from a construction.

        A DatasetDesign instance is preferably constructed by providing a
        'constr' argument, instead of providing 'domain' and 'codomain'
        arguments.

        Args:
            domain (Term):   should be of sort 'object type' (not checked), but
                             is preferably not included as an argument
            codomain (Term): should not neccessarily have a sort (not checked),
                             but is preferably not included as an argument
            constr (Term):   the construction of a dataset design from its
                             variables

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        Element.__init__(self, name, 4, domain, codomain, info, constr, id)

class Quantity(Phenomenon):
    """Concrete subclass of the Phenomenon class.

    Attributes:
        sort (str): always yields 'quantity'
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """
     
    def __init__(self, name, info=None, constr=None, id=None):
        """Construct a Quantity instance.

        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        Phenomenon.__init__(self, name, 5, info, constr, id)

class Measure(Type):
    """Concrete subclass of the Type class.

    Attributes:
        sort (str): always yields 'measure'
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, sortix=6, info=None, constr=None, id=None):
        """Construct a Measure instance.

        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        Type.__init__(self, name, sortix, info, constr, id)

class Unit(Measure):
    """Concrete subclass of the Measure class.

    Attributes:
        sort (str): always yields 'unit (of measure)'
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, sortix=7, info=None, constr=None, id=None):
        """Construct a Unit instance.

        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        Measure.__init__(self, name, sortix, info, constr, id)

class CodeList(Measure):
    """Concrete subclass of the Measure class.

    Attributes:
        sort (str):        always yields 'code list'
        categories (list): the list of Categories the CodeList consists of
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """

    def __init__(self, name, categories=[], sortix=8, info=None, constr=None,
                 id=None):
        """Construct a Codelist instance.

        Arguments:
            categories (list): a list of Category instances the CodeList
            contains

        See the Kind and Type class documentation for the description of other
        arguments.
        
        """
        Measure.__init__(self, name, sortix, info, constr, id)
        self.categories = categories

class Level(CodeList):
    """Concrete subclass of the CodeList class.

    Attributes:
        sort (str):        always yields 'level'
        categories (list): the list of Categories the Level consists of
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """

    def __init__(self, name, categories=[], info=None, constr=None, id=None):
        """Construct a Level instance.

        Arguments:
            categories (list): a list of Category instances the CodeList
                               contains
                               
        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        CodeList.__init__(self, name, categories, 9, info, constr, id)

    def equalspan(self, other):
        """Decide whether or not a Level instance has a 'span' equal to that of
        another Level instance.

        Note: two Levels instances have equal 'span', when the unions of the
        sets of atoms each Category in the Level is buit up from, are equal.

        """
        selfatoms = []
        otheratoms = []
        for cat in self.categories:
            if len(cat.atoms) == 0:
                selfatoms.append(cat)
            else:
                selfatoms.extend(cat.atoms)
        for cat in other.categories:
            if len(cat.atoms) == 0:
                otheratoms.append(cat)
            else:
                otheratoms.extend(cat.atoms)
        selfatoms.sort()
        otheratoms.sort()
        return selfatoms == otheratoms

    def lessthanorequalto(self, other):
        """Decide whether or not a Level is less than or equal to another.

        Note: the less-than-or-equal-to relation is derived from the includes
        relation on Categories: if every Category in the first Level in included
        in some Category in the second, the less-than-or-equal-to relation
        holds.

        """
        for cat1 in self.categories:
            found = False
            for cat2 in other.categories:
                if cat2.includes(cat1):
                    found = True
                    break
            if not found:
                return False
        return True

class Representation(Type):
    """Concrete subclass of the Type class.

    Attributes:
        sort (str): always yields 'representation'
    
    See the Kind and Type class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, info=None, constr=None, id=None):
        """Construct a Representation instance.

        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        Type.__init__(self, name, 10, info, constr, id)

class ObjectTypeInclusion(ObjectTypeRelation):
    """Concrete subclass of the ObjectTypeRelation class, preferably from a
    construction.

    An ObjectTypeInclusion instance is preferably constructed by providing a
    'constr' argument with an application of an inclusion operation, instead of
    providing 'domain' and 'codomain' arguments.

    Attributes:
        sort (str):      always yields 'object type inclusion' (not checked)
        domain (Term):   should be of sort 'object type' (not checked)
        codomain (Term): should be of sort 'object type' (not checked)
    
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, domain=None, codomain=None, info=None,
                 constr=None, id=None):
        """Construct an ObjectTypeInclusion instance, preferably from a
        construction.

        An ObjectTypeInclusion instance is preferably constructed by providing
        a 'constr' argument with an application of an inclusion operation,
        instead of providing 'domain' and 'codomain' arguments.

        Args:
            domain (Term):   should be of sort 'object type' (not checked),
                             but is preferably not included as an argument
            codomain (Term): should be of sort 'object type' (not checked), but
                             is preferably not included as an argument
            constr (Term):   the construction of an object type inclusion,
                             preferably by an application of the inclusion
                             operation

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        ObjectTypeRelation.__init__(self, name, 11, domain, codomain, info,
                                    constr, id)

class DatasetDescription(Element):
    """Concrete subclass of the Element class, preferably from a construction.

    An DatasetDescription instance is preferably constructed by providing a
    'constr' argument with an appropriate application of the composition
    operation with a DatasetDesign, instead of providing 'domain' and
    'codomain' arguments.

    Attributes:
        sort (str):      always yields 'dataset description'
        domain (Term):   should be of sort 'object type' (not checked)
        codomain (Term): should not necessarily have a sort
    
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, domain=None, codomain=None, info=None,
                 constr=None, id=None):
        """Construct a DatasetDescription instance, preferably from a
        construction.

        A DatasetDescription instance is preferably constructed by providing a
        'constr' argument, instead of providing 'domain' and 'codomain'
        arguments.

        Args:
            domain (Term):   should be of sort 'object type' (not checked),
                             but is preferably not included as an argument
            codomain (Term): should not neccessarily have a sort (not checked),
                             but is preferably not included as an argument
            constr (Term):   the construction of a dataset description from a
                             dataset design

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        Element.__init__(self, name, 12, domain, codomain, info, constr, id)

class PhenomenonMeasureMapping(Element):
    """Concrete subclass of the Element class.

    Attributes:
        sort (str):      always yields 'phenomenon-measure mapping'
        domain (Term):   should be of sort 'phenomenon' or 'quantity' (not
                         checked)
        codomain (Term): should be of sort 'measure', 'unit (of measure)',
                         'code list' or 'level'
                        
    
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, domain=None, codomain=None, info=None,
                 constr=None, id=None):
        """Construct a PhenomenonMeasureMapping instance.

        Args:
            domain (Term):   should be of sort 'phenomenon' or 'quantity'
                             (not checked)
            codomain (Term): should be of sort 'measure', 'unit (of measure)',
                             'code list' or 'level' (not checked)

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        Element.__init__(self, name, 13, domain, codomain, info, constr, id)

class MeasureRepresentationMapping(Element):
    """Concrete subclass of the Element class.

    Attributes:
        sort (str):      always yields 'measure-representation mapping'
        domain (Term):   should be of sort 'measure', 'unit (of measure)',
                         'code list' or 'level' (not checked)
        codomain (Term): should be of sort 'representation' (not checked)
                        
    
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    def __init__(self, name, domain=None, codomain=None, info=None,
                 constr=None, id=None):
        """Construct a MeasureRepresentationMapping instance.

        Args:
            domain (Term):   should be of sort 'measure', 'unit (of measure)',
                             'code list' or 'level' (not checked)
            codomain (Term): should be of sort 'representation' (not checked)

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        Element.__init__(self, name, 14, domain, codomain, info, constr, id)
        

class Constant(Element):
    """Concrete subclass of the Element class.

    Attributes:
        sort (str):      always yields 'constant'
        domain (Term):   always yields the singleton instance 'one' of the
                         class One
        codomain (Term): should be of sort 'phenomenon', 'quantity', 'measure',
                         'unit (of measure)', 'code list', 'level', or
                         'representation' (not checked)
                         
    See the Kind and Element class documentation for the description of other
    attributes.

    """
    
    def __init__(self, name, codomain, info=None, constr=None, id=None, code=None):
        """Construct a Constant instance.

        Args:
            codomain (Term): should be of sort 'phenomenon', 'quantity',
                             'measure', 'unit (of measure)', 'code list',
                             'level', or 'representation' (not checked)
            code: an additional string that can serve as a code for the
                  constant.

        See the Kind and Element class documentation for the description of
        other arguments.
        
        """
        Element.__init__(self, name, 15, one, codomain, info, constr, id)
        self.code = code

class One(Type):
    """Concrete subclass of the Type class.

    Note: the class One should have one instance only, viz. the singleton
    instance 'one'. This instance is available through the kind module.

    Attributes:
        sort (str):      always yields 'one'
                        
    See the Kind and Element class documentation for the description of other
    attributes.

    """

    def __init__(self):
        """Construct a One instance.

        Note: the class One should have one instance only, viz. the singleton
        instance 'one'. This instance is available through the kind.py module.
        
        See the Kind and Type class documentation for the description of all
        arguments.
        
        """
        Type.__init__(self, '1', 16, 'A type with a single member',
                      constr=None, id=None)

class Operator(Element):
    def __init__(self, name, domain=None, codomain=None, info=None,
                 constr=None, id=None):
        Element.__init__(self, name, 21, domain, codomain, info, constr, id)

# Note: One is a singleton class
one = One()

if __name__ == '__main__':
    print("creating and printing object types, object type relations, " +
    "dataset designs, etc. and their info:")
    print("\n")
    person = ObjectType(name='person', info='A person like you and me')
    household = ObjectType(name='household',
                           info="A community in which a person lives, " +
                           "possibly together with other persons")
    livesin = ObjectTypeRelation(name='lives in',
                                 domain=person, codomain=household,
                                 info='The household a person is a member of')
    duration = Phenomenon(name='duration', info='A length of time')
    age = Variable(name='age', domain=person, codomain=duration,
                   info='The length of time since a person was born')
    amount = Phenomenon(name='amount', info='A quantity of money')
    income = Variable(name='income', domain=person, codomain=amount,
                      info='The amount of money a person earns in a year')
    dsdconstr = Application(product, [age, income])
    dsd = DatasetDesign(name='age and income', domain=None, codomain=None,
                        info='Ages and incomes of persons', constr=dsdconstr)
    const = Constant('minimum wage', amount,
    'The legal minimum amount of money a working person earns in a year', None)
    
    for obj in [person, household, livesin, duration, age,
                amount, income, const, dsd]:
        print(obj)
        print(obj.more())
        print(obj.info)
        print(obj.id)
        print("\n")

    print("the internal structure of the '%s' dataset design"  % (dsd.name))
    print("(printing 'constr' as well as pretty-printing 'constr'):")
    print(dsd.constr)
    print(dsd.constr.more())
    print("\n")
    print('code for a round trip of generating and parsing xml:')
    print("\n")
    print('    dsdxml = ET.tostring(dsd.getxml().getroot())')
    print('    dsd.constr = None')
    print('    dsd.type = None')
    print('    dsdroot = ET.XML(dsdxml)')
    print('    dsd.parsexml(dsdroot)')
    print('    print(dsd.constr)')
    print('    print(dsd.type)')
    print("\n")
    print('executing the above code yields:')
    dsdxml = ET.tostring(dsd.getxml().getroot())
    print(dsd.uses)
    dsd.constr = None
    dsd.type = None
    dsdroot = ET.XML(dsdxml)
    dsd.parsexml(dsdroot)
    print(dsd.constr)
    print(dsd.type)
    print("\n")
    print("the xml for the structure of the '%s' dataset design:" % (dsd.name))
    print(dsdxml)
    
    
    
    
