from contextlib import suppress
import inspect
import pyparsing as pp
from nodes import *


class PascalParser:
    def __init__(self):
        pass

    @staticmethod
    def parse(rule_name: str, parser: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        if getattr(parser, 'name', None) and parser.name.isidentifier():
            rule_name = parser.name
        if rule_name in ('bin_op',):
            def bin_op_parse_action(s, loc, tocs):
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
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            print(f"DEBUG: Rule '{rule_name}' -> Class '{cls}'")
            with suppress(NameError):
                try:
                    cls = eval(cls)
                    print(f"DEBUG: Found class {cls}")
                    if not inspect.isabstract(cls):
                        print(f"DEBUG: Class {cls} is not abstract, creating parse action")
                        def parse_action(s, loc, tocs):
                            print(f"DEBUG: Creating {cls.__name__} with tokens: {[str(t)[:30] for t in tocs]}")
                            try:
                                result = cls(*tocs)
                                print(f"DEBUG: Successfully created {cls.__name__}")
                                return result
                            except Exception as e:
                                print(f"DEBUG: Error creating {cls.__name__}: {e}")
                                raise

                        parser.setParseAction(parse_action)
                    else:
                        print(f"DEBUG: Class {cls} is abstract, skipping")
                except Exception as e:
                    print(f"DEBUG: Error evaluating class {cls}: {e}")