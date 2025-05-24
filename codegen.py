from nodes import *
from typing import Dict, List, Set
import os
import subprocess

class MSILCodeGenerator:
    def __init__(self):
        self.code = []
        self.variables = {}  # var_name -> type
        self.procedures = {}  # proc_name -> params
        self.functions = {}  # func_name -> (params, return_type)
        self.label_counter = 0
        self.local_vars = set()
        self.current_function = None  # Текущая функция/процедура
        self.current_params = {}  # Параметры текущей функции: name -> index
        
    def new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"
    
    def emit(self, instruction: str):
        self.code.append(instruction)
    
    def generate_program(self, program: ProgramNode) -> str:
        self.emit(".assembly extern mscorlib {}")
        self.emit(".assembly program")
        self.emit("{")
        self.emit("  .ver 1:0:0:0")
        self.emit("}")
        self.emit("")
        self.emit(".module program.exe")
        self.emit("")
        self.emit(".class private auto ansi beforefieldinit Program")
        self.emit("       extends [mscorlib]System.Object")
        self.emit("{")
          # Анализируем структуру AST программы
        if hasattr(program, 'childs') and len(program.childs) >= 2:
            print(f"DEBUG: Program has {len(program.childs)} children")
            
            # Ожидаем структуру: [IdentNode (имя), DeclSectionNode (объявления), StmtListNode (основная программа)]
            decl_section = None
            main_stmts = None
            
            for i, child in enumerate(program.childs):
                print(f"DEBUG: Child {i}: {type(child).__name__}")
                if isinstance(child, IdentNode):
                    # Имя программы, пропускаем
                    continue
                elif hasattr(child, '__class__') and 'DeclSection' in child.__class__.__name__:
                    # Секция объявлений
                    decl_section = child
                elif isinstance(child, StmtListNode):
                    # Основная программа
                    main_stmts = child
                elif isinstance(child, BlockNode):
                    # Если все-таки BlockNode
                    decl_section = child
                    main_stmts = child.stmt_list
            
            # Собираем информацию об объявлениях
            if decl_section:
                self.collect_declarations(decl_section)
                
                # Генерируем функции и процедуры
                if hasattr(decl_section, 'childs'):
                    for decl in decl_section.childs:
                        if isinstance(decl, FunctionDeclNode):
                            self.generate_function(decl)
                        elif isinstance(decl, ProcedureDeclNode):
                            self.generate_procedure(decl)
          # Предварительный сбор локальных переменных из основной программы
        main_statements = None
        if hasattr(program, 'childs') and len(program.childs) > 0:
            for child in program.childs:
                if isinstance(child, StmtListNode):
                    main_statements = child
                    break
        
        if main_statements:
            self.collect_local_variables_from_statements(main_statements)
        
        # Генерация главной функции
        self.emit("  .method private hidebysig static void Main(string[] args) cil managed")
        self.emit("  {")
        self.emit("    .entrypoint")
        self.emit("    .maxstack 8")
        
        # Генерация локальных переменных
        if self.local_vars:
            locals_decl = "    .locals init ("
            local_list = []
            for var_name in self.local_vars:
                var_type = self.variables.get(var_name, "integer")
                local_list.append(f"{self.get_msil_type(var_type)} {var_name}")
            locals_decl += ", ".join(local_list) + ")"
            self.emit(locals_decl)
          # Генерация тела программы
        if main_stmts:
            self.generate_statement_list(main_stmts)
        elif hasattr(program, 'childs') and len(program.childs) > 0:
            # Fallback: ищем последний StmtListNode
            for child in reversed(program.childs):
                if isinstance(child, StmtListNode):
                    self.generate_statement_list(child)
                    break
        elif hasattr(program, 'stmt_list') and program.stmt_list:
            self.generate_statement_list(program.stmt_list)
        
        self.emit("    ret")
        self.emit("  }")
        
        self.emit("}")
        
        return "\n".join(self.code)
    
    def collect_declarations(self, decl_section):
        """Собираем информацию о объявлениях переменных, функций и процедур"""
        if hasattr(decl_section, 'childs'):
            for child in decl_section.childs:
                print(f"DEBUG: Collecting decl child: {type(child).__name__}")
                if hasattr(child, '__class__') and child.__class__.__name__ == 'VarSectionNode':
                    if hasattr(child, 'childs'):
                        for var_child in child.childs:
                            if isinstance(var_child, VarDeclNode):
                                self.collect_var_declaration(var_child)
                elif isinstance(child, VarDeclNode):
                    self.collect_var_declaration(child)
                elif isinstance(child, ArrayDeclNode):
                    self.collect_array_declaration(child)
                elif isinstance(child, ProcedureDeclNode):
                    self.collect_procedure(child)
                elif isinstance(child, FunctionDeclNode):
                    self.collect_function(child)
        elif hasattr(decl_section, 'decls'):
            for decl in decl_section.decls:
                if isinstance(decl, VarsDeclNode):
                    for var_decl in decl.var_decs:
                        self.collect_var_declaration(var_decl)
                elif isinstance(decl, ProcedureDeclNode):
                    self.collect_procedure(decl)
                elif isinstance(decl, FunctionDeclNode):
                    self.collect_function(decl)
        else:
            self.collect_var_declarations(decl_section)
    
    def collect_var_declarations(self, vars_decl):
        if hasattr(vars_decl, 'var_decs'):
            for var_decl in vars_decl.var_decs:
                self.collect_var_declaration(var_decl)
        elif hasattr(vars_decl, 'childs'):
            for child in vars_decl.childs:
                if isinstance(child, VarDeclNode):
                    self.collect_var_declaration(child)
    
    def collect_var_declaration(self, var_decl: VarDeclNode):
        for ident in var_decl.ident_list.idents:
            self.variables[ident.name] = var_decl.vars_type.name
            self.local_vars.add(ident.name)
            print(f"DEBUG: Collected variable {ident.name}: {var_decl.vars_type.name}")
    
    def collect_array_declaration(self, array_decl: ArrayDeclNode):
        if hasattr(array_decl, 'name') and hasattr(array_decl.name, 'idents'):
            for ident in array_decl.name.idents:
                self.variables[ident.name] = f"array_{array_decl.vars_type.name}"
                self.local_vars.add(ident.name)
    
    def collect_procedure(self, proc_decl: ProcedureDeclNode):
        params = []
        if proc_decl.params:
            for param in proc_decl.params:
                if hasattr(param, 'vars_list'):
                    for var_decl in param.vars_list:
                        if hasattr(var_decl, 'ident_list'):
                            for ident in var_decl.ident_list.idents:
                                params.append((ident.name, var_decl.vars_type.name))
        self.procedures[proc_decl.name.name] = params
        print(f"DEBUG: Collected procedure {proc_decl.name.name} with params: {params}")
    
    def collect_function(self, func_decl: FunctionDeclNode):
        params = []
        if func_decl.params:
            # func_decl.params это кортеж с ParamsNode
            if hasattr(func_decl.params, '__iter__'):
                for param_node in func_decl.params:
                    if hasattr(param_node, 'vars_list'):
                        # ParamsNode имеет vars_list как кортеж (IdentListNode, TypeSpecNode)
                        if len(param_node.vars_list) >= 2:
                            ident_list = param_node.vars_list[0]  # IdentListNode
                            type_spec = param_node.vars_list[1]   # TypeSpecNode
                            if hasattr(ident_list, 'idents') and hasattr(type_spec, 'name'):
                                for ident in ident_list.idents:
                                    params.append((ident.name, type_spec.name))
                                    print(f"DEBUG: Function param from vars_list: {ident.name}:{type_spec.name}")
                        else:
                            # Старая обработка для совместимости
                            for var_decl in param_node.vars_list:
                                if hasattr(var_decl, 'ident_list'):
                                    for ident in var_decl.ident_list.idents:
                                        params.append((ident.name, var_decl.vars_type.name))
                                else:
                                    print(f"DEBUG: Unexpected var_decl structure: {type(var_decl)}")
                    elif hasattr(param_node, 'childs'):
                        # ParamsNode может иметь childs вместо vars_list
                        if len(param_node.childs) >= 2:
                            ident_list = param_node.childs[0]  # IdentListNode
                            type_spec = param_node.childs[1]   # TypeSpecNode
                            if hasattr(ident_list, 'idents') and hasattr(type_spec, 'name'):
                                for ident in ident_list.idents:
                                    params.append((ident.name, type_spec.name))
                                    print(f"DEBUG: Function param from childs: {ident.name}:{type_spec.name}")
        return_type = func_decl.return_type.name if func_decl.return_type else "integer"
        self.functions[func_decl.name.name] = (params, return_type)
        print(f"DEBUG: Collected function {func_decl.name.name} with params: {params}, return: {return_type}")    
        
    def generate_procedure(self, proc_decl: ProcedureDeclNode):
        proc_name = proc_decl.name.name
        params = self.procedures.get(proc_name, [])
        
        print(f"DEBUG: Generating procedure {proc_name}")
        
        # Устанавливаем контекст текущей функции
        old_function = self.current_function
        old_params = self.current_params
        old_local_vars = self.local_vars.copy()
        self.current_function = proc_name
        self.current_params = {}
        self.local_vars = set()
        
        # Предварительный проход для сбора локальных переменных
        if proc_decl.stmt_list:
            self.collect_local_variables_from_statements(proc_decl.stmt_list)
        
        # Создаем сигнатуру метода
        param_types = []
        for i, (param_name, param_type) in enumerate(params):
            param_types.append(self.get_msil_type(param_type))
            self.current_params[param_name] = i
        param_signature = ", ".join(param_types) if param_types else ""
        
        self.emit(f"  .method private hidebysig static void {proc_name}({param_signature}) cil managed")
        self.emit("  {")
        self.emit("    .maxstack 8")
        
        # Объявляем локальные переменные процедуры
        if self.local_vars:
            locals_decl = "    .locals init ("
            local_list = []
            for var_name in self.local_vars:
                var_type = self.variables.get(var_name, "integer")
                local_list.append(f"{self.get_msil_type(var_type)} {var_name}")
            locals_decl += ", ".join(local_list) + ")"
            self.emit(locals_decl)
        
        # Генерируем тело процедуры
        if proc_decl.stmt_list:
            self.generate_statement_list(proc_decl.stmt_list)
        
        self.emit("    ret")
        self.emit("  }")
        
        # Восстанавливаем контекст
        self.current_function = old_function
        self.current_params = old_params
        self.local_vars = old_local_vars    

    def generate_function(self, func_decl: FunctionDeclNode):
        """Генерируем MSIL код для функции"""
        func_name = func_decl.name.name
        func_info = self.functions.get(func_name, ([], "integer"))
        params, return_type = func_info
        
        print(f"DEBUG: Generating function {func_name}")
        
        # Устанавливаем контекст текущей функции
        old_function = self.current_function
        old_params = self.current_params
        old_local_vars = self.local_vars.copy()
        self.current_function = func_name
        self.current_params = {}
        self.local_vars = set()
        
        # Предварительный проход для сбора локальных переменных
        if func_decl.stmt_list:
            self.collect_local_variables_from_statements(func_decl.stmt_list)
        
        # Создаем сигнатуру метода
        param_types = []
        for i, (param_name, param_type) in enumerate(params):
            param_types.append(self.get_msil_type(param_type))
            self.current_params[param_name] = i
        param_signature = ", ".join(param_types) if param_types else ""
        return_msil_type = self.get_msil_type(return_type)
        
        self.emit(f"  .method private hidebysig static {return_msil_type} {func_name}({param_signature}) cil managed")
        self.emit("  {")
        self.emit("    .maxstack 8")
        
        # Добавляем локальную переменную для возвращаемого значения
        locals_init = [f"{return_msil_type} result"]
        
        # Собираем локальные переменные из тела функции
        if self.local_vars:
            for var_name in self.local_vars:
                var_type = self.variables.get(var_name, "integer")
                locals_init.append(f"{self.get_msil_type(var_type)} {var_name}")
        
        if locals_init:
            self.emit(f"    .locals init ({', '.join(locals_init)})")
        
        # Генерируем тело функции
        if func_decl.stmt_list:
            self.generate_statement_list(func_decl.stmt_list)
        
        # Возвращаем результат
        self.emit("    ldloc result")
        self.emit("    ret")
        self.emit("  }")
        
        # Восстанавливаем контекст
        self.current_function = old_function
        self.current_params = old_params
        self.local_vars = old_local_vars
    
    def generate_statement_list(self, stmt_list: StmtListNode):
        for stmt in stmt_list.stmts:
            self.generate_statement(stmt)
    
    def generate_statement(self, stmt: StmtNode):
        if isinstance(stmt, AssignNode):
            self.generate_assignment(stmt)
        elif isinstance(stmt, CallNode):
            self.generate_call(stmt)
        elif isinstance(stmt, IfNode):
            self.generate_if(stmt)
        elif isinstance(stmt, WhileNode):
            self.generate_while(stmt)
        elif isinstance(stmt, ForNode):
            self.generate_for(stmt)        
        elif isinstance(stmt, StmtListNode):
            self.generate_statement_list(stmt)
    
    def generate_assignment(self, assign: AssignNode):
        # Генерируем выражение для значения
        self.generate_expression(assign.val)
        
        # Сохраняем в переменную
        if isinstance(assign.var, IdentNode):
            var_name = assign.var.name
            
            # Проверяем, это присваивание возвращаемого значения функции
            if (self.current_function and 
                var_name == self.current_function and 
                var_name in self.functions):
                # Это присваивание возвращаемого значения функции (например f := n + 1)
                self.emit(f"    stloc result")
                print(f"DEBUG: Function return assignment: {var_name} := ...")
            elif var_name in self.local_vars:
                # Это локальная переменная
                self.emit(f"    stloc {var_name}")
            elif var_name in self.current_params:
                # Это параметр функции (обычно только для чтения, но возможно присваивание)
                param_index = self.current_params[var_name]
                self.emit(f"    starg {param_index}")
            else:
                # Неизвестная переменная, добавляем как локальную
                self.local_vars.add(var_name)
                self.variables[var_name] = "integer"
                self.emit(f"    stloc {var_name}")
                
        elif isinstance(assign.var, ArrayIdentNode):
            self.emit(f"    stloc {assign.var.name.name}")
    
    def generate_expression(self, expr: ExprNode):
        if isinstance(expr, LiteralNode):
            self.generate_literal(expr)
        elif isinstance(expr, IdentNode):
            var_name = expr.name
            if var_name in self.current_params:
                # Это параметр функции
                param_index = self.current_params[var_name]
                self.emit(f"    ldarg {param_index}")
                print(f"DEBUG: Loading parameter {var_name} (arg {param_index})")
            elif var_name in self.local_vars:
                # Это локальная переменная
                self.emit(f"    ldloc {var_name}")
            else:
                # Неизвестная переменная, загружаем как 0
                self.emit(f"    ldc.i4.0")
                print(f"DEBUG: Unknown variable {var_name}, loading 0")
        elif isinstance(expr, BinOpNode):
            self.generate_binary_operation(expr)
        elif isinstance(expr, CallNode):
            self.generate_call_expression(expr)
    
    def generate_literal(self, literal: LiteralNode):
        value = literal.literal
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            self.emit(f"    ldc.i4 {value}")
        elif value.startswith("'") and value.endswith("'"):
            self.emit(f"    ldstr {value}")
        elif value in ('True', 'False'):
            val = "1" if value == 'True' else "0"
            self.emit(f"    ldc.i4 {val}")
    
    def generate_binary_operation(self, binop: BinOpNode):
        self.generate_expression(binop.arg1)
        self.generate_expression(binop.arg2)
        
        op_map = {
            BinOp.ADD: "add",
            BinOp.SUB: "sub", 
            BinOp.MUL: "mul",
            BinOp.DIVISION: "div",
            BinOp.DIV: "div",
            BinOp.MOD: "rem",
            BinOp.GT: "cgt",
            BinOp.LT: "clt",
            BinOp.GE: ["clt", "ldc.i4.0", "ceq"], # a >= b -> !(a < b)
            BinOp.LE: ["cgt", "ldc.i4.0", "ceq"], # a <= b -> !(a > b)
            BinOp.EQUALS: "ceq",
            BinOp.NEQUALS: ["ceq", "ldc.i4.0", "ceq"], # a != b -> !(a == b)
            BinOp.LOGICAL_AND: "and",
            BinOp.LOGICAL_OR: "or"
        }
        
        if binop.op in op_map:
            op_code = op_map[binop.op]
            if isinstance(op_code, list):
                for instr in op_code:
                    self.emit(f"    {instr}")
            else:
                self.emit(f"    {op_code}")
    
    def generate_call(self, call: CallNode):
        """Генерируем вызов процедуры (не возвращает значение)"""
        func_name = call.func.name
        
        if func_name == "writeln":
            # Генерируем параметры
            for param in call.params:
                self.generate_expression(param)
            self.emit("    call void [mscorlib]System.Console::WriteLine(int32)")
        elif func_name == "write":
            for param in call.params:
                self.generate_expression(param)
            self.emit("    call void [mscorlib]System.Console::Write(int32)")
        elif func_name in self.procedures:
            # Вызов пользовательской процедуры
            params = self.procedures[func_name]
            
            # Генерируем параметры
            for i, param in enumerate(call.params):
                self.generate_expression(param)
            
            # Создаем сигнатуру вызова
            param_types = []
            for param_name, param_type in params:
                param_types.append(self.get_msil_type(param_type))
            param_signature = ", ".join(param_types) if param_types else ""
            
            self.emit(f"    call void Program::{func_name}({param_signature})")
        elif func_name in self.functions:
            # Вызов пользовательской функции (но результат игнорируется)
            self.generate_call_expression(call)
            self.emit("    pop")  # Убираем результат со стека
    
    def generate_call_expression(self, call: CallNode):
        """Генерируем вызов функции (возвращает значение)"""
        func_name = call.func.name
        
        if func_name in self.functions:
            # Вызов пользовательской функции
            func_info = self.functions[func_name]
            params, return_type = func_info
            
            print(f"DEBUG: Generating function call {func_name} with {len(call.params)} params")
            
            # Генерируем параметры
            for i, param in enumerate(call.params):
                print(f"DEBUG: Generating param {i}")
                self.generate_expression(param)
            
            # Создаем сигнатуру вызова
            param_types = []
            for param_name, param_type in params:
                param_types.append(self.get_msil_type(param_type))
            param_signature = ", ".join(param_types) if param_types else ""
            return_msil_type = self.get_msil_type(return_type)
            
            self.emit(f"    call {return_msil_type} Program::{func_name}({param_signature})")
        else:
            # Неизвестная функция, возвращаем 0
            print(f"DEBUG: Unknown function {func_name}, returning 0")
            self.emit("    ldc.i4.0")
    
    def generate_if(self, if_stmt: IfNode):
        else_label = self.new_label()
        end_label = self.new_label()
        
        # Генерируем условие
        self.generate_expression(if_stmt.cond)
        self.emit(f"    brfalse {else_label}")
        
        # Генерируем then-ветку
        self.generate_statement(if_stmt.then_stmt)
        self.emit(f"    br {end_label}")
        
        # Генерируем else-ветку
        self.emit(f"  {else_label}:")
        if if_stmt.else_stmt:
            self.generate_statement(if_stmt.else_stmt)
        
        self.emit(f"  {end_label}:")
    
    def generate_while(self, while_stmt: WhileNode):
        start_label = self.new_label()
        end_label = self.new_label()
        
        self.emit(f"  {start_label}:")
        self.generate_expression(while_stmt.cond)
        self.emit(f"    brfalse {end_label}")
        
        self.generate_statement(while_stmt.stmt_list)
        self.emit(f"    br {start_label}")
        
        self.emit(f"  {end_label}:")
    
    def generate_for(self, for_stmt: ForNode):
        start_label = self.new_label()
        end_label = self.new_label()
        
        # Инициализация
        if for_stmt.init:
            self.generate_statement(for_stmt.init)
        
        self.emit(f"  {start_label}:")
        
        # Проверка условия (i <= to)
        if isinstance(for_stmt.init, AssignNode):
            var_name = for_stmt.init.var.name if isinstance(for_stmt.init.var, IdentNode) else "i"
            self.emit(f"    ldloc {var_name}")
            self.generate_expression(for_stmt.to)
            self.emit(f"    cgt")
            self.emit(f"    brtrue {end_label}")
        
        # Тело цикла
        if for_stmt.body:
            self.generate_statement(for_stmt.body)
        
        # Инкремент
        if isinstance(for_stmt.init, AssignNode):
            var_name = for_stmt.init.var.name if isinstance(for_stmt.init.var, IdentNode) else "i"
            self.emit(f"    ldloc {var_name}")
            self.emit(f"    ldc.i4.1")
            self.emit(f"    add")
            self.emit(f"    stloc {var_name}")
        
        self.emit(f"    br {start_label}")
        self.emit(f"  {end_label}:")
    
    def get_msil_type(self, pascal_type: str) -> str:
        type_map = {
            "integer": "int32",
            "boolean": "bool", 
            "char": "char"
        }
        return type_map.get(pascal_type.lower(), "int32")

    def collect_local_variables_from_statements(self, stmt_list: StmtListNode):
        """Предварительный проход для сбора локальных переменных из присваиваний"""
        for stmt in stmt_list.stmts:
            if isinstance(stmt, AssignNode):
                if isinstance(stmt.var, IdentNode):
                    var_name = stmt.var.name
                    if var_name not in self.current_params and var_name != self.current_function:
                        self.local_vars.add(var_name)
                        self.variables[var_name] = "integer"
                        print(f"DEBUG: Pre-collected local var: {var_name}")
            elif isinstance(stmt, StmtListNode):
                self.collect_local_variables_from_statements(stmt)
    
def compile_to_exe(msil_code: str, output_name: str = "program") -> bool:
    """Компилирует MSIL код в исполняемый файл"""
    
    # Путь к ilasm.exe
    ilasm_path = r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\ilasm.exe"
    
    # Сохраняем MSIL код в файл
    il_file = f"{output_name}.il"
    with open(il_file, 'w') as f:
        f.write(msil_code)
    
    try:
        # Проверяем существование ilasm.exe
        if not os.path.exists(ilasm_path):
            print(f"Ошибка: ilasm.exe не найден по пути {ilasm_path}")
            return False
            
        # Компилируем с помощью ilasm
        result = subprocess.run([
            ilasm_path, 
            "/exe", 
            f"/output:{output_name}.exe", 
            il_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Успешно скомпилирован {output_name}.exe")
            if result.stdout:
                print(f"Вывод компилятора: {result.stdout}")
            return True
        else:
            print(f"Ошибка компиляции (код возврата: {result.returncode})")
            if result.stderr:
                print(f"Ошибки: {result.stderr}")
            if result.stdout:
                print(f"Вывод: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"Исключение при компиляции: {e}")
        return False
    finally:
        # Удаляем временный IL файл только при успешной компиляции
        # Оставляем его для отладки при ошибках
        if os.path.exists(il_file):
            print(f"IL файл сохранен как: {il_file}")
