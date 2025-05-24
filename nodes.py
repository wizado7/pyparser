from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Union
from enum import Enum
import inspect

# Абстрактный класс - узел AST-дерева
# Все рализованные далее классы узлов являются потомками этого класса
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
    def tree(self) -> list[str]:
        res = [str(self)]
        childs_temp = self.childs
        for i, child in enumerate(childs_temp):
            ch0, ch = '├', '│'
            if i == len(childs_temp) - 1:
                ch0, ch = '└', ' '
            # Проверяем, что child является AstNode, а не строкой
            if hasattr(child, 'tree'):
                res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
            else:
                # Если это строка, просто выводим её
                res.append((ch0 + ' ' + str(child)))
        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.childs)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class ExprNode(AstNode):
    pass

# Узел содержащий значение переменной и ее типа
class LiteralNode(ExprNode):
    def __init__(self, literal: str,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.literal = literal
        try:
            if literal.startswith("'") and literal.endswith("'"):
                self.value = literal[1:-1]  # Строка
            elif literal in ('True', 'False'):
                self.value = literal == 'True'  # Булево
            else:
                self.value = int(literal)  # Число
        except:
            self.value = literal

    def __str__(self) -> str:
        return '{0} ({1})'.format(self.literal, type(self.value).__name__)


# Узел содержащий название переменной
class IdentNode(ExprNode):
    # k,j..
    def __init__(self, name: str, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


# Узел содержащий элементы массива
class ArrayIdentNode(ExprNode):
    def __init__(self, name: IdentNode, literal: LiteralNode, row: Optional[int] = None, line: Optional[int] = None,
                 **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.literal = literal

    @property
    def childs(self) -> Tuple[IdentNode, LiteralNode]:
        return (self.name, self.literal)

    def __str__(self) -> str:
        return '{0} [{1}]'.format(self.name, self.literal)

# Перечисление содержащее символы для бинарных операций
class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIVISION = '/'
    DIV = 'div'
    MOD = 'mod'
    GE = '>='
    LE = '<='
    NEQUALS = '<>'
    EQUALS = '='
    GT = '>'
    LT = '<'
    LOGICAL_AND = 'and'
    LOGICAL_OR = 'or'

# Узел реализующий бинарную операцию
class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def childs(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class StmtNode(ExprNode):
    pass

# Узел содержащий список переменных определенного типа
class IdentListNode(StmtNode):
    def __init__(self, *idents: Tuple[IdentNode, ...], row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.idents = idents

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.idents

    def __str__(self) -> str:
        return "idents"

# Узел содержащий тип переменной или списка переменных
class TypeSpecNode(StmtNode):
    def __init__(self, name: str, row: Optional[int] = None, line: Optional[int] = None, **props):
        super(TypeSpecNode, self).__init__(row=row, line=line, **props)
        self.name = name

    def __str__(self) -> str:
        return self.name


class VarDeclNode(StmtNode):
    def __init__(self, ident_list: IdentListNode, vars_type: TypeSpecNode,  # *vars_list: Tuple[AstNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.ident_list = ident_list
        self.vars_type = vars_type

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return (self.ident_list,) + (self.vars_type,)

    def __str__(self) -> str:
        return 'var_dec'

# Узел реализующий объявление массива, переменную, размерность и тип
# name идентификатор массива
# from_ индекс первого элемента массива
# to_ индекс последнего элемента массива
# vars_type тип к которому относится массив
class ArrayDeclNode(StmtNode):
    def __init__(self, name: Tuple[AstNode, ...],
                 from_: LiteralNode, to_: LiteralNode, vars_type: TypeSpecNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.from_ = from_
        self.to_ = to_
        self.vars_type = vars_type

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        # return self.vars_type, (*self.vars_list)
        return (self.vars_type,) + (self.name,) + (self.from_,) + (self.to_,)

    def __str__(self) -> str:
        return 'arr_decl'

# Узел реализующий раздел описания переменных
class VarsDeclNode(StmtNode):
    def __init__(self, *var_decs: Tuple[VarDeclNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var_decs = var_decs

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.var_decs

    def __str__(self) -> str:
        return 'var'

# Узел реализующий вызов функций или процедур
class CallNode(StmtNode):
    def __init__(self, func: IdentNode, *params: Tuple[ExprNode],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.func = func
        self.params = params

    @property
    def childs(self) -> Tuple[IdentNode, ...]:
        # return self.func, (*self.params)
        return (self.func,) + self.params

    def __str__(self) -> str:
        return 'call'

# Узел реализующий операцию присваивания переменной var значения val
class AssignNode(StmtNode):
    def __init__(self, var,
                 val: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var = var
        self.val = val

    # def childs(self) -> Tuple[IdentNode, ExprNode]:
    @property
    def childs(self):
        return self.var, self.val

    def __str__(self) -> str:
        return ':='

# Узел реализующий условный оператор if
# cond логическое выражение внутри if
# then_stmt выражение выполняющееся при true в cond
# else_stmt выражение выполняющееся при false в cond
class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.cond, self.then_stmt) + ((self.else_stmt,) if self.else_stmt else tuple())

    def __str__(self) -> str:
        return 'if'

# Узел реализующий цикл while
# cond логическое выражение внутри while
# stmt_list операторы в теле цикла
class WhileNode(StmtNode):
    def __init__(self, cond: ExprNode, stmt_list: StmtNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.stmt_list = stmt_list

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.cond, self.stmt_list)

    def __str__(self) -> str:
        return 'while'

# в данный момент в разработке
class RepeatNode(StmtNode):
    def __init__(self, stmt_list: StmtNode, cond: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.stmt_list = stmt_list
        self.cond = cond

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.stmt_list, self.cond)

    def __str__(self) -> str:
        return 'repeat'

# Узел описывающий цикл с параметром for
# init начальное значение
# to конечное значение
# body оператор в теле цикла
class ForNode(StmtNode):
    def __init__(self, init: Union[StmtNode, None],
                 to,
                 body: Union[StmtNode, None],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.init = init if init else _empty
        self.to = to
        self.body = body if body else _empty

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.init, self.to, self.body

    def __str__(self) -> str:
        return 'for'

# Узел содержащий список выражений
class StmtListNode(StmtNode):
    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.stmts = exprs

    @property
    def childs(self) -> Tuple[StmtNode, ...]:
        return self.stmts

    def __str__(self) -> str:
        return '...'

# Узел являющийся телом (внутренности между begin и end) содержащий список выражений
class BodyNode(ExprNode):
    def __init__(self, body: Tuple[StmtNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.body = body

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (self.body,)

    def __str__(self) -> str:
        return 'Body'

# Узел содержащий параметры функции, процедуры
#TODO переделать, параметры считываются неправильно
class ParamsNode(StmtNode):
    def __init__(self, *vars_list: VarDeclNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.vars_list = vars_list if vars_list else _empty

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.vars_list

    def __str__(self) -> str:
        return 'params'

# Узел блока программы (содержит объявления и составной оператор)
class BlockNode(StmtNode):
    def __init__(self, *args, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        
        print(f"DEBUG: Creating BlockNode with args: {[type(arg).__name__ for arg in args]}")
        
        # Разбираем аргументы блока
        self.var_section = None
        self.declarations = []
        self.stmt_list = None
        
        for arg in args:
            if isinstance(arg, VarSectionNode):
                self.var_section = arg
            elif isinstance(arg, (ProcedureDeclNode, FunctionDeclNode)):
                self.declarations.append(arg)
            elif isinstance(arg, StmtListNode):
                self.stmt_list = arg
            elif hasattr(arg, 'stmts'):  # Составной оператор
                self.stmt_list = arg
        
        # Если нет stmt_list, создаем пустой
        if self.stmt_list is None:
            self.stmt_list = StmtListNode()

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        result = []
        if self.var_section:
            result.append(self.var_section)
        result.extend(self.declarations)
        result.append(self.stmt_list)
        return tuple(result)

    def __str__(self) -> str:
        return 'block'

# Узел содержщий объявление процедуры
# число параметров *args зависит от того, объявили мы процедуру с параметрами или без
class ProcedureDeclNode(StmtNode):
    def __init__(self, *args, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        print(f"DEBUG: Creating ProcedureDeclNode with {len(args)} args: {[str(arg)[:50] for arg in args]}")
        
        # Parse the procedure declaration from the arguments
        self.name = IdentNode("unknown_procedure")
        self.params = ()
        self.vars_decl = None
        self.stmt_list = StmtListNode()
        
        try:
            if args and len(args) > 0:
                # The parser should give us a grouped result
                tokens = args[0]
                print(f"DEBUG: ProcedureDeclNode parsing tokens: {tokens}")
                
                # If it's a ParseResults or similar iterable, extract components
                if hasattr(tokens, '__iter__') and not isinstance(tokens, str):
                    token_list = list(tokens)
                    print(f"DEBUG: ProcedureDeclNode token list: {[str(t) for t in token_list]}")
                    
                    # Expected structure: ['procedure', name, [params], ';', block, ';']
                    # Or: ['procedure', name, ';', block, ';'] (no params)
                    if len(token_list) >= 2:
                        # Skip 'procedure' keyword, get name
                        if len(token_list) > 1:
                            name_node = token_list[1]
                            print(f"DEBUG: ProcedureDeclNode name_node: {name_node}, type: {type(name_node)}")
                            if hasattr(name_node, 'name'):
                                self.name = name_node
                                print(f"DEBUG: ProcedureDeclNode extracted name: {self.name.name}")
                            elif isinstance(name_node, str):
                                self.name = IdentNode(name_node)
                                print(f"DEBUG: ProcedureDeclNode extracted name from string: {name_node}")
                        
                        # Look for block (should be at the end)
                        for token in reversed(token_list):
                            print(f"DEBUG: ProcedureDeclNode checking block token: {token}, type: {type(token)}")
                            if 'Block' in str(type(token)):
                                if hasattr(token, 'stmt_list'):
                                    self.stmt_list = token.stmt_list
                                else:
                                    self.stmt_list = token
                                print(f"DEBUG: ProcedureDeclNode extracted block")
                                break
                
        except Exception as e:
            print(f"DEBUG: Error parsing ProcedureDeclNode: {e}")
            # Keep defaults if parsing fails
        
        print(f"DEBUG: ProcedureDeclNode created successfully")

    @property
    def childs(self) -> Tuple[IdentNode, ...]:
        result = []
        if self.name:
            result.append(self.name)
        result.extend(self.params)
        if self.vars_decl:
            result.append(self.vars_decl)
        if self.stmt_list:
            result.append(self.stmt_list)
        return tuple(result)

    def __str__(self) -> str:
        return 'procedure'


# Узел содержщий объявление функции
# число параметров *args зависит от того, объявили мы функцию с параметрами или без
class FunctionDeclNode(StmtNode):
    def __init__(self, *args, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        print(f"DEBUG: Creating FunctionDeclNode with {len(args)} args: {[str(arg)[:50] for arg in args]}")
        
        # Parse the function declaration from the arguments
        self.name = IdentNode("unknown_function")
        self.params = ()
        self.return_type = TypeSpecNode("integer")
        self.vars_decl = None
        self.stmt_list = StmtListNode()
        
        try:
            if args and len(args) > 0:
                # The parser should give us a grouped result
                tokens = args[0]
                print(f"DEBUG: FunctionDeclNode parsing tokens: {tokens}")
                
                # If it's a ParseResults or similar iterable, extract components
                if hasattr(tokens, '__iter__') and not isinstance(tokens, str):
                    token_list = list(tokens)
                    print(f"DEBUG: FunctionDeclNode token list: {[str(t) for t in token_list]}")
                    
                    # Expected structure: ['function', name, [params], ':', return_type, ';', block, ';']
                    # Or: ['function', name, ':', return_type, ';', block, ';'] (no params)
                    if len(token_list) >= 2:
                        # Skip 'function' keyword, get name
                        if len(token_list) > 1:
                            name_node = token_list[1]
                            print(f"DEBUG: FunctionDeclNode name_node: {name_node}, type: {type(name_node)}")
                            if hasattr(name_node, 'name'):
                                self.name = name_node
                                print(f"DEBUG: FunctionDeclNode extracted name: {self.name.name}")
                            elif isinstance(name_node, str):
                                self.name = IdentNode(name_node)
                                print(f"DEBUG: FunctionDeclNode extracted name from string: {name_node}")
                        
                        # Look for return type (after ':' or as TypeSpecNode)
                        for i, token in enumerate(token_list):
                            print(f"DEBUG: FunctionDeclNode checking token {i}: {token}, type: {type(token)}")
                            if 'TypeSpec' in str(type(token)):
                                self.return_type = token
                                print(f"DEBUG: FunctionDeclNode extracted return type: {self.return_type.name}")
                                break
                        
                        # Look for params (ParamsNode)
                        for token in token_list:
                            token_type_str = str(type(token))
                            print(f"DEBUG: FunctionDeclNode checking for params - token type: {token_type_str}")
                            if 'ParamsNode' in token_type_str:
                                self.params = (token,)  # Store as tuple
                                print(f"DEBUG: FunctionDeclNode extracted params: {token}")
                                break
                        
                        # Look for block (should be at the end)
                        for token in reversed(token_list):
                            print(f"DEBUG: FunctionDeclNode checking block token: {token}, type: {type(token)}")
                            if 'Block' in str(type(token)):
                                if hasattr(token, 'stmt_list'):
                                    self.stmt_list = token.stmt_list
                                else:
                                    self.stmt_list = token
                                print(f"DEBUG: FunctionDeclNode extracted block")
                                break
                
        except Exception as e:
            print(f"DEBUG: Error parsing FunctionDeclNode: {e}")
            # Keep defaults if parsing fails
        
        print(f"DEBUG: FunctionDeclNode created successfully")

    @property
    def childs(self) -> Tuple[IdentNode, ...]:
        result = []
        if self.name:
            result.append(self.name)
        result.extend(self.params)
        if self.return_type:
            result.append(self.return_type)
        if self.vars_decl:
            result.append(self.vars_decl)
        if self.stmt_list:
            result.append(self.stmt_list)
        return tuple(result)

    def __str__(self) -> str:
        return 'function'


# Добавляем класс DeclSectionNode в файл nodes.py
class DeclSectionNode(StmtNode):
    def __init__(self, *decls: Tuple[Union[VarsDeclNode, ProcedureDeclNode, FunctionDeclNode], ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.decls = decls

    @property
    def childs(self) -> Tuple[Union[VarsDeclNode, ProcedureDeclNode, FunctionDeclNode], ...]:
        return self.decls

    def __str__(self) -> str:
        return 'declarations'


# Узел реализующий раздел описания переменных из грамматики
class VarSectionNode(StmtNode):
    def __init__(self, *var_decs: Tuple[Union[VarDeclNode, ArrayDeclNode], ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var_decs = var_decs

    @property
    def childs(self) -> Tuple[Union[VarDeclNode, ArrayDeclNode], ...]:
        return self.var_decs

    def __str__(self) -> str:
        return 'var_section'

# Узел описывающий программу
# prog_name название программы
# vars_decl раздел описаний
# stmt_list тело программы
class ProgramNode(StmtNode):
    def __init__(self, *args, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        
        # Более гибкая обработка аргументов
        # Ожидаем: PROGRAM ident SEMI block DOT (где некоторые элементы подавлены)
        
        if len(args) >= 1:
            self.name = args[0]  # ident - имя программы
            
            # Ищем блок программы
            block = None
            for arg in args[1:]:
                if isinstance(arg, BlockNode):
                    block = arg
                    break
                elif hasattr(arg, 'childs') or isinstance(arg, StmtListNode):
                    block = arg
                    break
            
            if isinstance(block, BlockNode):
                # Обрабатываем BlockNode
                self.decl_section = block.var_section
                self.stmt_list = block.stmt_list
                
                # Если есть объявления процедур/функций, создаем DeclSectionNode
                if block.declarations:
                    if self.decl_section:
                        # Комбинируем существующие объявления переменных с процедурами/функциями
                        all_decls = [self.decl_section] + block.declarations
                        self.decl_section = DeclSectionNode(*all_decls)
                    else:
                        self.decl_section = DeclSectionNode(*block.declarations)
                        
            elif block and hasattr(block, 'childs') and len(block.childs) > 0:
                # Блок содержит секции объявлений и основной код
                childs = block.childs
                
                # Пытаемся найти секцию объявлений и тело программы
                self.decl_section = None
                self.stmt_list = None
                
                for child in childs:
                    if isinstance(child, (VarSectionNode, DeclSectionNode)):
                        self.decl_section = child
                    elif isinstance(child, StmtListNode):
                        self.stmt_list = child
                    elif hasattr(child, 'stmts'):  # Составной оператор
                        self.stmt_list = child
                
                # Если не нашли stmt_list, используем блок как stmt_list
                if self.stmt_list is None:
                    self.stmt_list = block if isinstance(block, StmtListNode) else StmtListNode()
            else:
                # Простая структура
                self.decl_section = None
                self.stmt_list = block if isinstance(block, StmtListNode) else StmtListNode()
        else:
            # Минимальная программа
            self.name = IdentNode("unknown")
            self.decl_section = None
            self.stmt_list = StmtListNode()

    @property
    def childs(self) -> Tuple[IdentNode, Optional[DeclSectionNode], StmtListNode]:
        return (self.name,) + ((self.decl_section,) if self.decl_section else tuple()) + (self.stmt_list,)

    def __str__(self) -> str:
        return 'program'

_empty = StmtListNode()