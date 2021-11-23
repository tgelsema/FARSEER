#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 07:55:59 2019

@author: tgelsema
@author: Guido van den Heuvel
"""
import re
from copy import copy, deepcopy

from farseer.term.trm import Application, composition, product, inclusion, inverse, alpha, projection
from farseer.kind.knd import Variable, ObjectTypeRelation, Constant, Operator, one, ObjectType

# global variable
table_num = 0

# Two constants that determine how aggressive query optimization is

# If FREEZE_ALL is True, all intermediate queries are frozen. This means
# that a new temporary table is generated for each operation.
# If FREEZE_ALL is False, queries remain unfrozen as long as is feasible.
# This tends to lead to fewer queries and therefore, likely faster execution. 
# Currently all aggregation subqueries are frozen, and all others aren't.
FREEZE_ALL = False    

# If DEDUP_FROZEN is False, frozen queries are not deduplicated. Duplicate
# frozen queries arise naturally when the same sub-expression is present
# multiple times.
# If DEDUP_FROZEN is True, identical frozen queries are deduplicated, which
# leads to faster execution times.
DEDUP_FROZEN = True

DIALECT_MYSQL = "MySQL"
DIALECT_SQLSERVER = "T-SQL"


# Perhaps Name should be derived from str(), given that it is for the most part identical
class Name:
    def __init__(self, name):
        self.name = f"{name}"

    def __bool__(self):
        return bool(repr(self))

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name

    def gen_sql(self, dialect):
        return self.name


class Alias:
    def __init__(self, alias):
        self.alias = Name(alias)
        
    def __repr__(self):
        return f" AS {self.alias}" if self.alias else ""
    
    def gen_sql(self, dialect):
        return f" AS {self.alias.gen_sql(dialect)}" if self.alias else ""


class TableAlias(Alias):
    def __init__(self, table, alias = ""):
        self.table = Name(table)
        Alias.__init__(self, alias)

    def get_alias(self):
        return repr(self.alias) if self.alias else repr(self.table)

    def replace_alias(self, table, alias):
        self.alias = Name(repr(self.alias).replace(repr(table), repr(alias), 1))

    def substitute_table(self, old, new):
        if self.table == old:
            self.table = new

    def __repr__(self):
        if not self.alias or repr(self.table) == repr(self.alias):
            return repr(self.table)
        return f"{self.table}" + Alias.__repr__(self) if self.table else ""

    def gen_sql(self, dialect):
        if not self.alias or self.table.gen_sql(dialect) == self.alias.gen_sql(dialect):
            return self.table.gen_sql(dialect)
        return f"{self.table.gen_sql(dialect)}" + Alias.gen_sql(self, dialect) if self.table else ""
    

class Column:
    def __init__(self, table, column):
        self.table = Name(table)
        self.column = Name(column)

    def replace_table(self, table, alias):
        self.table = Name(repr(self.table).replace(repr(table), repr(alias), 1))

    def substitute_table(self, old, new):
        if self.table == old:
            self.table = new

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __repr__(self):
        return f"{self.table}.{self.column}" if self.table else f"{self.column}"

    def gen_sql(self, dialect):
        return f"{self.table.gen_sql(dialect)}.{self.column.gen_sql(dialect)}" if self.table else f"{self.column.gen_sql(dialect)}"


class ColumnAlias(Column, Alias):
    def __init__(self, table, column, alias):
        Column.__init__(self, table, column)
        Alias.__init__(self, alias)

    def get_column(self):
        return Column(self.table, self.column)

    def __repr__(self):
        return Column.__repr__(self) + Alias.__repr__(self)

    def gen_sql(self, dialect):
        return Column.gen_sql(self, dialect) + Alias.gen_sql(self, dialect)


class ExpressionAlias(Alias):
    def __init__(self, args, alias = "", prefix = "", infix = ", "):
        super().__init__(alias)
        self.args = args
        self.prefix = prefix
        self.infix = infix

    def substitute_table(self, old, new):
        for arg in self.args:
            arg.substitute_table(old, new)

    def __repr__(self):
        if len(self.args) == 0:
            result = ""
        elif len(self.args) == 1 and self.prefix == "":
            result = repr(self.args[0]) + super().__repr__()
        else:
            # argstr = self.infix.join([ repr(a) for a in self.args ]) # tgelsema: an operator could translate to an expression
            argstr = self.infix % tuple([ repr(a) for a in self.args ])
            result = self.prefix + "(" + argstr + ")" + super().__repr__()
        return result

    def gen_sql(self, dialect):
        if len(self.args) == 0:
            result = ""
        elif len(self.args) == 1 and self.prefix == "":
            result = self.args[0].gen_sql(dialect) + super().gen_sql(dialect)
        else:
            # argstr = self.infix.join([ a.gen_sql(dialect) for a in self.args ]) # tgelsema: an operator could translate to an expression
            argstr = self.infix % tuple([ a.gen_sql(dialect) for a in self.args ])
            result = self.prefix + "(" + argstr + ")" + super().gen_sql(dialect)
        return result



class Cond:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
        
    def replace_tables(self, table, alias):
        self.lhs.replace_table(table, alias)
        self.rhs.replace_table(table, alias)

    def substitute_table(self, old, new):
        self.lhs.substitute_table(old, new)
        self.rhs.substitute_table(old, new)

    def is_trivially_true(self):
        return repr(self.lhs) == repr(self.rhs)

    def __repr__(self):
        return f'({self.lhs} = {self.rhs})'

    def gen_sql(self, dialect):
        return f'({self.lhs.gen_sql(dialect)} = {self.rhs.gen_sql(dialect)})'


# Note: for the moment, only JoinSpec makes use of CondList
# Potentially, the WHERE clause could also use this object
class CondList:
    def __init__(self):
        self.condlist = []

    def add_cond(self, lhs, rhs):
        new_cond = Cond(lhs, rhs)
        self.condlist.append(new_cond)
        return self

    def replace_tables(self, table, alias):
        for cond in self.condlist:
            cond.replace_tables(table, alias)

    def substitute_table(self, old, new):
        for cond in self.condlist:
            cond.substitute_table(old, new)

    def is_trivially_true(self):
        return all(cond.is_trivially_true() for cond in self.condlist)

    def __repr__(self):
        condlist_str = " AND ".join(repr(cond) for cond in self.condlist)
        return condlist_str

    def gen_sql(self, dialect):
        condlist_str = " AND ".join(cond.gen_sql(dialect) for cond in self.condlist)
        return condlist_str


# I'm not entirely happy with replace_alias(): it is meant to override both
# CondList.replace_tables() and TableAlias.replace_alias() but in the current
# implementation it does not. Reason for the discrepancy is that the column
# specifications in CondList use a table name which is, in fact, a table alias.
# I'll leave it as is for the moment, as the old CondAlias class, and the rest
# of the code, have the same design error.
#
# One fix of this issue could be to use class composition instead of inheritance,
# but I am not fully convinced that is the right choice in this case.
class JoinSpec(TableAlias, CondList):
    def __init__(self, table, alias, lhs = None, rhs = None):
        TableAlias.__init__(self, table, alias)
        CondList.__init__(self)
        if lhs is not None and rhs is not None:
            CondList.add_cond(self, lhs, rhs)

    def replace_alias(self, table, alias):
        CondList.replace_tables(self, table, alias)
        TableAlias.replace_alias(self, table, alias)

    def substitute_table(self, old, new):
        CondList.substitute_table(self, old, new)
        TableAlias.substitute_table(self, old, new)

    def __eq__(self, other):
        if self.table != other.table or len(self.condlist) != len(other.condlist):
            return False
        for selfcond, othercond in zip(self.condlist, other.condlist):
            if selfcond.lhs.column != othercond.lhs.column or repr(selfcond.rhs) != repr(othercond.rhs):
                return False
        return True

    def __repr__(self):
        # return f'({TableAlias.__repr__(self)}) ON {CondList.__repr__(self)}' # tgelsema: removed brackets below due to error in SQL Server
        return f'{TableAlias.__repr__(self)} ON {CondList.__repr__(self)}'

    def gen_sql(self, dialect):
        # return f'({TableAlias.gen_sql(self, dialect)}) ON {CondList.gen_sql(self, dialect)}' # tgelsema: removed brackets below due to error in SQL Server
        return f'{TableAlias.gen_sql(self, dialect)} ON {CondList.gen_sql(self, dialect)}'

# CondAlias does not support multiple column joins
# It is also badly named, as it is not an aliased condition, in the same way
# that ColumnAlias is an aliased column
class CondAlias(Cond, TableAlias):
    def __init__(self, table, alias, lhs, rhs):
        TableAlias.__init__(self, table, alias)
        Cond.__init__(self, lhs, rhs)

    def replace_alias(self, table, alias):
        Cond.replace_tables(self, table, alias)
        TableAlias.replace_alias(self, table, alias)

    def substitute_table(self, old, new):
        Cond.substitute_table(self, old, new)
        TableAlias.substitute_table(self, old, new)

    def __repr__(self):
        return f'({TableAlias.__repr__(self)}) ON {Cond.__repr__(self)}'

    def gen_sql(self, dialect):
        return f'({TableAlias.gen_sql(self, dialect)}) ON {Cond.gen_sql(self, dialect)}'


class QStruct:    
    def __init__(self, selectsdom, selectscod, frm, joins = None, wheres = None, groupbys = None, frozen_qsts = None, distinct = None, orderby = None, orderdir = ""):
        joins = [] if joins is None else joins
        wheres = [] if wheres is None else wheres
        groupbys = [] if groupbys is None else groupbys
        frozen_qsts = [] if frozen_qsts is None else frozen_qsts    
        distinct = False if distinct is None else distinct

        self.frozen_qsts = frozen_qsts
        self.selectsdom = selectsdom
        self.selectscod = selectscod
        self.frm = frm
        self.joins = []
        for j in joins:
            self.add_join(j)
        self.wheres = []
        for w in wheres:
            self.add_where(w)
        self.groupbys = groupbys
        self.distinct = distinct
        self.orderby = orderby
        self.orderdir = orderdir
        
    def add_join(self, new_join):
        if all(join != new_join for join in self.joins):
            self.joins.append(new_join)
        # for join in self.joins:
        #     if join == new_join:
        #         break
            # if join.table == new_join.table and join.lhs.column == new_join.lhs.column and repr(join.rhs) == repr(new_join.rhs):
            #     break
            # if repr(join) == repr(new_join):            # Code for new join already in existing joins
            #     break                                   # therefore the new join can be omitted
        # else:
        #     self.joins.append(new_join)

    def add_where(self, new_where):
        for where in self.wheres:
            if repr(where) == repr(new_where):
                break
        else:
            self.wheres.append(new_where)

    def freeze(self):
        global table_num

        tablename = f"tmp{table_num}"
        table_num += 1

        frozen_qst = copy(self)
        frozen_qst.tablename = Name(tablename)
        column_num = 0
        for s in frozen_qst.selectsdom + frozen_qst.selectscod:
            if not s.alias:
                s.alias = Name(f"col{column_num}")
            column_num += 1
        frozen_qst.frozen_qsts = []
        frozen_qst.orderby = None
        frozen_qst.orderdir = ""

        self.frozen_qsts.append(frozen_qst)
        self.frm = TableAlias(tablename)
        self.selectsdom = [ ColumnAlias(tablename, s.alias, "") for s in frozen_qst.selectsdom ]
        self.selectscod = [ ColumnAlias(tablename, s.alias, "") for s in frozen_qst.selectscod ]
        self.joins = []
        self.wheres = []
        self.groupbys = []
        
        return self

    def substitute_table(self, old_table, new_table):
        for s in self.selectsdom + self.selectscod:
            s.substitute_table(old_table, new_table)
        if self.frm.table == old_table:
            self.frm.table = new_table
        old_joins = self.joins
        self.joins = []
        for j in old_joins:
            j.substitute_table(old_table, new_table)
            # if j.table == old_table:
            #     j.table = new_table
            # if j.lhs.table == old_table:
            #     j.lhs.table = new_table
            # if j.rhs.table == old_table:
            #     j.rhs.table = new_table

            # add_join = True
            # for j2 in self.joins:
            #     if j.table == j2.table and j.lhs.column == j2.lhs.column and repr(j.rhs) == repr(j2.rhs):
            #         add_join = False
            #         break
            # if add_join and repr(j.lhs) != repr(j.rhs):
            if not j.is_trivially_true() and all(j != j2 and CondList.__repr__(j) != CondList.__repr__(j2) for j2 in self.joins):
                self.joins.append(j)
        for w in self.wheres:
            if w.lhs.table == old_table:
                w.lhs.table = new_table
            if w.rhs.table == old_table:
                w.rhs.table = new_table
        if isinstance(self.groupbys, list):
            for g in self.groupbys:
                if g.table == old_table:
                    g.table = new_table
            
    def dedup_frozen(self):
        if not DEDUP_FROZEN:
            return self

        old_qsts = self.frozen_qsts
        self.frozen_qsts = []
        queries = []
        for i, qst in enumerate(old_qsts):
            query = repr(qst)
            try:
                j = queries.index(query)
            except ValueError:        
                # Query is not on the list of queries yet, therefore we must keep it
                queries.append(query)
                self.frozen_qsts.append(qst)
                continue

            # Query is the same as some other one already in the list of queries. We therefore
            # don't need this query. We go through the remaining queries to rename all instances
            # of the new query's tablename to the existing query's one.
            cur_table = qst.tablename
            rep_table = old_qsts[j].tablename

            for qst in old_qsts[i+1:]:
                qst.substitute_table(cur_table, rep_table)
            self.substitute_table(cur_table, rep_table)
        return self


    def __repr__(self):
        sql = ""
        for frozen_qst in self.frozen_qsts:
            sql += f"CREATE TEMPORARY TABLE {frozen_qst.tablename}\n{frozen_qst}"

        colspec = ""
        for alias in self.selectsdom + self.selectscod:
            if colspec:
                colspec += ", "
            colspec += repr(alias)
        joinstr = ""
        for join in self.joins:
            joinstr += f"\nJOIN {join}"
        fromstr = f"\nFROM {self.frm}" if repr(self.frm) else ""
        wherestr = ""
        for where in self.wheres:
            wherestr += f" AND {where}" if wherestr else f"\nWHERE {where}"
        groupbystr = ""
        if isinstance(self.groupbys, list):
            for groupby in self.groupbys:
                groupbystr += f", {groupby}" if groupbystr else f"\nGROUP BY {groupby}"
        orderbystr = ""
        if self.orderby is not None:
            orderdir = "DESC" if self.orderdir == "desc" else "ASC"
            orderbystr = f"\nORDER BY {self.orderby} {orderdir} LIMIT 5"
        distinctstr = "DISTINCT " if self.distinct else ""

        sql += f"SELECT {distinctstr}{colspec}{fromstr}{joinstr}{wherestr}{groupbystr}{orderbystr}\n"

        return sql

    def gen_sql(self, dialect, create_table = False):
        sql = ""
        for frozen_qst in self.frozen_qsts:
            sql += frozen_qst.gen_sql(dialect, create_table = True)
            #sql += f"CREATE TEMPORARY TABLE {frozen_qst.tablename}\n{frozen_qst.gen_sql(dialect)}"

        create_str = ""
        into_str = ""
        if create_table:
            if dialect == DIALECT_MYSQL:
                create_str = f"CREATE TEMPORARY TABLE {self.tablename.gen_sql(dialect)}\n"
            else:
                into_str = f" INTO {self.tablename.gen_sql(dialect)}"
        colspec = ""
        for alias in self.selectsdom + self.selectscod:
            if colspec:
                colspec += ", "
            colspec += alias.gen_sql(dialect)
        joinstr = ""
        for join in self.joins:
            joinstr += f"\nJOIN {join.gen_sql(dialect)}"
        fromstr = f"\nFROM {self.frm.gen_sql(dialect)}" if self.frm.gen_sql(dialect) else ""
        wherestr = ""
        for where in self.wheres:
            wherestr += f" AND {where.gen_sql(dialect)}" if wherestr else f"\nWHERE {where.gen_sql(dialect)}"
        groupbystr = ""
        if isinstance(self.groupbys, list):
            for groupby in self.groupbys:
                groupbystr += f", {groupby.gen_sql(dialect)}" if groupbystr else f"\nGROUP BY {groupby.gen_sql(dialect)}"
        orderbystr = ""
        limitstr = ""
        topstr = "" 
        if self.orderby is not None:
            orderdir = "DESC" if self.orderdir == "desc" else "ASC"
            orderbystr = f"\nORDER BY {self.orderby} {orderdir}"
            if dialect == DIALECT_MYSQL:
                limitstr = " LIMIT 5"
            else:
                topstr = "TOP 5 "
        distinctstr = "DISTINCT " if self.distinct else ""

        # tgelsema added double newlines below
        sql += f"{create_str}SELECT {distinctstr}{topstr}{colspec}{into_str}{fromstr}{joinstr}{wherestr}{groupbystr}{orderbystr}{limitstr}\n\n"
        if dialect == DIALECT_SQLSERVER and not create_table:
            # Add a # to all references to temporary tables. Temporary tables have names "tmp<nr>", where <nr> consists of one or more decimal digits
            # Don't do this if create_table is True, for in that case it is a subquery, for which the # will be added at the end of main query generation
            sql = re.sub(r"(tmp[0-9]+)", r"#\1", sql)

        return sql

class QOperator:
    def __init__(self, prefix = "", infix = ""):
        self.prefix = prefix
        self.infix = infix

class QProjection:
    """
    class QProjection:
    
    contains the data necessary for the projection operator. Projection selects some of the 
    dimensions of the co-domain of a term with a multi-dimensional co-domain.
    """
    def __init__(self, dimensions, all_dimensions):
        self.dimensions = dimensions
        self.all_dimensions = all_dimensions


def freeze_qsts(qsts):

    for qst in qsts:
        if isinstance(qst, QStruct) and (FREEZE_ALL or qst.groupbys or qst.distinct):
            qst.freeze()

def cmpl(data, term, var = None, order = ""):
    global table_num

    table_num = 0
    return do_cmpl(data, term, var, order).dedup_frozen()

def do_cmpl(data, term, var, order):
    if isinstance(term, Application):
        if term.op == composition:
            return cmplcomposition(data, term.args, var, order)
        elif term.op == product:
            return cmplproduct(data, term.args, var, order)
        elif term.op == inclusion:
            return cmplinclusion(data, term.args, var, order)
        elif term.op == inverse:
            return cmplinverse(data, term.args, var, order)
        elif term.op == alpha:
            return cmplaggregation(data, term.args, var, order)
        elif term.op == projection:
            return cmplprojection(data, term.args, var, order)
    elif isinstance(term, Variable):
        return cmplvariable(data, term, var, order)
    elif isinstance(term, ObjectTypeRelation):
        return cmplobjecttyperelation(data, term, var, order)
    elif isinstance(term, Constant):
        return cmplconstant(data, term, var, order)
    elif isinstance(term, Operator):
        return cmploperator(data, term, var, order)


def cmplcomposition(data, args, var, order):
    qsts = []
    for arg in args:
        qsts.append(do_cmpl(data, arg, var, order))

    freeze_qsts(qsts)
    return do_composition(qsts)


def do_composition(qsts):
    """
    do_composition() performs n-ary composition as a recursive series of binary compositions.
    The n-ary composition A o B o C o D is evaluated as A o (B o (C o D)).
    """
    if len(qsts) == 1:
        return qsts[0]

    rhs = qsts.pop()
    lhs = qsts.pop()

    if isinstance(rhs, QProjection):
        new_qst = do_composition_rhs_projection(lhs, rhs)
    elif isinstance(lhs, QProjection):
        new_qst = do_composition_lhs_projection(lhs, rhs)
    elif isinstance(lhs, QOperator):
        new_qst = do_composition_operator(lhs, rhs)
    elif len(lhs.selectsdom) == 1:
        new_qst = do_composition_one_dim(lhs, rhs)
    else:
        new_qst = do_composition_multi_dim(lhs, rhs)

    qsts.append(new_qst)
    return do_composition(qsts)


def do_composition_lhs_projection(lhs, rhs):
    """
    This function handles composition of a projection operator with some expression.
    The effect of an lhs projection operator is to only keep those columns from the rhs codomain
    that are projected onto.
    """
    rhs.selectscod = [ rhs.selectscod[x] for x in lhs.dimensions ]
    if all(column.alias != Name("keyc") for column in rhs.selectscod): # tgelsema: note 'key' is a keyword in T-SQL
        # This should only occur if rhs.orderby was None already (and hence rhs is an unordered query): 
        # we assume that an ordered query isn't ordered with regards to a dimension that is deleted by a projection.
        rhs.orderby = None
        rhs.orderdir = ""
    
    return rhs


def do_composition_rhs_projection(lhs, rhs):
    """
    This function handles composition of some expression with a projection operator.
    The effect of an rhs projection operator is to add dummy columns to the lhs domain.

    We assume that the list of columns projected onto does not contain duplicates
    """
    new_selectsdom = [ None ] * len(rhs.all_dimensions)
    for i, dimension in enumerate(rhs.dimensions):
        new_selectsdom[dimension] = lhs.selectsdom[i]
    lhs.selectsdom = new_selectsdom

    return lhs


def do_composition_operator(lhs, rhs):
    """
    This function handles composition between a binary operator and a list of its arguments
    
    We assume that the operator is ascending as a function of its first operand, and descending
    with respect to its second operand. The only operator currently in use, division of two numbers, 
    satisfies this assumption.
    """
    alias = ""
    args = deepcopy(rhs.selectscod) 
    
    # Set the sort order of the result of the operation according to the sort orders specified for its operands
    if rhs.orderby is not None:
        if args[0].column == Name("keyc") or args[0].alias == Name("keyc"):
            alias = Name("keyc")
            args[0].alias = ""
        elif args[1].column == Name("keyc") or args[1].alias == Name("keyc"):
            alias = Name("keyc")
            args[1].alias = ""
            rhs.orderdir = "desc" if rhs.orderdir == "asc" else "asc" # Reverse sort order

    # Replace the operands with the result of the operation
    rhs.selectscod = [ ExpressionAlias(args, alias = alias, prefix = lhs.prefix, infix = lhs.infix) ]
    return rhs


def do_composition_one_dim(lhs, rhs):
    """
    Do composition of two ordinary (non-projection, non-operator) expressions where the domain of the lhs and the
    codomain of the rhs are both one dimensional.
    """
    selectsdom = rhs.selectsdom
    selectscod = lhs.selectscod
    frm = rhs.frm
    joins = rhs.joins
    wheres = lhs.wheres + rhs.wheres

    if lhs.frm.table: # If there is no lhs table, lhs is an immediate value, for which no joins are necessary or possible
        joinfrm = lhs.frm 
        joincod = rhs.selectscod[0].get_column()
        joindom = lhs.selectsdom[0].get_column()
        if joincod == joindom:
            # Trivial join, for which no new alias is to be generated.
            # Note that trivial joins are eliminated later on, during code generation
            alias = Name(f"{joincod.table}")
        else:
            if f"{joinfrm.table}"[0:3] == "tmp":
                # Don't do aliasing on tmp tables
                alias = joinfrm.table
                joinfrm.alias = ""
            else:
                # Generate new table alias
                alias = Name(f"{joincod.table}_{joincod.column}")
                joinfrm.alias = alias
                joindom.table = alias

            joins.append(JoinSpec(joinfrm.table, joinfrm.alias, joindom, joincod))

        for j in lhs.joins:
            j.replace_alias(joinfrm.table, alias)
            joins.append(j)

        for c in selectscod:
            c.replace_table(joinfrm.table, alias)

    frozen_qsts = [ f for q in [ rhs, lhs ] for f in q.frozen_qsts ]

    # Note: only one of lhs.orderby or rhs.orderby should ever be in use
    orderby = lhs.orderby if lhs.orderby else rhs.orderby
    orderdir = lhs.orderdir if lhs.orderby else rhs.orderdir

    return QStruct(selectsdom, selectscod, frm, joins, wheres, [], frozen_qsts, None, orderby, orderdir)


def do_composition_multi_dim(lhs, rhs):
    """
    Perform composition of two expressions, where the codomain of the rhs and the domain of the lhs
    are multi-dimensional. Rather than doing a complicated join of joins (which would require in-depth
    analysis if this is even possible in the SQL dialects in use and some rewriting of the underlying 
    JoinSpec class to accomodate this) we simply freeze both queries and do a multi-column join on the
    resulting temporary tables.

    TODO: See if it is possible to do this without freezing the queries. If this is possible, it should
          also be possible to see one dimensional composition as a special case of this, in which case 
          this function can be combined with do_composition_one_dim()
    """
    lhs.freeze()
    rhs.freeze()

    selectsdom = rhs.selectsdom
    selectscod = lhs.selectscod
    frm = rhs.frm
    wheres = [] # We know that newly frozen queries do not have wheres (any where clauses have been executed as part of temp table creation)
    joins = [] # We know that newly frozen queries do not have joins (any join clauses have been executed as part of temp table creation)

    joinfrm = lhs.frm
    joinspec = JoinSpec(joinfrm.table, "")
    for dom, cod in zip(lhs.selectsdom, rhs.selectscod):
        joindom = dom.get_column()
        joincod = cod.get_column()
        joinspec.add_cond(joindom, joincod)
    joins.append(joinspec)

    frozen_qsts = [ f for q in [ rhs, lhs ] for f in q.frozen_qsts ] # This includes the newly frozen lhs and rhs

    # Note: only one of lhs.orderby or rhs.orderby should ever be in use
    orderby = lhs.orderby if lhs.orderby else rhs.orderby
    orderdir = lhs.orderdir if lhs.orderby else rhs.orderdir

    return QStruct(selectsdom, selectscod, frm, joins, wheres, [], frozen_qsts, None, orderby, orderdir)


def cmplproduct(data, args, var, order):
    qsts = []
    for arg in args:
        qsts.append(do_cmpl(data, arg, var, order))

    if isinstance(qsts[0], QProjection):
        dimensions = []
        all_dimensions = qsts[0].all_dimensions
        for qst in qsts:
            if not isinstance(qst, QProjection):
                raise SyntaxError("Product contains mixture of projections and other stuff")
            dimensions += qst.dimensions
        
        return QProjection(dimensions, all_dimensions)

    freeze_qsts(qsts)

    selectsdom = qsts[0].selectsdom
    joins = []

    # Is the following necessary? 
    # domain of all product operands must be the same, can we then conclude that table is also the same?
    # If this is the case, this for loop is not necessary
    # Edit: No we cannot. One table or both can be frozen queries, in which case table names are different
    newjoins = {}
    for qst in qsts[1:]:
        for qdim, dim in zip(qst.selectsdom, selectsdom):
            if qdim is not None and dim is not None and qdim.table != dim.table:
                newjoins[qdim.table] = newjoins.get(qdim.table, JoinSpec(qdim.table, "")).add_cond(dim.get_column(), qdim.get_column())
                #joins.append(JoinSpec(qdim.table, "", dim.get_column(), qdim.get_column()))
    joins = list(newjoins.values())
    selectscod = [s for q in qsts for s in q.selectscod ]
    frm = qsts[0].frm
    joins += [ j for q in qsts for j in q.joins ]
    wheres = [ w for q in qsts for w in q.wheres ]
    groupbys = qsts[0].groupbys
    frozen_qsts = [ f for q in qsts for f in q.frozen_qsts ]
    orderby = None
    orderdir = ""
    for qst in qsts:
        if qst.orderby is not None:
            orderby = qst.orderby
            orderdir = qst.orderdir

    qst = QStruct(selectsdom, selectscod, frm, joins, wheres, groupbys, frozen_qsts, None, orderby, orderdir)
    return qst

def cmplinclusion(data, args, var, order):
    qsts = []
    for arg in args:
        qsts.append(do_cmpl(data, arg, var, order))

    freeze_qsts(qsts)

    selectsdom = qsts[0].selectsdom
    joins = []
    for qst in qsts[1:]:
        if qst.selectsdom[0].table != selectsdom[0].table:
            joins.append(JoinSpec(qst.selectsdom[0].table, "", selectsdom[0].get_column(), qst.selectsdom[0].get_column()))
    selectscod = deepcopy(selectsdom)
    frm = qsts[0].frm
    joins += [ j for q in qsts for j in q.joins]
    wheres = qsts[0].wheres     # Gather wheres from inclusions within inclusions.
                                # If arguments contain wheres, they should be the same for all arguments, 
                                # since the domain of every argument must be the same. Hence it is sufficient
                                # to only gather the wheres from the 1st argument.
    for i, q in enumerate(qsts):
        if i % 2 == 0: # LHS of comparison
            lhs = q.selectscod
        else:
            rhs = q.selectscod
            for l, r in zip(lhs, rhs):  # We can assume the input is well-formed, and hence lhs and rhs have the same length
                wheres.append(Cond(l, r))
    frozen_qsts = [ f for q in qsts for f in q.frozen_qsts ]
    qst = QStruct(selectsdom, selectscod, frm, joins, wheres, [], frozen_qsts)
    return qst

def cmplinverse(data, args, var, order):
    qsts = []
    for arg in args:
        qsts.append(do_cmpl(data, arg, var, order))

    freeze_qsts(qsts)

    selectsdom = deepcopy(qsts[0].selectscod)
    selectscod = deepcopy(qsts[0].selectscod)
    frm = qsts[0].frm
    joins = qsts[0].joins
    wheres = qsts[0].wheres
    frozen_qsts = [ f for q in qsts for f in q.frozen_qsts ]
    orderby = qsts[0].orderby
    orderdir = qsts[0].orderdir

    qst = QStruct(selectsdom, selectscod, frm, joins, wheres, [], frozen_qsts, True, orderby, orderdir)
    return qst

def cmplaggregation(data, args, var, order):
    qsts = []
    for arg in args:
        qsts.append(do_cmpl(data, arg, var, order))

    freeze_qsts(qsts)

    selectsdom = qsts[1].selectscod
    joins = []

    if qsts[0].selectsdom[0].table and qsts[1].selectsdom[0].table and qsts[0].selectsdom[0].table != qsts[1].selectsdom[0].table:
        joins.append(JoinSpec(qsts[0].selectsdom[0].table, "", qsts[0].selectsdom[0].get_column(), qsts[1].selectsdom[0].get_column()))
    selectscod = []
    for s in qsts[0].selectscod:
        # selectscod.append(ExpressionAlias([s.get_column()], alias = s.alias, infix = "", prefix = "SUM")) # tgelsema: needed another mechanism to form expressions
        selectscod.append(ExpressionAlias([s.get_column()], alias = s.alias, infix = "%s", prefix = "SUM"))
    frm = qsts[1].frm
    joins += [ j for j in qsts[0].joins + qsts[1].joins ]
    wheres = [ w for w in qsts[0].wheres + qsts[1].wheres ]
    groupbys = [ s.get_column() for s in selectsdom if s.table ]
    if not groupbys:
         groupbys = True
    frozen_qsts = [ f for q in qsts for f in q.frozen_qsts ]
    qst = QStruct(selectsdom, selectscod, frm, joins, wheres, groupbys, frozen_qsts, False, qsts[0].orderby, qsts[0].orderdir)
    return qst

def count_args(arg):
    if hasattr(arg, "args"):
        n = 0
        for arg in arg.args:
            n += count_args(arg)
        return n
    else:
        return 1

def cmplprojection(data, args, var, order):
    """ The projection operator has as input n arguments. The last argument is a number n
        while the other arguments are terms. The projection operator selects the nth term
        from the list of terms. The parameter n is between 1 and the number of terms, inclusive
        
        Terms can be products of terms, and those have to be expanded first. The reason for this
        is that in cases such as that the projection operator works on a product of products, and while
        <<A, B>, C> is different from <A, B, C> in the intermediate language, both give the same
        QStruct. Projecting <<A,B>,C> to its first dimension means that <A,B> is kept; hence
        this leads to a QProjection that projects to the first two dimensions of <A,B,C>
        """
    cur_dim = 0
    for i, arg in enumerate(args[:-1]):
        argsize = count_args(arg)
        next_dim = cur_dim + argsize
        if i == args[-1] - 1:
            proj_list = list(range(cur_dim, next_dim))
        cur_dim = next_dim

    return QProjection(proj_list, cur_dim)

def cmploperator(data, term, var, order):
    if term.name == "(/)":
        # qop = QOperator(infix = " / ") # tgelsema: a/b returns an integer when a and b are both integers in T-SQL
        qop = QOperator(infix = "(1.0 * %s) / %s")
        return qop
    
def findtable(data, term_name):
    for d in data:
        if foundsome(term_name, d.constr):
            return d
    return None
        
def foundsome(subterm_name, term):
    if term.__class__.__name__ == 'Application':
        for arg in term.args:
            if foundsome(subterm_name, arg):
                return True
    elif term.__class__.__name__ == 'Variable' or term.__class__.__name__ == "Constant" or term.__class__.__name__ == "ObjectTypeRelation":
        if term.name == subterm_name:
            return True
    return False
    
def cmplobjecttyperelation(data, term, var, order):
    name = re.sub(' ', '_', term.name)
    table = findtable(data, name)
    frm = TableAlias(table)
    selectsdom = [ ColumnAlias(frm.get_alias(), f"{table}_id", "") ]
    selectscod = [ ColumnAlias(frm.get_alias(), f"{name}", "") ]
    qst = QStruct(selectsdom, selectscod, frm, [], [])
    return qst

def cmplvariable(data, term, var, order):
    # if term.codomain == one or term.name[:3] == "een": # tgelsema: more instances of 'one' cause confusion and errors - cheap fix
    if term.codomain.name == "1" or term.name[:3] == "een":
        return cmplimmediate(data, term, var, order)

    # Code below copied from cmplobjecttyperelation() and adapted
    table = findtable(data, term.name)
    name = re.sub(' ', '_', term.name)
    frm = TableAlias(table)
    selectsdom = [ ColumnAlias(frm.get_alias(), f"{table}_id", "") ]
    selectscod = [ ColumnAlias(frm.get_alias(), f"{name}", "") ]
    orderby = None
    if var is not None and var.equals(term):
        orderby = Name("keyc")
        selectscod[0].alias = Name("keyc")
    qst = QStruct(selectsdom, selectscod, frm, None, None, None, None, None, orderby, order)
    return qst

def cmplimmediate(data, term, var, order):
    # if term.codomain == one: # tgelsema: more instances of 'one' cause confusion and errors - cheap fix
    if term.codomain.name == "1":
        imm = "'*'"
    elif term.name[:3] == "een":
        imm = "1"
    # tgelsema: domain.name need not correspond to a table. If not: ignore
    selectsdom = [] # tgelsema added this line
    frm = None # tgelsema added this line
    if isinstance(term.domain, ObjectType): # tgelsema added this line
        table = term.domain.name
        frm = TableAlias(table) 
        selectsdom = [ ColumnAlias(frm.get_alias(), f"{table}_id", "") ]
    selectscod = [ ColumnAlias("", f"{imm}", "") ]
    orderby = None
    if var is not None and var.equals(term):
        orderby = Name("keyc")
        selectscod[0].alias = Name("keyc")
    qst = QStruct(selectsdom, selectscod, frm, None, None, None, None, None, orderby, order)
    return qst

def cmplconstant(data, term, var, order):
    # name = re.sub(" ", "_", term.name) # tgelsema: rather use 'code' with constants
    print("term:", term)
    name = re.sub(" ", "_", term.code)
    selectsdom = [ ColumnAlias("", f"'*'", "") ]
    selectscod = [ ColumnAlias("", f"'{name}'", "") ]
    qst = QStruct(selectsdom, selectscod, TableAlias(""), [], [])
    return qst

if __name__ == '__main__':
    #testTableAlias()
    #testColumn()
    #quit()
    # create = Name('tmp_persoon')
    # selectsdom = [Alias('baan_werknemer.persoon_id', 'baan_werknemer.persoon_id')]
    # selectscod = [Alias('baan_werknemer.naam', 'baan_werknemer.naam')]
    # frm = Alias('baan', 'baan')
    # print(frm)
    # joins = [CondAlias('persoon', 'baan_werknemer', 'baan_werknemer.persoon_id', 'baan.werknemer')]
    # wheres = [Cond('baan_werknemer.woont_in', 'Amsterdam'), Cond('baan.functie', 'tandarts')]
    # groupbys = []
    # orderbys = []
    # #qst = QStruct(create, selectsdom, selectscod, frm, joins, wheres, groupbys, orderbys)
    # qst = QStruct(selectsdom, selectscod, frm, joins, wheres)
    # print(qst)
    # print(wheres)
    # print(joins)
    # q = cmplobjecttyperelation(woontop)
    # r = cmplobjecttyperelation(ligtin)
    pass