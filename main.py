import os
from grammar import *
from semantic import *


def main():
    # Исходный пример - процедура с параметром
    prog1 = '''
    Program t;
    procedure p(a: integer);
    var A : integer;
    begin
    A:=1;
    g:=a;
    end;    
    BEGIN    
    g:=1;
    p(10);
    END.
    '''
    
    # Пример 2 - модифицированный для более строгого соответствия Pascal
    prog2 = '''
    Program n;
    var 
      x, y, a : integer;
      
    function f(n: integer): integer;
    begin
      f := n + 1;
    end;

    procedure outer;
    var 
      b : integer;
    begin
      b := 5;
      a := b + 10;
      x := a * 2;
      y := f(a);
    end;

    BEGIN
      x := 1;
      y := 2;
    END.
    '''
    
    # Пример 3 - вложенная функция с рекурсией
    prog3 = '''
    Program f;
    var a, b, c : char;
    BEGIN
    a := '1';
    b := '1';
    c := a + b;
    END.
    '''
    
    # Пример 4 - работа с массивами
    prog4 = '''
    Program arrays;
    BEGIN
    END.
    '''
    
    # Пример 5 
    prog5 = '''
    Program complex;
    BEGIN
    END.
    '''
    
    g = PascalGrammar()
    
    print("\n==== Тестирование примера 1 ====")
    try:
        ast1 = g.parse(prog1)
        print("AST для примера 1:")
        print(*ast1.tree, sep=os.linesep)
        symb_table_builder = SemanticAnalyzer()
        symb_table_builder.visit(ast1)
        print("Семантический анализ для примера 1 успешно завершен")
    except Exception as e:
        print(f"Ошибка при обработке примера 1: {e}")
    
    print("\n==== Тестирование примера 2 ====")
    try:
        ast2 = g.parse(prog2)
        print("AST для примера 2:")
        print(*ast2.tree, sep=os.linesep)
        symb_table_builder = SemanticAnalyzer()
        symb_table_builder.visit(ast2)
        print("Семантический анализ для примера 2 успешно завершен")
    except Exception as e:
        print(f"Ошибка при обработке примера 2: {e}")
    
    print("\n==== Тестирование примера 3 ====")
    try:
        ast3 = g.parse(prog3)
        print("AST для примера 3:")
        print(*ast3.tree, sep=os.linesep)
        symb_table_builder = SemanticAnalyzer()
        symb_table_builder.visit(ast3)
        print("Семантический анализ для примера 3 успешно завершен")
    except Exception as e:
        print(f"Ошибка при обработке примера 3: {e}")
    
    print("\n==== Тестирование примера 4 ====")
    try:
        ast4 = g.parse(prog4)
        print("AST для примера 4:")
        print(*ast4.tree, sep=os.linesep)
        symb_table_builder = SemanticAnalyzer()
        symb_table_builder.visit(ast4)
        print("Семантический анализ для примера 4 успешно завершен")
    except Exception as e:
        print(f"Ошибка при обработке примера 4: {e}")
    
    print("\n==== Тестирование примера 5 ====")
    try:
        ast5 = g.parse(prog5)
        print("AST для примера 5:")
        print(*ast5.tree, sep=os.linesep)
        symb_table_builder = SemanticAnalyzer()
        symb_table_builder.visit(ast5)
        print("Семантический анализ для примера 5 успешно завершен")
    except Exception as e:
        print(f"Ошибка при обработке примера 5: {e}")


if __name__ == "__main__":
    main()