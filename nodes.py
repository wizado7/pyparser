from abc import ABC, abstractmethod
from typing import Tuple, Optional, Union, Callable
from enum import Enum

# Абстрактный базовый класс для всех узлов AST-дерева
class AstNode(ABC):
    def __init__(self, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__()
        self.row = row
        self.line = line
        for k, v in props.items():
            setattr(self, k, v)

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs_temp = self.childs
        for i, child in enumerate(childs_temp):
            if isinstance(child, AstNode):
                ch0, ch = '├', '│'
                if i == len(childs_temp) - 1:
                    ch0, ch = '└', ' '
                res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
            else:
                # Обработка строковых значений
                ch0 = '└' if i == len(childs_temp) - 1 else '├'
                res.append(f"{ch0} {str(child)}")
        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        for child in self.childs:
            if isinstance(child, AstNode):
                child.visit(func)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


# Узел для литералов (числа, строки, булевы значения)
class LiteralNode(AstNode):
    def __init__(self, literal: str, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.literal = literal
        self.value = eval(literal)

    def __str__(self) -> str:
        return '{0} ({1})'.format(self.literal, type(self.value).__name__)


# Узел для идентификаторов (имена переменных)
class IdentNode(AstNode):
    def __init__(self, name: str, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


# Узел для бинарных операций (+, -, *, /, и т.д.)
class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIVISION = '/'
    DIV = 'div'
    MOD = 'mod'
    GE = '>='
    LE = '<='
    NE = '<>'
    EQ = '='
    GT = '>'
    LT = '<'
    LOGICAL_AND = 'and'
    LOGICAL_OR = 'or'


class BinOpNode(AstNode):
    def __init__(self, op: BinOp, arg1: 'AstNode', arg2: 'AstNode', row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def childs(self) -> Tuple['AstNode', 'AstNode']:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


# Узел для списка идентификаторов (например, в объявлении переменных)
class IdentListNode(AstNode):
    def __init__(self, *idents: Tuple[IdentNode, ...], row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.idents = idents

    @property
    def childs(self) -> Tuple[IdentNode, ...]:
        return self.idents

    def __str__(self) -> str:
        return "idents"


# Узел для объявления переменных
class VarDeclNode(AstNode):
    def __init__(self, ident_list: IdentListNode, vars_type: 'AstNode', row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.ident_list = ident_list
        self.vars_type = vars_type

    @property
    def childs(self) -> Tuple[IdentListNode, 'AstNode']:
        return self.ident_list, self.vars_type

    def __str__(self) -> str:
        return 'var_dec'


# Узел для оператора присваивания
class AssignNode(AstNode):
    def __init__(self, var: Union[IdentNode, 'AstNode'], val: 'AstNode', row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var = var
        self.val = val

    @property
    def childs(self) -> Tuple[Union[IdentNode, 'AstNode'], 'AstNode']:
        return self.var, self.val

    def __str__(self) -> str:
        return ':='


# Узел для условного оператора if
class IfNode(AstNode):
    def __init__(self, cond: 'AstNode', then_stmt: 'AstNode', else_stmt: Optional['AstNode'] = None, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    @property
    def childs(self) -> Tuple['AstNode', 'AstNode', Optional['AstNode']]:
        return (self.cond, self.then_stmt) + ((self.else_stmt,) if self.else_stmt else tuple())

    def __str__(self) -> str:
        return 'if'


# Узел для цикла while
class WhileNode(AstNode):
    def __init__(self, cond: 'AstNode', stmt_list: 'AstNode', row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.stmt_list = stmt_list

    @property
    def childs(self) -> Tuple['AstNode', 'AstNode']:
        return self.cond, self.stmt_list

    def __str__(self) -> str:
        return 'while'


# Узел для списка операторов
class StmtListNode(AstNode):
    def __init__(self, *exprs: 'AstNode', row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.exprs = exprs

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


# Узел для программы
class ProgramNode(AstNode):
    def __init__(self, prog_name: IdentNode, vars_decl: 'AstNode', stmt_list: 'AstNode', row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.prog_name = prog_name
        self.vars_decl = vars_decl
        self.stmt_list = stmt_list

    @property
    def childs(self) -> Tuple[IdentNode, 'AstNode', 'AstNode']:
        return self.prog_name, self.vars_decl, self.stmt_list

    def __str__(self) -> str:
        return 'Program'