from contextlib import suppress
import pyparsing as pp
from nodes import *
import inspect

class PascalParser:
    def __init__(self):
        pass

    @staticmethod
    def parse(rule_name: str, parser: pp.ParserElement) -> None:
        """
        Метод для настройки обработчиков парсера.
        Преобразует токены в узлы AST-дерева.
        """
        if rule_name == rule_name.upper():
            return

        # Если у парсера есть имя, используем его
        if getattr(parser, 'name', None) and parser.name.isidentifier():
            rule_name = parser.name

        # Обработка бинарных операций
        if rule_name in ('bin_op',):
            def bin_op_parse_action(s, loc, tocs):
                """
                Обработчик для бинарных операций (например, 5 + 3).
                Создает узел BinOpNode.
                """
                node = tocs[0]
                if not isinstance(node, AstNode):
                    node = bin_op_parse_action(s, loc, node)
                for i in range(1, len(tocs) - 1, 2):
                    secondNode = tocs[i + 1]
                    if not isinstance(secondNode, AstNode):
                        secondNode = bin_op_parse_action(s, loc, secondNode)
                    node = BinOpNode(BinOp(tocs[i]), node, secondNode)
                return node

            parser.setParseAction(bin_op_parse_action)

        # Обработка других конструкций (if, while, assign и т.д.)
        else:
            # Преобразуем имя правила в имя класса узла AST-дерева
            cls_name = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls = eval(cls_name)  # Получаем класс узла по имени
                if not inspect.isabstract(cls):  # Проверяем, что класс не абстрактный
                    def parse_action(s, loc, tocs):
                        """
                        Обработчик для создания узлов AST-дерева.
                        """
                        return cls(*tocs)  # Создаем узел AST-дерева

                    parser.setParseAction(parse_action)