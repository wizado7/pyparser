class Symbol:
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name


class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return f'<{self.name}:{self.type}>'


class ArraySymbol(Symbol):
    def __init__(self, name, type, start, end):
        super().__init__(name, type)
        self.start = start
        self.end = end

    def __str__(self):
        return f'<{self.name}:{self.type}[{self.start}..{self.end}]>'


class ProcedureSymbol(Symbol):
    def __init__(self, name, params=None):
        super().__init__(name)
        self.params = params if params is not None else []

    def __str__(self):
        param_list = ', '.join(str(p) for p in self.params)
        return f'<procedure {self.name}({param_list})>'


class FunctionSymbol(Symbol):
    def __init__(self, name, params=None, return_type=None):
        super().__init__(name, return_type)
        self.params = params if params is not None else []

    def __str__(self):
        param_list = ', '.join(str(p) for p in self.params)
        return f'<function {self.name}({param_list}):{self.type}>'


class BuiltinFunction(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name


class BlockSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return f'{self.name}'