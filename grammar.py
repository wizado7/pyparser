from pyparsing import pyparsing_common as ppc
from myParser import *

class PascalGrammar:
    def __init__(self):
        self.parser = self._make_parser()

    def _make_parser(self):
        # Базовые элементы языка
        num = pp.Regex(r'[+-]?\d+')  # Целые числа
        ident = ppc.identifier.setName('ident')  # Идентификаторы (имена переменных)

        # Типы данных
        INT = pp.CaselessKeyword("integer")
        CHAR = pp.CaselessKeyword("char")
        BOOL = pp.CaselessKeyword("boolean")
        type_spec = INT | CHAR | BOOL  # Типы переменных

        # Операторы и разделители
        LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
        SEMI, COLON = pp.Literal(';').suppress(), pp.Literal(':').suppress()
        ASSIGN = pp.Literal(':=')
        VAR = pp.CaselessKeyword("var").suppress()

        # Арифметические операторы
        ADD, SUB = pp.Literal('+'), pp.Literal('-')
        MUL, DIV = pp.Literal('*'), pp.Literal('/')

        # Логические операторы
        AND, OR = pp.Literal('and'), pp.Literal('or')
        GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
        EQUALS = pp.Literal('=')

        # Выражения
        expr = pp.Forward()
        term = num | ident | (LPAR + expr + RPAR)
        arith_expr = pp.infixNotation(term, [
            (MUL | DIV, 2, pp.opAssoc.LEFT),
            (ADD | SUB, 2, pp.opAssoc.LEFT),
        ])
        logical_expr = pp.infixNotation(arith_expr, [
            (GE | LE | GT | LT | EQUALS, 2, pp.opAssoc.LEFT),
            (AND | OR, 2, pp.opAssoc.LEFT),
        ])
        expr << logical_expr

        # Объявление переменных
        ident_list = ident + pp.ZeroOrMore(pp.Suppress(',') + ident)
        var_decl = ident_list + COLON + type_spec + SEMI
        vars_decl = VAR + pp.OneOrMore(var_decl)

        # Определяем stmt заранее
        stmt = pp.Forward()

        # Блок операторов
        stmt_block = pp.Keyword("begin").suppress() + pp.ZeroOrMore(stmt) + pp.Keyword("end").suppress()

        # Операторы
        assign = ident + ASSIGN + expr + SEMI
        if_stmt = (
                pp.Keyword("if").suppress() + expr +
                pp.Keyword("then").suppress() + (stmt | stmt_block) +  # Позволяем одиночный оператор или блок
                pp.Optional(pp.Keyword("else").suppress() + (stmt | stmt_block))
        )
        while_stmt = pp.Keyword("while").suppress() + expr + pp.Keyword("do").suppress() + (stmt | stmt_block)

        # Заполняем stmt
        stmt <<= assign | if_stmt | while_stmt | stmt_block

        stmt = assign | if_stmt | while_stmt
        stmt_list = pp.ZeroOrMore(stmt)

        # Тело программы
        body = pp.Keyword("begin").suppress() + stmt_list + pp.Keyword("end").suppress()

        # Программа
        program = pp.Keyword("Program").suppress() + ident + SEMI + vars_decl + body + pp.Literal('.').suppress()

        # Игнорирование комментариев
        start = program.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

        # Регистрация правил для AST
        for var_name, value in locals().copy().items():
            if isinstance(value, pp.ParserElement):
                PascalParser.parse(var_name, value)

        return start

    def parse(self, prog: str) -> StmtListNode:
        return self.parser.parseString(str(prog))[0]