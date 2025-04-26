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
        VAR = pp.CaselessKeyword("var").suppress()
        DOT = pp.Literal('.').suppress()
        PROCEDURE = pp.CaselessKeyword("procedure").suppress()
        FUNCTION = pp.CaselessKeyword("function").suppress()
        PROGRAM = pp.CaselessKeyword("Program").suppress()

        # Операторы
        ADD, SUB = pp.Literal('+'), pp.Literal('-')
        MUL, DIVISION = pp.Literal('*'), pp.Literal('/')
        MOD, DIV = pp.CaselessKeyword('mod'), pp.CaselessKeyword('div')
        AND = pp.Literal('and')
        OR = pp.Literal('or')
        GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
        NEQUALS, EQUALS = pp.Literal('!='), pp.Literal('=')
        ARRAY = pp.CaselessKeyword("array").suppress()
        OF = pp.CaselessKeyword("of").suppress()

        # Forward declarations
        expr = pp.Forward()
        stmt = pp.Forward()
        stmt_list = pp.Forward()
        
        # Новые forward declarations для устранения циклических зависимостей
        proc_decl = pp.Forward()
        func_decl = pp.Forward()
        var_decl_section = pp.Forward()
        decl_section = pp.Forward()

        # Идентификаторы и вызовы
        array_ident = ident + LBRACK + literal + RBRACK
        call = ident + LPAR + pp.Optional(expr + pp.ZeroOrMore(COMMA + expr)) + RPAR

        # Выражения
        group = (
            literal |
            call |
            array_ident |
            ident |
            LPAR + expr + RPAR
        )

        # Операции
        mult = pp.Group(group + pp.ZeroOrMore((MUL | DIVISION | MOD | DIV) + group)).setName('bin_op')
        add = pp.Group(mult + pp.ZeroOrMore((ADD | SUB) + mult)).setName('bin_op')
        compare1 = pp.Group(add + pp.Optional((GE | LE | GT | LT) + add)).setName('bin_op')
        compare2 = pp.Group(compare1 + pp.Optional((EQUALS | NEQUALS) + compare1)).setName('bin_op')
        logical_and = pp.Group(compare2 + pp.ZeroOrMore(AND + compare2)).setName('bin_op')
        logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('bin_op')

        expr << logical_or

        # Объявления переменных
        ident_list = ident + pp.ZeroOrMore(COMMA + ident)
        var_decl = ident_list + COLON + type_spec + SEMI
        array_decl = ident_list + COLON + ARRAY + LBRACK + literal + pp.Literal("..").suppress() + literal + RBRACK + OF + type_spec + SEMI

        # Изменим определение секции переменных
        var_decl_section = VAR + pp.OneOrMore(var_decl | array_decl)
        
        # Операторы
        assign = pp.Optional(array_ident | ident) + ASSIGN.suppress() + expr
        simple_stmt = assign | call

        for_body = stmt | pp.Group(SEMI).setName('stmt_list')
        for_cond = assign + pp.Keyword("to").suppress() + literal

        if_ = pp.Keyword("if").suppress() + expr + pp.Keyword("then").suppress() + stmt + pp.Optional(pp.Keyword("else").suppress() + stmt)
        while_ = pp.Keyword("while").suppress() + expr + pp.Keyword("do").suppress() + stmt
        repeat_ = pp.Keyword("repeat").suppress() + stmt_list + pp.Keyword("until").suppress() + expr
        for_ = pp.Keyword("for").suppress() + for_cond + pp.Keyword("do").suppress() + for_body

        compound_stmt = LBRACE + stmt_list + RBRACE

        stmt << (
            if_ |
            for_ |
            while_ |
            repeat_ |
            compound_stmt |
            (simple_stmt + SEMI)
        )

        stmt_list << pp.ZeroOrMore(stmt)

        # Параметры
        param_decl = ident_list + COLON + type_spec
        params = LPAR + pp.Optional(param_decl + pp.ZeroOrMore(SEMI + param_decl)) + RPAR
        
        # Forward declarations для устранения циклических зависимостей
        proc_decl = pp.Forward()
        func_decl = pp.Forward()
        decl_section = pp.Forward()
        
        # Определение тела процедуры и функции с учетом возможных вложенных объявлений
        proc_body = pp.Optional(decl_section) + compound_stmt
        proc_decl << PROCEDURE + ident + pp.Optional(params) + SEMI + proc_body + SEMI

        func_body = pp.Optional(decl_section) + compound_stmt
        func_decl << FUNCTION + ident + pp.Optional(params) + COLON + type_spec + SEMI + func_body + SEMI
        
        # Определяем каждое объявление как отдельный элемент 
        decl_item = var_decl_section | proc_decl | func_decl
        decl_section << pp.ZeroOrMore(decl_item)
        
        # Определение программы
        program_body = LBRACE + stmt_list + RBRACE + DOT
        program = PROGRAM + ident + SEMI + pp.Optional(decl_section) + program_body

        # Финальный парсер
        start = program.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

        # Регистрация парсеров
        for var_name, value in locals().copy().items():
            if isinstance(value, pp.ParserElement):
                PascalParser.parse(var_name, value)

        return start

    def parse(self, prog: str) -> StmtListNode:
        return self.parser.parseString(str(prog))[0]