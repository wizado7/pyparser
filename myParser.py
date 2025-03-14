import inspect
from contextlib import suppress
import pyparsing as pp
from nodes import *


class PascalParser:
    def __init__(self):
        pass

    @staticmethod
    def parse(rule_name: str, parser: pp.ParserElement) -> None:
        """Назначает обработчики, формирующие AST-дерево."""
        if rule_name == rule_name.upper():
            return  # Игнорируем полностью заглавные имена (типы данных, ключевые слова)

        # Если у парсера есть имя, используем его
        if getattr(parser, 'name', None) and parser.name.isidentifier():
            rule_name = parser.name

        # Обработка бинарных операций (арифметические, логические)
        if rule_name in ('arith_expr', 'logical_expr', 'bin_op'):
            def bin_op_parse_action(s, loc, tocs):
                if len(tocs) == 1:
                    return tocs[0]  # Один элемент — просто возвращаем его
                node = BinOpNode(BinOp(tocs[1]), tocs[0], tocs[2])
                for i in range(3, len(tocs), 2):
                    node = BinOpNode(BinOp(tocs[i]), node, tocs[i + 1])
                return node

            parser.setParseAction(bin_op_parse_action)

        # Обработка присваивания (:=)
        elif rule_name == 'assign':
            def assign_action(s, loc, tocs):
                return AssignNode(tocs[0], tocs[2])  # tocs[1] — это оператор ':='

            parser.setParseAction(assign_action)

        # Обработка оператора IF
        elif rule_name == 'if_stmt':
            def if_action(s, loc, tocs):
                cond = tocs[0]
                then_stmt = tocs[1]
                else_stmt = tocs[2] if len(tocs) > 2 else None
                return IfNode(cond, then_stmt, else_stmt)

            parser.setParseAction(if_action)

        # Обработка WHILE-цикла
        elif rule_name == 'while_stmt':
            def while_action(s, loc, tocs):
                return WhileNode(tocs[0], tocs[1])

            parser.setParseAction(while_action)

        # Обработка списка операторов (StmtListNode)
        elif rule_name == 'stmt_list':
            def stmt_list_action(s, loc, tocs):
                return StmtListNode(*tocs)

            parser.setParseAction(stmt_list_action)

        # Обработка объявления переменных (VarDeclNode)
        elif rule_name == 'var_decl':
            def var_decl_action(s, loc, tocs):
                return VarDeclNode(tocs[0], tocs[1])  # tocs[0] — список переменных, tocs[1] — тип

            parser.setParseAction(var_decl_action)

        # Обработка программы (ProgramNode)
        elif rule_name == 'program':
            def program_action(s, loc, tocs):
                return ProgramNode(tocs[0], tocs[1], tocs[2])

            parser.setParseAction(program_action)

        # Попытка автоматически привязать класс AST-узла
        else:
            class_name = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            cls = globals().get(class_name)
            if cls and inspect.isclass(cls) and not inspect.isabstract(cls):
                def parse_action(s, loc, tocs):
                    return cls(*tocs)

                parser.setParseAction(parse_action)
