from grammar import PascalGrammar
from nodes import ProgramNode

def main():
    prog = """
    Program Test;
    var
        a: integer;
    begin
        
        if a > 0 then
            a := a - 1;
    end.
    """

    g = PascalGrammar()

    try:
        parsed_prog = g.parse(prog)
        print("Парсинг завершён успешно!")
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return

    # Вывод AST-дерева
    if isinstance(parsed_prog, ProgramNode):
        print("\nAST-дерево:")
        for line in parsed_prog.tree:
            print(line)
    else:
        print("Ошибка: результат парсинга не является ProgramNode.")

if __name__ == "__main__":
    main()