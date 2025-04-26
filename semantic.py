from nodes import *
from grammar import *
from symbols import *


class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level, enclosing_scope=None):
        self._symbols = {}
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self.init_builtins()
        self.init_builtin_functions()

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
                ('Scope name', self.scope_name),
                ('Scope level', self.scope_level),
                ('Enclosing scope',
                 self.enclosing_scope.scope_name if self.enclosing_scope else None
                )
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, str(value)))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    def init_builtins(self):
        self.define(BuiltinTypeSymbol('integer'))
        self.define(BuiltinTypeSymbol('char'))
        self.define(BuiltinTypeSymbol('boolean'))

    def init_builtin_functions(self):
        self.define(BuiltinFunction('Read'))
        self.define(BuiltinFunction('ReadLn'))
        self.define(BuiltinFunction('Write'))
        self.define(BuiltinFunction('WriteLn'))

    def define(self, symbol: Symbol):
        print('Define: %s' % symbol)
        self._symbols[symbol.name] = symbol

    def lookup(self, name, current_scope_only=False) -> Symbol:
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        if symbol is not None:
            return symbol

        if current_scope_only:
            return None

        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)



class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        # self.global_scope = ScopedSymbolTable(scope_name='global', scope_level=1)
        # self.current_scope = self.global_scope
        self.dictionary = {'int':'integer', 'str':'char','bool':'boolean'}
        self.BinOpArgTypes = {
            'ADD':['integer','char'],
            'SUB':['integer'],
            'MUL':['integer'],
            'DIVISION':['integer'],
            'DIV':['integer'],
            'MOD':['integer'],
            'GE':['integer','char'],
            'LE':['integer','char'],
            'NEQUALS':['integer','char','boolean'],
            'EQUALS':['integer','char','boolean'],
            'GT':['integer','char'],
            'LT': ['integer', 'char'],
            'LOGICAL_AND':['boolean'],
            'LOGICAL_OR':['boolean']}

        self.BinOpReturnTypes = {
            'ADD': ['integer', 'char'],
            'SUB': ['integer'],
            'MUL': ['integer'],
            'DIVISION': ['integer'],
            'DIV': ['integer'],
            'MOD': ['integer'],
            'GE': ['boolean'],
            'LE': ['boolean'],
            'NEQUALS': ['boolean'],
            'EQUALS': ['boolean'],
            'GT': ['boolean'],
            'LT': ['boolean'],
            'LOGICAL_AND': ['boolean'],
            'LOGICAL_OR': ['boolean']}
        self.current_scope = None
        self.log = []

    #convert type name to a correct format
    def __changeType(self,type) -> str:
        for key in self.dictionary:
            if type == key :
                return self.dictionary[key]
        return type

    def __typeChecker(self, type1, type2):
        if(type1 is None or type2 is None):
            return True
        if type1 == type2:
            return True
        for key in self.dictionary:
            if(type1 == key and type2 == self.dictionary[key] or type2==key and type1==self.dictionary[key]):
                return True
        return False

    def __isBinaryArgsValid(self, binOP, type_var):
        for key in self.BinOpArgTypes:
            if(binOP == key and type_var in self.BinOpArgTypes[key]):
                return True
        return False

    def __BinaryReturningType(self,binOP,type_var)->str:
        for key in self.BinOpReturnTypes:
            if key == binOP:
                if len(self.BinOpReturnTypes[key]) == 1:
                    return self.BinOpReturnTypes[key][0]
                else:
                    return type_var


    def visit_BinOpNode(self, node):
        type_arg1 = self.visit(node.arg1)
        type_arg2 = self.visit(node.arg2)

        if (not isinstance(node.arg1, BinOpNode)) or not (isinstance(node.arg2, BinOpNode)):
            if type_arg1 is not None and not self.__typeChecker(type_arg1, type_arg2):
                raise Exception("Incompatible types in line: ")
            type_arg1 = self.__changeType(type_arg1)
            type_arg2 = self.__changeType(type_arg2)
            if not self.__isBinaryArgsValid(node.op.name, type_arg1):
                raise Exception(
                    "Operation {op} not supported for types {t1} and {t2}"
                        .format(op = node.op.name,t1 = type_arg1,t2=type_arg2))
            return self.__BinaryReturningType(node.op.name, type_arg1)

    def visit_IdentNode(self, node: IdentNode):
        var_name = node.name
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            raise Exception("Symbol(identifier) not found '%s'" % var_name)
        return var_symbol.type.name

    def visit_LiteralNode(self, node: LiteralNode):
        return type(node.value).__name__

    def visit_ProgramNode(self, node):
        self.global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
        )
        self.current_scope = self.global_scope
        self.log.append(f'ENTER scope: global')
        self.current_scope.init_builtins()
        self.current_scope.init_builtin_functions()

        # Посещаем блок объявлений
        if hasattr(node, 'decl_section') and node.decl_section:
            self.visit(node.decl_section)

        # Посещаем тело программы
        self.visit(node.stmt_list)
        
        self.log.append(f'LEAVE scope: global')
        self.current_scope = None

    def visit_VarsDeclNode(self, node: VarsDeclNode):
        for var_decl in node.var_decs:
            self.visit(var_decl)

    def visit_VarDeclNode(self, node: VarDeclNode):
        type_symbol = self.current_scope.lookup(node.vars_type.name)
        for ident in node.ident_list.idents:
            var_name = ident.name
            var_symbol = VarSymbol(var_name, type_symbol)
            #only for current scope
            if self.current_scope.lookup(var_name, current_scope_only=True):
                raise Exception(
                    "Duplicate identifier '%s' found" % var_name
                )
            self.current_scope.define(var_symbol)


    def visit_ArrayDeclNode(self, node: ArrayDeclNode):
        type = node.vars_type
        from_ = node.from_.literal
        to_ = node.to_.literal
        for ident in node.name.idents:
            arr_name = ident.name
            arr_symb = ArraySymbol(arr_name,type,from_,to_)
            if self.current_scope.lookup(arr_name,current_scope_only=True):
                raise Exception(
                    "Duplicate identifier '%s' found" % arr_name
                )
            self.current_scope.define(arr_symb)

    def visit_ArrayIdentNode(self, node : ArrayIdentNode):
        arr_name = node.name.name
        liter = int(node.literal.literal)
        arr_symbol : ArraySymbol = self.current_scope.lookup(arr_name)
        if(liter < int(arr_symbol.from_) or liter > int(arr_symbol.to_)):
            raise Exception("Out of range '%s'" % liter)
        return arr_symbol.type.name



    def visit_BodyNode(self, node: BodyNode):
        self.visit(node.body)

    def visit_StmtListNode(self, node: StmtListNode):
        for stmt in node.exprs:
            self.visit(stmt)

    def visit_AssignNode(self, node: AssignNode):
        var = node.var
        visit = node.val
        type_var =None

        if( isinstance(var,ArrayIdentNode) ):
            var_name = var.name.name
            type_var = self.visit(var)
        else:
            var_name = var.name
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            #raise NameError(var_name)
            raise Exception(
                "Undefined variable '%s' found" % var_name
            )
        type_visited = self.visit(visit)
        if type_var is None: type_var=var_symbol.type.name
        if not self.__typeChecker(type_visited, type_var):
            raise Exception(
                "Wrong type '%s' found" % var_name
            )

    def visit_ProcedureDeclNode(self, node: ProcedureDeclNode):
        proc_name = node.name.name
        proc_symbol = ProcedureSymbol(proc_name)
        self.current_scope.define(proc_symbol)

        self.log.append(f'ENTER scope: {proc_name}')
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )

        self.current_scope = procedure_scope
        
        # Обрабатываем параметры
        for param in node.params:
            if isinstance(param, IdentNode):
                # Это может быть простой идентификатор
                param_name = param.name
                param_type = self.current_scope.lookup('integer')  # По умолчанию integer
                var_symbol = VarSymbol(param_name, param_type)
                self.current_scope.define(var_symbol)
                proc_symbol.params.append(var_symbol)
            else:
                # Это может быть декларация типа
                param_type = self.current_scope.lookup(param.vars_type.name)
                for param_name in param.ident_list.idents:
                    var_symbol = VarSymbol(param_name.name, param_type)
                    self.current_scope.define(var_symbol)
                    proc_symbol.params.append(var_symbol)

        # Проверяем, есть ли после параметров объявления внутри процедуры
        i_next = 2
        if i_next < len(node.decls) and isinstance(node.decls[i_next], DeclSectionNode):
            # Обрабатываем объявления внутри процедуры
            print(f"DEBUG: Processing inner declarations for procedure {proc_name}")
            self.visit(node.decls[i_next])
            i_next += 1

        # Проверяем, есть ли тело процедуры
        if i_next < len(node.decls) and isinstance(node.decls[i_next], StmtListNode):
            # Обрабатываем тело процедуры
            print(f"DEBUG: Processing body for procedure {proc_name}")
            self.visit(node.decls[i_next])

        # Завершаем область видимости процедуры
        self.log.append(str(procedure_scope))
        self.current_scope = self.current_scope.enclosing_scope
        self.log.append(f'LEAVE scope: {proc_name}')

        # Пропускаем обработанные узлы
        i = i_next + 1

    def visit_FunctionDeclNode(self, node: FunctionDeclNode):
        func_name = node.name.name
        func_type = node.return_type.name
        func_symbol = FunctionSymbol(func_name)
        func_symbol.type = func_type
        self.current_scope.define(func_symbol)

        self.log.append(f'ENTER scope: {func_name}')
        function_scope = ScopedSymbolTable(
            scope_name=func_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )

        self.current_scope = function_scope
        
        # Обрабатываем параметры
        for param in node.params:
            if isinstance(param, IdentNode):
                # Это может быть простой идентификатор
                param_name = param.name
                param_type = self.current_scope.lookup('integer')  # По умолчанию integer
                var_symbol = VarSymbol(param_name, param_type)
                self.current_scope.define(var_symbol)
                func_symbol.params.append(var_symbol)
            else:
                # Это может быть декларация типа
                param_type = self.current_scope.lookup(param.vars_type.name)
                for param_name in param.ident_list.idents:
                    var_symbol = VarSymbol(param_name.name, param_type)
                    self.current_scope.define(var_symbol)
                    func_symbol.params.append(var_symbol)

        # Обрабатываем локальные переменные
        if hasattr(node, 'vars_decl') and node.vars_decl:
            self.visit(node.vars_decl)

        # Обрабатываем тело функции
        self.visit(node.stmt_list)

        self.log.append(str(function_scope))
        self.current_scope = self.current_scope.enclosing_scope
        self.log.append(f'LEAVE scope: {func_name}')

    def visit_CallNode(self, node: CallNode):
        func_name = node.func.name
        func_symbol = self.current_scope.lookup(func_name)
        if func_symbol is None:
            raise Exception(
                "Undefined function '%s' " % func_name
            )
        #TODO builtin vs proc and func
        if (isinstance(func_symbol, FunctionSymbol) or isinstance(func_symbol, ProcedureSymbol)):
            if(len(node.params) != len(func_symbol.params)):
                raise Exception(
                    "Wrong number of parameters specified for call to '%s' " % func_name
                )
        for param in node.params:
            self.visit(param)
        return func_symbol.type

    def visit_IfNode(self, node: IfNode):
        type_cond = self.visit(node.cond)
        if (type_cond != 'boolean'):
            raise Exception(
                "Wrong type of if condition '%s' " % type_cond
            )
        self.visit(node.then_stmt)

        if node.else_stmt:
            self.visit(node.else_stmt)



    def visit_WhileNode(self, node: WhileNode):
        type_cond = self.visit(node.cond)
        if (type_cond != 'boolean'):
            raise Exception(
                "Wrong type of while condition '%s' " % type_cond
            )
        self.visit(node.stmt_list)

    #TODO check type of node.init
    def visit_ForNode(self, node: ForNode):
        type_init = self.visit(node.init)
        type_to = self.visit(node.to)
        if (type_to != 'int'):
            raise Exception(
                "Wrong type of for condition '%s'" % type_to
            )
        self.visit(node.body)

    def visit_DeclSectionNode(self, node: DeclSectionNode):
        """
        Обрабатываем секцию объявлений с учетом особенностей AST
        """
        print("\nDEBUG: DeclSectionNode contents:")
        for i, decl in enumerate(node.decls):
            print(f"  {i}: {type(decl).__name__}")
            if hasattr(decl, 'name'):
                print(f"     name: {decl.name}")
            if hasattr(decl, 'childs'):
                print(f"     childs: {[type(c).__name__ for c in decl.childs]}")
        
        # Определение структуры AST - какие узлы образуют процедуру или функцию
        i = 0
        while i < len(node.decls):
            decl = node.decls[i]
            
            if isinstance(decl, VarDeclNode) or isinstance(decl, ArrayDeclNode) or isinstance(decl, VarsDeclNode):
                # Обработка обычных объявлений переменных
                self.visit(decl)
                i += 1
            elif isinstance(decl, IdentNode) and i + 2 < len(node.decls) and isinstance(node.decls[i+1], ParamsNode):
                # Это похоже на начало процедуры: имя + параметры
                proc_name = decl.name
                print(f"DEBUG: Found procedure {proc_name}")
                
                # Создаем символ процедуры
                proc_symbol = ProcedureSymbol(proc_name)
                self.current_scope.define(proc_symbol)
                
                # Создаем область видимости для процедуры
                self.log.append(f'ENTER scope: {proc_name}')
                procedure_scope = ScopedSymbolTable(
                    scope_name=proc_name,
                    scope_level=self.current_scope.scope_level + 1,
                    enclosing_scope=self.current_scope
                )
                self.current_scope = procedure_scope
                
                # Обрабатываем параметры
                params_node = node.decls[i+1]
                print(f"DEBUG: Processing parameters for procedure {proc_name}")
                if isinstance(params_node, ParamsNode):
                    for child in params_node.childs:
                        if isinstance(child, IdentListNode):
                            # Получаем список идентификаторов параметров
                            for ident in child.idents:
                                print(f"DEBUG: Processing parameter {ident.name}")
                                param_name = ident.name
                                # По умолчанию тип integer, но может быть указан явно
                                param_type = self.current_scope.lookup('integer')
                                var_symbol = VarSymbol(param_name, param_type)
                                self.current_scope.define(var_symbol)
                                proc_symbol.params.append(var_symbol)
                        elif isinstance(child, TypeSpecNode):
                            # Получен тип параметров
                            param_type_name = child.name
                            param_type = self.current_scope.lookup(param_type_name)
                            # Обновляем тип последнего добавленного параметра
                            if proc_symbol.params and param_type:
                                for param in proc_symbol.params:
                                    param.type = param_type
                
                # Проверяем, есть ли после параметров объявления внутри процедуры
                i_next = i + 2
                if i_next < len(node.decls) and isinstance(node.decls[i_next], DeclSectionNode):
                    # Обрабатываем объявления внутри процедуры
                    print(f"DEBUG: Processing inner declarations for procedure {proc_name}")
                    self.visit(node.decls[i_next])
                    i_next += 1

                # Проверяем, есть ли тело процедуры
                if i_next < len(node.decls) and isinstance(node.decls[i_next], StmtListNode):
                    # Обрабатываем тело процедуры
                    print(f"DEBUG: Processing body for procedure {proc_name}")
                    self.visit(node.decls[i_next])

                # Завершаем область видимости процедуры
                self.log.append(str(procedure_scope))
                self.current_scope = self.current_scope.enclosing_scope
                self.log.append(f'LEAVE scope: {proc_name}')
                
                # Пропускаем обработанные узлы
                i = i_next + 1
            else:
                # Обработка других типов узлов
                try:
                    self.visit(decl)
                except Exception as e:
                    print(f"WARNING: Error processing node {type(decl).__name__}: {e}")
                i += 1

    def visit_ParamsNode(self, node: ParamsNode):
        """
        Обработка узла параметров процедуры или функции
        """
        print("DEBUG: ParamsNode processing")
        # В текущей реализации мы просто пропускаем узел параметров,
        # так как они должны обрабатываться в контексте ProcedureDeclNode
        # Но в нашем случае структура AST разбита на отдельные компоненты
        pass

    def visit_TypeSpecNode(self, node: TypeSpecNode):
        """
        Обработка узла с типом
        """
        print(f"DEBUG: TypeSpecNode processing: {node.name}")
        return node.name