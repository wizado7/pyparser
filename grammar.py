from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from myParser import *

# Включаем поддержку Packrat парсинга для улучшения производительности
pp.ParserElement.enablePackrat()

# Класс описывающий грамматику языка Pascal
class PascalGrammar:
    def __init__(self):
        self.parser = self._make_parser()

    def _make_parser(self):
        # Базовые элементы
        num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
        str_ = pp.QuotedString("'", escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
        TRUE = pp.Literal('True')
        FALSE = pp.Literal('False')
        bool_val = FALSE | TRUE
        literal = num | str_ | bool_val
        ident = ppc.identifier.setName('ident')

        # Типы данных
        INT = pp.CaselessKeyword("integer")
        CHAR = pp.CaselessKeyword("char")
        BOOL = pp.CaselessKeyword("boolean")
        type_spec = INT | CHAR | BOOL

        # Символы и ключевые слова
        LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
        LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()
        LBRACE, RBRACE = pp.CaselessKeyword("begin").suppress(), pp.CaselessKeyword("end").suppress()
        SEMI, COMMA, COLON = pp.Literal(';').suppress(), pp.Literal(',').suppress(), pp.Literal(':').suppress()
        ASSIGN = pp.Literal(':=')
        VAR = pp.CaselessKeyword("var")
        DOT = pp.Literal('.').suppress()
        PROCEDURE = pp.CaselessKeyword("procedure")
        FUNCTION = pp.CaselessKeyword("function")
        PROGRAM = pp.CaselessKeyword("Program").suppress()
        TO = pp.CaselessKeyword("to")
        IF = pp.CaselessKeyword("if")
        THEN = pp.CaselessKeyword("then")
        ELSE = pp.CaselessKeyword("else")
        WHILE = pp.CaselessKeyword("while")
        DO = pp.CaselessKeyword("do")
        FOR = pp.CaselessKeyword("for")
        REPEAT = pp.CaselessKeyword("repeat")
        UNTIL = pp.CaselessKeyword("until")
        WRITELN = pp.CaselessKeyword("writeln")

        # Операторы
        ADD, SUB = pp.Literal('+'), pp.Literal('-')
        MUL, DIVISION = pp.Literal('*'), pp.Literal('/')
        MOD, DIV = pp.CaselessKeyword('mod'), pp.CaselessKeyword('div')
        AND = pp.CaselessKeyword('and')
        OR = pp.CaselessKeyword('or')
        GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
        NEQUALS, EQUALS = pp.Literal('<>'), pp.Literal('=')
        ARRAY = pp.CaselessKeyword("array")
        OF = pp.CaselessKeyword("of")

        # Forward declarations
        expr = pp.Forward()
        stmt = pp.Forward()
        stmt_list = pp.Forward()
        block = pp.Forward()

        # Идентификаторы и вызовы
        array_ident = ident + LBRACK + expr + RBRACK
        call = ident + LPAR + pp.Optional(expr + pp.ZeroOrMore(COMMA + expr)) + RPAR

        # Выражения
        group = (
            literal |
            call |
            array_ident |
            ident |
            LPAR + expr + RPAR
        )

        # Операции с правильным приоритетом
        factor = group
        term = pp.Group(factor + pp.ZeroOrMore((MUL | DIVISION | MOD | DIV) + factor)).setName('bin_op')
        simple_expr = pp.Group(term + pp.ZeroOrMore((ADD | SUB) + term)).setName('bin_op')
        relational = pp.Group(simple_expr + pp.Optional((GE | LE | GT | LT | EQUALS | NEQUALS) + simple_expr)).setName('bin_op')
        and_expr = pp.Group(relational + pp.ZeroOrMore(AND + relational)).setName('bin_op')
        or_expr = pp.Group(and_expr + pp.ZeroOrMore(OR + and_expr)).setName('bin_op')

        expr << or_expr

        # Объявления переменных
        ident_list = ident + pp.ZeroOrMore(COMMA + ident)
        var_decl = ident_list + COLON + type_spec + SEMI
        array_decl = ident_list + COLON + ARRAY + LBRACK + literal + pp.Literal("..").suppress() + literal + RBRACK + OF + type_spec + SEMI

        # Секция объявления переменных - исправлена
        var_section = VAR.suppress() + pp.OneOrMore(var_decl | array_decl)
        
        # Операторы
        assign = (array_ident | ident) + ASSIGN.suppress() + expr
        simple_stmt = assign | call
        writeln_stmt = WRITELN + LPAR + expr + RPAR

        # Условные и циклические операторы
        if_ = IF.suppress() + expr + THEN.suppress() + stmt + pp.Optional(ELSE.suppress() + stmt)
        while_ = WHILE.suppress() + expr + DO.suppress() + stmt
        repeat_ = REPEAT.suppress() + stmt_list + UNTIL.suppress() + expr
        
        # Цикл for
        for_init = ident + ASSIGN.suppress() + expr
        for_stmt = FOR.suppress() + for_init + TO.suppress() + expr + DO.suppress() + stmt

        # Составной оператор
        compound_stmt = LBRACE + stmt_list + RBRACE

        stmt << (
            if_ |
            for_stmt |
            while_ |
            repeat_ |
            compound_stmt |
            (simple_stmt + SEMI) |
            writeln_stmt
        )

        stmt_list << pp.ZeroOrMore(stmt)

        # Параметры процедур и функций
        param_decl = ident_list + COLON + type_spec
        params = LPAR + pp.Optional(param_decl + pp.ZeroOrMore(SEMI + param_decl)) + RPAR
        
        # Объявления процедур и функций - исправлены для правильного порядка
        procedure_decl = pp.Group(PROCEDURE + ident + pp.Optional(params) + SEMI + block + SEMI)
        function_decl = pp.Group(FUNCTION + ident + pp.Optional(params) + COLON + type_spec + SEMI + block + SEMI)
        
        # Блок с объявлениями и телом - исправлен для корректного парсинга
        block << pp.Optional(var_section) + pp.ZeroOrMore(procedure_decl | function_decl) + compound_stmt
        
        # Определение программы
        program = PROGRAM + ident + SEMI + block + DOT

        # Финальный парсер
        start = program.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

        # Регистрация парсеров
        for var_name, value in locals().copy().items():
            if isinstance(value, pp.ParserElement):
                print(f"Регистрируем парсер: {var_name}")
                PascalParser.parse(var_name, value)

        return start

    def parse(self, prog: str) -> StmtListNode:
        return self.parser.parseString(str(prog))[0]