__package__ = 'farseer.term'

"""The term Python module exposes a number of classes and functions that can be
used in the creation of a term, from Kind instances (see the kind Python
module) and Gap instaces (these act as 'variables' in a Term) and from the
Application of an Operation to a list of other Term instances. In this way, a
Term instance can be built up from other Term instances recursively.

The term module also exposes concrete Operation classes, and instances of these
classes. Only the latter should be used, since concrete Operation classes
should be treated as singleton classes: they have one instance only. The term
Python module also exposes these instances.

Each of the concrete classes derived from Operation represents an operation,
that can be applied (through an Application) to a number of arguments. Concrete
Operations can be split into two: those that, in an Application, return a Term
that is a 'type' (Selection, CartesianProduct and FunctionalType) and those
that return an 'element' (Composition, Product, Inclusion).

Functionality is added to each concrete Operation class for checking whether or
not an Application of an Operation instance to a number of Term instances is
valid or not.

Functionality is added to each concrete Operation class for returning a return
type, if the operation returns an element: the return type is then the
functional type of the element (i.e., its 'domain' and 'codomain' can be
inspected from the functional type).

Functionality for translating a Term instance to some form of xml is also
provided, as well as the opposite: the creation of a Term from an appropriate
xml structure.

Classes:
    Term:               abstract base class for a Term instance
    Gap(Term):          concrete class for constructing a 'hole' in a term
    Application(Term):  concrete class for constructing the Application of an
                        Operation to a list of Term instances

    Operation:                   abstract base class for concrete Operation
                                 classes
    Composition(Operation):      class representing functional composition
    Product(Operation):          class representing functional product
    CartesianProduct(Operation): class representing the Cartesian product of
                                 sets
    Inclusion(Operation):        class representing the construction of an
                                 inclusion function
    Selection(Operation):        class representing the construction of a
                                 subset from a given set
    FunctionalType(Operation):   class representing the construction of a set
                                 of functions, of given domain and codomain
    Alpha(Operation):            class representing the aggregation of a
                                 function relative to another function
    Inverse(Operation):          class representing the inclusion of a
                                 function's range in it's codomain
    Range(Operation):            class representing the range of a function
                        
Exception classes:
    InvalidTerm(Exception):        instances of InvalidTerm are raised when an
                                   attempt is made to construct an invalid Term
                                   instance. See the documentation of the
                                   __init__() member function of the Term class
                                   for the conditions under which an
                                   InvalidTerm exception is raised.
    InvalidGap(Exception)          instances of InvalidGap are raised when an
                                   attempt is made to construct an invalid Gap
                                   instance. See the documentation of the
                                   __init__() member function of the Gap class
                                   for the conditions under which an InvalidGap
                                   exception is raised.
    InvalidApplication(Exception): instances of InvalidApplication are raised
                                   when an attempt is made to construct an
                                   invalid Application instance, i.e., an
                                   instance in which the Operation does not
                                   match a given list of Term instances. See
                                   the documentation of the
                                   checkapplicationconstraints() methods of
                                   the Operation subclasses in the operation
                                   Python module for the conditions under which
                                   an InvalidApplication exception is raised.

Module level functions:
    equals(term1 (Term), term2 (Term)): a test for equality between two Term
    instances

Module level instances:
    composition (Composition):            THE composition operation
    product (Product):                    THE product operation
    cartesian_product (CartesianProduct): THE Cartesian product operation
    inclusion (Inclusion):                THE inclusion operation
    selection (Selection):                THE selection operation
    functional_type (FunctionalType):     THE functional type operation
    alpha(Alpha):			            THE alpha operation
    inverse(Inverse):                     THE inverse operation
    range(Range):                         THE range operation

Note: use the term Python module in combination with the kind Python module.
See the code at the bottom of this module for example term definitions, or
execute this code by importing the term module in a Python console.

"""

from functools import reduce
import xml.etree.ElementTree as ET
import uuid

class Term:
    """Abstract class for the Kind (Types and Elements), Gap, and Application
    classes.

    A Term instance is either a Kind instance, a Gap instance or an Application
    instance. A Gap instance acts as a 'hole' in a Term. An an Application
    instance must be used (recursively) to build larger Terms from smaller
    ones.

    A Term instance always reflects either the structure of a 'type' (i.e., the
    way the 'type' is build from other 'types' or 'elements') or the structure
    of an 'element' (i.e., the way the 'element' is built from other 'elements'
    or 'types') . In the latter case, the 'element' is associated with a
    functional type, which is the Application of the functional type operator
    to the 'domain' and 'codomain' of the element.
    
    The use of an Application is bound by certain rules; in fact, some of these
    rules constitute a type system for Term instances, in case these instances
    reflect 'elements'. Hence, for instance, an Application of the composition
    operator to a number of 'elements' is allowed only if these elements form a
    'path', where the 'codomain' of an element equals the 'domain' of the next
    (see the documentation of the Operator class).

    Attributes:
        kind (str):  equals either 'element' or 'type'
        sort (str):  the name of an actual (non abstract) Kind instance (like
                     'object type' or 'variable') or a Gap instance. Equals
                     'None' if the Term instance is an Application instance.
        type (Term): the structure of the type of a Kind, Application or Gap
                     instance. Equals 'None' if kind is 'type' and is optional
                     if kind is 'element'

    Class level attributes:
        kind (list): the list ['type', 'element']
        sort (list): the list containing all valid sorts, i.e., ['object type',
                     'phenomenon', ...]

    Class level methods:
        parsexml(root (ET.Element), uses (dict)): create a Term instance from
        the root of an xml structure

    """
    kind = ['type', 'element', 'kind']
    sort = ['object type', 'phenomenon', 'object type relation',
            'variable', 'dataset design', 'quantity', 'measure',
            'unit (of measure)', 'code list', 'level', 'representation',
            'object type inclusion', 'dataset description',
            'phenomenon-measure mapping', 'measure-representation mapping',
            'constant', 'one', 'value', 'category', 'classification',
            'hierarchy', 'operator', 'unspecified element', 'unspecified type']
    
    def __init__(self, kind, sort=None, type=None):
        """Construct a Term instance.

        Args:
            See the Term class documentation for the meaning and types of the
            arguments of __init__()

        In the following cases an InvalidTerm is raised:
              - if sort and kind don't match (e.g., if sort eqals 'object type'
                and kind equals 'element')
              - if kind equals 'type' and type does not equal 'None'
              - if type.kind equals 'element'
              
        """
        if (sort == 'object type' or sort == 'phenomenon' or sort == 'quantity'
            or sort == 'measure' or sort == 'unit (of measure)'
            or sort == 'code list' or sort == 'level'
            or sort == 'representation'
            or sort == 'one') and kind == 'element':
            raise InvalidTerm(kind)
        if (sort == 'object type relation' or sort == 'variable'
            or sort == 'dataset design' or sort == 'object type inclusion'
            or sort == 'dataset description'
            or sort == 'phenomenon-measure mapping'
            or sort == 'measure-representation mapping'
            or sort == 'constant' or sort == 'operator') and kind == 'type':
            raise InvalidTerm(kind)
        if type != None and kind == 'type':
            raise InvalidTerm(kind)
        if type != None and type.kind == 'element':
            raise InvalidTerm(kind)
        self.kind = kind
        self.sort = sort
        self.type = type

    @classmethod
    def parsexml(cls, root, uses):
        """Return a Term instance created from the root of an xml structure.

        Note: parsexml() dispatches the parsing of the xml structure given by
              root and the creation of a Term instance to parsexml() of the Gap
              and Application classes.
              
        Note: parsexml() assumes that the uses dictionary of Kind instances is
              in correspondence with the xml elements tagged 'use' found in the
              xml structure. That is: the 'id' attributes of these xml elements
              should be keys in the dictionary.

        Args:
            root (ET.Element): the xml element of the root of the xml structure
            uses (dict)      : a dictionary of (id (uuid.UUID), kind (Kind))
                               pairs the xml structure refers to through xml
                               elements tagged 'use'
                               
        """
        if root.tag == 'application':
            return Application.parsexml(root, uses)
        if root.tag == 'gap':
            return Gap.parsexml(root, uses)
        if root.tag == 'use':
            return uses[root.get('id')]

def equals(term1, term2):
    """Return True if term1 equals term2, False otherwise.

    Args:
        term1 (Term): the 'left' argument in the equality test
        term2 (Term): the 'right' argument in the equality test

    """
    return term1.equals(term2)

class Gap(Term):
    """Concrete class for a Term that represents a 'gap': a 'hole' in a Term.

    Attributes:
        name (str): the symbol reresenting the Gap instance, like 'x' or 'y'
        id (str):   a UUID for the Gap instance
        
    See the Term class documentation for the meaning and types of other
    attributes.
    
    """

    def __init__(self, name, kindix, sortix=None, type=None, id=None):
        """Construct a Gap instance and generate a UUID for the Gap instance,
        if none is given.

        Note: an InvalidGap instance is raised if a Gap of kind 'element' is
        attempted to construct that has:
            - no type attribute provided, or
            - a type attribute provided that is not an Application of a
              functional type

            Args:
                name (str):   a name for the Gap instance, like 'x' or 'y'
                kindix (int): an index for the Term.kind list (see the Term
                              class documentation)
                sortix (int): an index for the Term.sort list (see the Term
                              class documentation)
                type (Term):  the functional type of a Gap instance, if the Gap
                              instance represents an 'element'
                id (str):     a UUID for the Gap instance
                
        """
        self.name = name
        sort = None
        if sortix != None:
            sort = Term.sort[sortix]
        if kindix == 1:
            if type == None:
                raise InvalidGap(name)
            elif type.__class__.__name__ != 'Application':
                raise InvalidGap(name)
            elif type.op.name != 'functional type':
                raise InvalidGap(name)
        Term.__init__(self, Term.kind[kindix], sort, type)
        if id == None:
            self.id = str(uuid.uuid1())
        else:
            self.id = id

    def equals(self, term):
        """Return True if a Gap instance equals a given Term instance, and
        False otherwise.

        Args:
            term (Term): the Term instance that is tested for equality with the
            Gap instance

        Note: it is required that the Term instance is a Gap instance itself.
        Note: equality is based on equality of id's (as UUIDs) of the Gap
        instances.

        """
        if term.__class__.__name__ != 'Gap':
            return False
        elif self.id != term.id:
            return False
        return True

    def getreturntype(self):
        """Return the functional type (an an Application) of a Gap instance, if
        the Gap instance represents an 'element', return 'None' otherwise.

        """
        return self.type

    def more(self):
        """Return the name of a Gap instance, or name and type, used for pretty
        printing.

        """
        if self.type != None:
            return '%s : %s' % (self.__repr__(), self.type.__repr__())
        else:
            return self.__repr__()
    
    def __repr__(self):
        """Return the name of a Gap instance, used for printing.

        """
        return self.name

    def appendxml(self, elt, kind):
        """Append an xml-element with tag name 'gap' to a given xml element,
        that corresponds with the 'self' Gap instance.

        The name, kind, sort and id of the 'self' Gap instance are stored as
        xml attributes. Also, if the Gap instance has a type (that does not
        equal 'None'), xml elements with tag names 'domain' and 'codomain' are
        created.

        Note: a side effect of appendxml() is that to the uses dictionary of
        another given Kind instance, other Kind instance can be added, in
        particular if they are encountered in the 'domain' and the 'codomain'
        (i.e., in the type of the Gap instance).

        Args:
            elt (xml.etree.ElementTree.Element): The xml element to which the
                                                 'gap' xml element (and
                                                 possibly 'domain' and
                                                 'codomain' xml elements) is
                                                 added as a child
            kind (Kind)                        : The kind instance that
                                                 possibly updates its uses
                                                 attribute in the process

        """
        gapelement = ET.Element('gap')
        gapelement.set('name', self.name)
        gapelement.set('kind', self.kind)
        gapelement.set('sort', self.sort)
        gapelement.set('id', self.id)
        if self.type != None:
            domainelement = ET.Element('domain')
            gapelement.append(domainelement)
            type.args[0].appendxml(domainelement, kind)
            codomainelement = ET.Element('codomain')
            gapelement.append(codomainelement)
            type.args[1].appendxml(codomainelement, kind)
        elt.append(gapelement)
        return

    @classmethod
    def parsexml(cls, root, uses):
        """Return a Gap instance created from the root of an xml structure.
              
        Note: parsexml() assumes that the uses dictionary of Kind instances is
        in correspondence with the xml elements tagged 'use' found in the xml
        structure. That is: the 'id' attributes of these xml elements should be
        keys in the dictionary.

        Args:
            root (ET.Element): the xml element of the root of the xml structure
            uses (dict)      : a dictionary of (id (uuid.UUID), kind (Kind))
                               pairs the xml structure refers to through xml
                               elements tagged 'use'
                               
        """
        type = None
        domainelement = root.find('domain')
        codomainelement = root.find('codomain')
        if not domainelement == None:
            domain = Term.parsexml(domainelement[0], uses)
            if not codomainelement == None:
                codomain = Term.parsexml(codomainelement[0], uses)
            type = Application(functional_type, [domain, codomain])
        return Gap(root.get('name'), root.get('kind'), root.get('sort'),
                   type, id)
        
class Application(Term):
    """Concrete class for a Term that represents an 'application': an operation
    applied to a number of arguments.

    Attributes:
        op (Operation): the Operation instance used in the Application instance
        args (list):    a list of Term instances that represent the arguments
                        for the Operation
        
    See the Term class documentation for the meaning and types of other
    attributes.
    
    """
    
    def __init__(self, op, args):
        """Construct an Application instance from an Operation instance and a
        list of Term instances.

        Args:
            op (Operation): the Operation instance used in the Application
                            instance
            args (list):    a list of Term instances that represent the
                            arguments for the Operation

        Note: an InvalidApplication is raised if the Operation instance does
        not correspond with the args argument. The exact conditions under which
        an InvalidApplication is raised depend on the specific Operation. For
        instance, if the Operation instance is an instance of Composition, it
        is checked whether or not the Term instances in the args list form a
        'path'. Further details are documented in the documentation of the
        checkapplicationconstraint() methods.
                
        """
        if op.checkapplicationconstraints(args):
            self.args = args
            self.op = op
            Term.__init__(self, op.kind, sort=None,
                          type=op.getreturntype(self.args))
        else:
            raise InvalidApplication(op, args)

    def equals(self, term):
        """Return True if an Application instance equals a given Term instance,
        and False otherwise.

        Args:
            term (Term): the Term instance that is tested for equality with the
            Gap instance

        Note: it is required that the Term instance is an Application instance
        itself.
        
        Note: equality is based on equality of the op attributes and the args
        attributes of the Application instances.

        """
        if term.__class__.__name__ != 'Application':
            return False
        elif self.op.name != term.op.name:
            return False
        elif len(self.args) != len(term.args):
            return False
        for i in range(len(term.args)):
            if isinstance(term.args[i], int):
                if not isinstance(self.args[i], int):
                    return False
                if term.args[i] != self.args[i]:
                    return False
            if isinstance(self.args[i], int):
                if not isinstance(term.args[i], int):
                    return False
            if isinstance(term.args[i], Term) and isinstance(self.args[i], Term) and not term.args[i].equals(self.args[i]):
                return False
        return True
        # return reduce((lambda x, y: x and y), list(map(equals, self, term)))

    def getreturntype(self):
        """Return the type of an Application instance, if the Application
        instance represents an 'element', and return 'None' otherwise.

        """
        return self.op.getreturntype(self.args)

    def __repr__(self):
        """Return a string representation (str) of an Application instance,
        used for printing both the op and the args attributes in a meaningful
        way.

        Note: both infix and prefix notations are supported. 

        """
        argstr = []
        i = 0
        for arg in self.args:
            argstr.append(arg.__repr__())
            if(self.op.symbol == ','):
                argstr.append('%s ' % self.op.symbol)
            elif self.op.name == 'inclusion' or self.op.name == 'selection':
                if i % 2 == 0:
                    argstr.append('=')
                else:
                    argstr.append(', ')
            elif self.op.name == 'aggregation' or self.op.name == 'projection':
                argstr.append(', ')
            else:
                argstr.append(' %s ' % self.op.symbol)
            i += 1
        argstr.pop()
        if self.op.notation == 'prefix':
            return '%s%s%s%s' % (self.op.symbol, self.op.leftparenthesis,
                                 reduce((lambda x, y: x+y), argstr),
                                    self.op.rightparenthesis)
        elif self.op.notation == 'infix':
            return '%s%s%s' % (self.op.leftparenthesis,
                               reduce((lambda x, y: x+y), argstr),
                                self.op.rightparenthesis)

    def more(self):
        """Return a string representation (str) of an Application instance,
        and its type (if present) used for pretty printing.

        Note: both infix and prefix notations are supported, both for the
        Application instance and its type (if applicable). 

        """
        if self.kind == 'type' or type == None:
            return self.__repr__()
        else:
            return '%s : %s' % (self.__repr__(), self.type.__repr__())

    def appendxml(self, elt, kind):
        """Append an xml element with tag name 'application' to a given xml
        element, that corresponds with the 'self' Application instance.

        The name of the operation attribute is stored as an xml attribute. All
        the Term instances in the args list are stored as child elements of xml
        element with 'application' tag.
        
        Note: a side effect of appendxml() is that to the uses dictionary of
        another given Kind instance, other Kind instance can be added, in
        particular if they are encountered in the args attribute.

        Args:
            elt (xml.etree.ElementTree.Element): The xml element to which the
                                                 'application' xml element is
                                                 added as a child
            kind (Kind)                        : The kind instance that
                                                 possibly updates its uses
                                                 attribute in the process

        """
        applicationelement = ET.Element('application')
        applicationelement.set('operation', self.op.name)
        for arg in self.args:
            arg.appendxml(applicationelement, kind)
        elt.append(applicationelement)
        return

    @classmethod
    def parsexml(cls, root, uses):
        """Return an Application instance created from the root of an xml
        structure.
              
        Note: parsexml() assumes that the uses dictionary of Kind instances is
        in correspondence with the xml elements tagged 'use' found in the xml
        structure. That is: the 'id' attributes of these xml elements should
        be keys in the dictionary.

        Args:
            root (ET.Element): the xml element of the root of the xml structure
            uses (dict)      : a dictionary of (id (uuid.UUID), kind (Kind))
                               pairs the xml structure refers to through xml
                               elements tagged 'use'
                               
        """
        args = []
        op = None
        if root.get('operation') == 'composition':
            op = composition
        elif root.get('operation') == 'product':
            op = product
        elif root.get('operation') == 'Cartesian product':
            op = cartesian_product
        elif root.get('operation') == 'inclusion':
            op = inclusion
        elif root.get('operation') == 'selection':
            op = selection
        elif root.get('operation') == 'functional type':
            op = functional_type
        elif root.get('operation') == 'aggregation':
            op = alpha
        for child in root:
            args.append(Term.parsexml(child, uses))
        return Application(op, args)

class InvalidGap(Exception):
    """Exception class, instances of which are raised when trying to construct
    a Gap instance of kind 'element' with no type argument that represents a
    functional type provided.

    Attribues:
        name (str) : the name of the Gap instance that was attempted to
                     construct

    """

    def __init__(self, name):
        """Constructs an InvalidGap instance and records the name of the Gap
        instance that was attempted to construct.

        Args:
            See the documentation of the InvalidGap class for the meaning of the
            argument.
        """
        self.name = name

    def __str__(self):
        """Return the text displayed in a Python module, when an instance of
        InvalidGap is raised.

        """
        return ("Invalid type argument in the construction of a gap of kind "
                "'element': %s" % (self.name))

class InvalidApplication(Exception):
    """Exception class, instances of which are raised when trying to construct
    an Application instance with non-matching Operation instance and args list.

    Note: see the documentation of the checkapplicationconstraints() methods in
    the operation classes for the conditions under which an InvalidApplication
    instance is raised.
    
    Attributes:
        op (Operation): the operation instance of the Application instance that
                        was attempted to construct
        args (list):    the argument list of Term instances of the Application
                        instance that was attempted to construct
                        
    """
    
    def __init__(self, op, args):
        """Constructs an InvalidApplication instance and record the Operation
        and args instances of the Application instance that was attempted to
        construct.

        Args:
            See the documentation of the InvalidApplication class for the
            meaning of the arguments.
        """
        self.op = op
        self.args = args
        
    def __str__(self):
        """Return the text displayed in a Python console, when an instance of
        InvalidApplication is raised.

        """
        return 'Invalid arguments in application of: %s' \
        'args: %s' % (self.op.name, self.args)

class InvalidTerm(Exception):
    """Exception class, instances of which are raised when trying to construct
    an invalid Term instance.

    Note: see the documentation of the __init__() method of the Term class for
    the conditions under which an InvalidTerm instance is raised.

    Attributes:
        kind (str): the kind ('element' or 'type') of the Term instance that
        was attempted to construct
    """
    
    def __init__(self, kind):
        """Constructs an InvalidTerm instance and record the kind of the Term
        instance that was attempted to construct.

        Args:
            See the documentation of the InvalidTerm class for the meaning of
            the argument.
        """
        self.kind = kind

    def __str__(self):
        """Return the text dispayed in a Python console, when an instance of
        InvalidTerm is raised.

        """
        return 'Invalid construction of term: %s' % (self.kind)


class Operation:
    """Abstract base class for defining (properties) of operations: Composition
    and CartesianProduct for example derive from this class.

    An Operation instance is used as an actual operation in an Application,
    thereby creating a Term from a number of smaller Terms. See the Application
    and Term class documentation.

    Note: the Operation class (and all derived classes) should be treated as
    singleton classes. At the bottom of this module, single instances of each
    class are defined and they (and only they) should be used in Applications.

    Attributes:
        name (str):             a name for the operation, like 'product' or
                                'composition'
        notation (str):         either 'prefix' or 'infix'. This determines how
                                an Application of the Operation will be printed
        kind (str):             either 'type' or 'element'. Represents the kind
                                of the return type for an Application of the
                                Operator
        symbol (str):           a symbol for the operation, used for pretty
                                printing an Application using the Operator
                                instance
        leftparenthesis (str):  a left parenthesis used for pretty printing an
                                Applcation using the Operator instance
        rightparenthesis (str): a right perentthesis used for pretty printing
                                an Application using the Operator instance

    Class level attributes:
        notation (list): the list ['prefix', 'infix']

    """
    notation = ['prefix', 'infix'] # postfix and mixfix are not supported yet
    
    def __init__(self, name, notationix, kindix, symbol=',',
                 leftparenthesis='(', rightparenthesis=')'):
        """Create an Operation instance.

        Note: by default, the Operation symbol equals ',' (a comma), the left
        parenthesis for the Operation instance equals '(' and its right
        parenthesis equals ')'.

        Args:
            notationix (int): an index for the Operation.notation list
            kindix     (int): an index for the Term.kind list
            
        """
        self.name = name
        self.notation = Operation.notation[notationix]
        self.kind = Term.kind[kindix]
        self.symbol = symbol
        self.leftparenthesis = leftparenthesis
        self.rightparenthesis = rightparenthesis

    def getreturntype(self, args):
        """Return the return type of an Operation instance, when applied to a
        number of arguments.

        Note: getreturntype() is only meaningful for Operation instances of
        kind 'element'. This abstract version of getreturntype() handles the
        cases in which the Operation instance is of kind 'type': in these
        cases, getreturntype() yields 'None'. For Operations of kind 'element',
        getreturntype() has special implementations.

        Args:
            args (list): a list of Term instances to apply the Operation
                         instance to
            
        """
        return None

class Projection(Operation):
    """Represents the projection Operation, which can be applied to two or
    more 'types', together with a number k that indexes the type projected to.
    It yields an 'element'.
    
    Note: k-th Projection shpuld be thought of as a function that, given n
    arguments, produces the k-th argument.
    
    Attributes:
        See the attributes of the Operation base class.
        
    """
    
    def __init__(self):
        """Construct a projection instance.
        
        Note: Projection has prefix notation. Its operation symbol should be a
        Greek pi symbol (symbol=u'\u03C0') if the Python console supports UTF
        printing. Left and right parentheses are the default ones.
        
        """
        Operation.__init__(self, 'projection', 0, 1, symbol='p') # symbol=u'\u03C0'
        
    def checkapplicationconstraints(self, args):
        """Check whether the constraints of a Projection instance, when
        applied to a number of Term arguments and a number k, hold or not.

        Note: a Projection Application should have at least three arguments of
        which all are types and the last argument a number. The number should
        be between 1 (inclusive) and the number of types given as arguments.

        Args:
            args (list): a list of Term instances plus a number that form the
            arguments for Projection.

        """
        if len(args) < 3:
            return False
        else:
            i = 0
            while i < len(args) - 1:
                if args[i].kind != 'type':
                    return False
                i += 1
            if not isinstance(args[len(args) - 1], int):
                return False
            if args[len(args) - 1] < 1 or args[len(args) - 1] > len(args) - 1:
                return False
        return True
    
    def getreturntype(self, args):
        """Return the return type, as a Term instance, of Projection when
        applied to a list of Term instances and a number.

        Note: the return type is the functional type which has as domain the
        Cartesian product of all its type arguments (except the last, which is
        an integer argument). It has as a codomain the (type of the) k-th
        argument.

        Args:
            args (list): a list of Term instances, all but the last should
            have kind 'type' (not checked). The last argument should be an
            integer (not checked)

        Use checkapplicationconstraints(args) before calling
        getreturntype(args).

        """
        newargs = []
        newargs.append(Application(cartesian_product, args[:-1]))
        newargs.append(args[args[len(args) - 1] - 1])
        type = Application(functional_type, newargs)
        return type

class Composition(Operation):
    """Represents the composition Operation, which can be applied to two or
    more 'elements'. It yields an 'element'.

    Note: Composition should be thought of as functional composition: the
    'functions' (or rather: 'elements') to which it is applied form a path in
    which the codomain of one 'function' equals the domain of the next. Note
    also that the path should be given in reverse order.

    Attributes:
        See the attributes of the Operation base class.
        
    Class level methods:
        consecutive(cls, arg1 (Term), arg2 (Term)): return the second argument
        if the domain of the first argument equals the codomain of the second
        argument, and return 'None' otherwise
        
    """
    
    def __init__(self):
        """Construct a Composition instance.

        Note: Composition has infix notation. Its operation symbol should be a
        little circle (symbol=u'\u2218') if the Python console supports UTF
        printing. Left and right parentheses are the default ones.
        
        """
        Operation.__init__(self, 'composition', 1, 1, symbol='o') # symbol=u'\u2218'

    @classmethod
    def consecutive(cls, arg1, arg2):
        """Return the second argument if the domain of the first argument
        equals the codomain of the second argument, and return 'None'
        otherwise.

        Args:
            arg1 (Term): the first argument, should have kind 'element'
                         (not checked)
            arg2 (Term): the second argument, should have kind 'element'
                         (not checked)
            
        """
        if arg1 != None and arg2 != None:
            if arg1.type.args[0].equals(arg2.type.args[1]):
                return arg2
        return None

    def checkapplicationconstraints(self, args):
        """Check whether the constraints of a Composition instance, when
        applied to a number of Term arguments, hold or not.

        Note: a Composition Application should have at least two arguments. All
        should be elements. They should form a path: the codomain of one equals
        the domain of the next. Note also that the path should be given in
        reverse order.

        Args:
            args (list): a list of Term instances that form the arguments for
                         Composition.

        """
        if len(args) < 2:
            return False
        else:
            for arg in args:
                if arg.kind != 'element':
                    return False
        return reduce(Composition.consecutive, args) != None
    
    def getreturntype(self, args):
        """Return the return type, as a Term instance, of Composition when
        applied to a list of Term instances.

        Note: the return type is the functional type which has as domain the
        domain of the last argument, and which has as codomain the codomain of
        the first argument. Note also that the arguments that form a path must
        be given in reverse order.

        Args:
            args (list): a list of Term instances, all should have kind
            'element' (not checked)

        Use checkapplicationconstraints(args) before calling
        getreturntype(args).

        """
        newargs = []
        newargs.append(args[len(args)-1].type.args[0])
        newargs.append(args[0].type.args[1])
        type = Application(functional_type, newargs)
        return type

class Product(Operation):
    """Represents the product Operation, which can be applied to two or more
    'elements'. It yields an 'element'.

    Note: Product should be thought of as functional product: the 'functions'
    (or rather: 'elements') to which it is applied should have a common domain. 

    Attributes:
        See the attributes of the Operation base class.
        
    """
    
    def __init__(self):
        """Construct a Product instance.

        Note: Product has infix notation. Its has the default operation symbol.
        Left and right parentheses look like '<' and '>' respectively. Use
        leftparenthesis=u'\u27E8' and rightparenthesis=u'\u27E9' if the Python
        interpreter supports UTF printing.
        
        """
        Operation.__init__(self, 'product', 1, 1, leftparenthesis='<',
                           rightparenthesis='>')

    def getreturntype(self, args):
        """Return the return type, as a Term instance, of Product when applied
        to a list of Term instances.

        Note: the return type is the functional type which has as domain the
        domain of either of the arguments (so pick the domain of the first),
        and which has as codomain the Cartesian product of the codomains of all
        the arguments.

        Args:
            args (list): a list of Term instances, all should have type
            'element' (not checked)

        Use checkapplicationconstraints(args) before calling
        getreturntype(args).

        """
        newargs1 = []
        newargs = []
        for arg in args:
            newargs1.append(arg.type.args[1])
        type1 = Application(cartesian_product, newargs1)
        newargs.append(args[0].type.args[0])
        newargs.append(type1)
        type = Application(functional_type, newargs)
        return type

    def checkapplicationconstraints(self, args):
        """Check whether the constraints of a Product instance, when applied to
        a number of Term arguments, hold or not.

        Note: a Product Application should have at least two arguments. All
        should be elements. Their domains should coincide.

        Args:
            args (list): a list of Term instances that form the arguments for
            Product.

        """
        if len(args) < 2:
            return False
        else:
            type = args[0].type.args[0]
            for arg in args:
                if arg.kind != 'element':
                    return False
                if not arg.type.args[0].equals(type):
                    return False
        return True

class CartesianProduct(Operation):
    """Represents the Cartesian product Operation, which can be applied to two
    or more 'types'. It yields a 'type'.

    Note: Cartesian product should be thought of as the Cartesian product
    applied to sets. 

    Attributes:
        See the attributes of the Operation base class.
        
    """
    
    def __init__(self):
        """Construct a Cartesian product instance.

        Note: Cartesian product has infix notation. Its operation symbol is
        like an 'x'. Use symbol=u'\u2A2F' if the Python console supports
        UTF printing. Left and right parentheses are the default ones.
        
        """
        Operation.__init__(self, 'Cartesian product', 1, 0, symbol='x')

    def checkapplicationconstraints(self, args):
        """Check whether the constraints of a Cartesian product instance, when
        applied to a number of Term arguments, hold or not.

        Note: a Cartesian product Application should have at least two
        arguments. All should be types.

        Args:
            args (list): a list of Term instances that form the arguments for
            the Cartesian product.

        """
        if len(args) < 2:
            return False
        else:
            for arg in args:
                if arg.kind != 'type':
                    return False
        return True

class Inclusion(Operation):
    """Represents the Inclusion Operation, which can be applied to two or more
    pairs of 'elements'. It yields an 'element'.

    Note: Inclusion yields an element, that should be thought of as the
    inclusion function between two sets, the one being included in the other.
    See Selection for the construction of this subset.

    Attributes:
        See the attributes of the Operation base class.
        
    """
    
    def __init__(self):
        """Construct an Inclusion Operation instance.

        Note: Inclusion has prefix notation. Its operation symbol should be the
        Greek symbol 'iota' (symbol=u'\u03B9') if the Python console supports
        UTF printing. Left and right parentheses are the default ones.
        
        """
        Operation.__init__(self, 'inclusion', 0, 1, symbol='i') # symbol=u'\u03B9'

    def getreturntype(self, args):
        """Return the return type, as a Term instance, of Inclusion when applied
        to a list of Term instances.

        Note: the return type is the functional type which has as domain the
        Selection applied to the same arguments, and which has as codomain the
        domain of any of the arguments (they all should have a common domain).

        Args:
            args (list): a list of Term instances, all should have type
            'element' (not checked)

        Use checkapplicationconstraints(args) before calling
        getreturntype(args).

        """
        newargs = []
        type1 = Application(selection, args)
        newargs.append(type1)
        newargs.append(args[0].type.args[0])
        type = Application(functional_type, newargs)
        return type

    def checkapplicationconstraints(self, args):
        """Check whether the constraints of an Inclusion instance, when applied
        to a number of Term arguments, hold or not.

        Note: Selection and Inclusion have the same constraints: an Inclusion
        Application should have at least two arguments and their total number
        should be even. All arguments should be elements. They should all have
        a common domain. Finally, each pair of consecutive arguments should
        have a common codomain.

        Args:
            args (list): a list of Term instances that form the arguments for
            the Inclusion.

        """
        return Inclusion.checkapplicationconstraints(args)
       
    @classmethod
    def checkapplicationconstraints(cls, args):
        """Check whether the constraints of an Inclusion, when applied to a
        number of Term arguments, hold or not.

        Note: Selection and Inclusion have the same constraints: an Inclusion
        Application should have at least two arguments and their total number
        should be even. All arguments should be elements. They should all have
        a common domain. Finally, each pair of consecutive arguments should
        have a common codomain. This method is also called by the
        checkapplicationconstraints() methods of an Inclusion and a Selection
        instance

        Args:
            args (list): a list of Term instances that form the arguments for
            the Inclusion.
        
        """
        if len(args) < 2:
            return False
        if len(args) % 2 != 0:
            return False
        else:
            type = args[0].type.args[0]
            for arg in args:
                if arg.kind != 'element':
                    return False
                if not arg.type.args[0].equals(type):
                    return False
            # consecutive elements should have common codomain
            for arg in args:
                if args.index(arg) % 2 == 0:
                    if not arg.type.args[1].equals(args[args.index(arg)+1].
                    type.args[1]):
                        return False
            return True

class Selection(Operation):
    """Represents the Selection Operation, which can be applied to two or more
    pairs of 'elements'. Its yields a 'type'.

    Note: Inclusion yields a type, that should be thought of as the subset of
    the domain of any of its arguments (they all should have a common domain).
    More specifically, it is the subset for which the first and second
    arguments, as a function, are equal, as well as the third and fourth
    argument, etc.

    Attributes:
        See the attributes of the Operation base class.
        
    """
    
    def __init__(self):
        """Construct a Selection Operation instance.

        Note: Selection has prefix notation. Its operation symbol should be the
        Greek symbol 'sigma' (symbol=u'\u03C3') if the Python console supports
        UTF printing. Left and right parentheses are the default ones.
        
        """
        Operation.__init__(self, 'selection', 0, 0, symbol='s') # symbol=u'\u03C3'

    def checkapplicationconstraints(self, args):
        """Check whether the constraints of a Selection instance, when applied
        to a number of Term arguments, hold or not.

        Note: Selection and Inclusion have the same constraints: a Selection
        Application should have at least two arguments and their total number
        should be even. All arguments should be elements. They should all have
        a common domain. Finally, each pair of consecutive arguments should
        have a common codomain.

        Args:
            args (list): a list of Term instances that form the arguments for
            the Selection.

        """
        return inclusion.checkapplicationconstraints(args)


class Inverse(Operation):
    """Represents the inclusion of an element's range in it's codomain
    
    Attributes:
        See the attributes of the Operation base class.
        
    """
    
    def __init__(self):
        """Construct an Inverse Operation instance.
        
        Note: Inverse has prefix notation. Its operation symbol should be the
        Greek symbol 'kappa' (symbol=u'\u03BA') if the Python console suppotrs
        UTF printing. Left and right parentheses are the default ones.
        
        """
        Operation.__init__(self, 'inverse', 0, 1, symbol='k') # symbol=u'\u03BA'
        
    def getreturntype(self, args):
        """Return te return type, as a Term instance, of Inverse when applied
        to a list of Term instances. Note: Inverse is a unary operator and
        expects one element only.
        
        Note: the return type is the functional type which has as domain the
        range of the argument of Inverse, and which has as a codomain the 
        codomain of the argument of Inverse.
        
        Args:
            args (list): a list of Term instance, which should contain exactly
            one 'element' (not checked)
            
        Use checkapplicationconstraints(args) before calling
        getreturntype(args).
        """
        newargs = []
        newargs.append(Application(rnge, args))
        newargs.append(args[0].type.args[1])
        type = Application(functional_type, newargs)
        return type
        
    def checkapplicationconstraints(self, args):
        """Check whether the constraints of an Inverse instance, when applied
        to a list of Term instances, hold or not.
        
        Inverse should receive exactly one 'element' Term instance.
        
        Args:
            args(list): a list of Term instances that form the arguments for
            the application of Inverse.
        """
        if len(args) != 1:
            return False
        if args[0].kind != 'element':
            return False
        return True

class Alpha(Operation):
    """Represents the Aggregation Operation, which is applied to two 'elements':
    it should be thought of as the aggregation of the first argument relative
    (grouped by) the second argument.

    Attributes:
        See the attributes of the Operation base class.

    """

    def __init__(self):
        """Construct an Alpha Operation instance.

        Note: Alpha has prefix notation. Its operation symbol should be the Greek
        symbol 'alpha' (symbol=u'\u03B1') if the Python console supports UTF printing.
        Left and right parentheses are the default ones.

        """
        Operation.__init__(self, 'aggregation', 0, 1, symbol='a') # symbol=u'\u03B1'


    def getreturntype(self, args):
        """Return the return type, as a Term instance, of Alpha when applied
        to a list of Term instances.

        Note: the return type is the functional type which has as domain the
        codomain of the second argument, and which has as codomain the
        codomain of the first argument (both arguments should have a common domain).

        Args:
            args (list): a list of Term instances, all should have type
            'element' (not checked)

        Use checkapplicationconstraints(args) before calling
        getreturntype(args).

        """
        newargs = []
        newargs.append(args[1].type.args[1])
        newargs.append(args[0].type.args[1])
        type = Application(functional_type, newargs)
        return type

    def checkapplicationconstraints(self, args):
        """Check whether the constraints of an Alpha instance, when applied to a
        number of Term arguments, hold or not.

        Alpha should receive two 'element' Term instances, which should have a
        common domain.

        Args:
            args (list): a list of Term instances that form the arguments for the
            application of Alpha.

        """
        if len(args) != 2:
            return False
        for arg in args:
            if arg.kind != 'element':
                return False
        if not args[0].type.args[0].equals(args[1].type.args[0]):
            return False
        return True
        
class Range(Operation):
    """Represents a set that is the range of its single argument. It yields a
    'type'.
    
    Attributes:
        See the attributes of the Operation base class.
    """
    
    def __init__(self):
        """Construct a Range Operation instance.
        
        Note: Range has infix notation. Its operation symbol should be the
        Graak symbol 'rho' (symbol=u'\u03C1') if the Python console supports
        UTF printing. Left and right parentheses are the default ones.
        """
        Operation.__init__(self, 'range', 0, 0, symbol='r') # symbol=u'\u03C1'
        
    def checkapplicationconstraints(self, args):
        """Check whether the constraints of a Range instance, when applied to
        a list of Term instances, hold or not.
        
        Note: Range should be given exactly one argument, which should be an
        'element'.
        
        Args:
            args(list): a list of Term instances that form the arguments for
            the Range Appication.
        """
        return inverse.checkapplicationconstraints(args)
        

class FunctionalType(Operation):
    """Represents a pair that can be thought of as the domain and codomain of
    an 'element'. It yields a 'type'.

    Note: FunctionalType yields a type that should be thought of as the set of
    functions with given domain and codomain.

    Attributes:
        See the attributes of the Operation base class.
        
    """
    
    def __init__(self):
        """Construct a FunctionalType Operation instance.

        Note: FunctionalType has infix notation. Its operation symbol should
        be a right arrow (symbol=u'\u2192') if the Python console supports UTF
        printing. Left and right parentheses are '[' and ']', respectively.
        
        """
        Operation.__init__(self, 'functional type', 1, 0, symbol='->',
                           leftparenthesis='[', rightparenthesis=']')

    def checkapplicationconstraints(self, args):
        """Check whether the constraints of a FunctionalType instance, when
        applied to a number of Term arguments, hold or not.

        Note: a FunctionalType Application should have exactly two arguments.
        Both must be types.

        Args:
            args (list): a list of Term instances that form the arguments for
            the FunctionalType Application.

        """
        if len(args) != 2:
            return False
        elif args[0].kind != 'type':
            return False
        elif args[1].kind != 'type':
            return False
        return True

# Note: these are instances of singleton classes
composition = Composition()
product = Product()
cartesian_product = CartesianProduct()
inclusion = Inclusion()
selection = Selection()
functional_type = FunctionalType()
alpha = Alpha()   
inverse = Inverse()
rnge = Range()
projection = Projection()               

if __name__ == '__main__':
    c = Gap('c', 0)
    d = Gap('d', 0)
    e = Gap('e', 0)
    f = Gap('f', 0)
    u = Gap('u', 1, type=Application(functional_type, [c, d]))
    x = Gap('x', 1, type=Application(functional_type, [c, d]))
    y = Gap('y', 1, type=Application(functional_type, [c, e]))
    z = Gap('z', 1, type=Application(functional_type, [e, f]))
    term1 = Application(product, [x, y])
    term2 = Application(composition, [z, y])
    term3 = Application(inclusion, [u, x])
    term4 = Application(inclusion, [u, u, u, u])
    term5 = Application(inverse, [u])
    for obj in [c, d, e, f, u, x, y, z, term1, term2, term3, term4, term5]:
        print(obj.more())

    print("\n")
    print(('for navigating the last term, the structure of its type, and the '
           "name of its domain's top-level operation, consider the following "
           'code:\n'))
    print('    print(term5.type.args[0].op.name)\n')
    print('executing this code yields:')
    print(term5.type.args[0].op.name)
    print('\n')
    print('relationship between projection and product:')
    term6 = Application(projection, [c, d, e, 1])
    term7 = Application(projection, [c, d, e, 2])
    term8 = Application(product, [term6, term7])
    for obj in [term6, term7, term8]:
        print(obj.more())
           
    

