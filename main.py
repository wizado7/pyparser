import os
from grammar import *
from semantic import *
from codegen import MSILCodeGenerator, compile_to_exe
from nodes import BlockNode


def main():
    """Демонстрация полного процесса компиляции Pascal программы"""
    
    # Простая Pascal программа с переменными и базовыми операциями
    prog = '''
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
      a := f(y);
      writeln(a);
    END.
    '''
        
    print("=== PASCAL КОМПИЛЯТОР ===")
    print("Исходная программа:")
    print(prog)
    print("=" * 50)
    
    try:
        # 1. Парсинг
        print("1. Парсинг...")
        parser = PascalGrammar()
        ast = parser.parse(prog)
        print("✓ Парсинг успешен")
        
        print("\nAST дерево:")
        try:
            print(f"DEBUG: AST type: {type(ast)}")
            print(f"DEBUG: AST children count: {len(ast.childs) if hasattr(ast, 'childs') else 'No childs'}")
            if hasattr(ast, 'childs'):
                for i, child in enumerate(ast.childs):
                    print(f"DEBUG: Child {i}: {type(child).__name__}")
                    if hasattr(child, 'childs') and len(child.childs) > 0:
                        print(f"  Sub-children: {[type(c).__name__ for c in child.childs]}")
                        # Проверяем BlockNode более детально
                        if isinstance(child, BlockNode):
                            print(f"  BlockNode details:")
                            print(f"    var_section: {type(child.var_section).__name__ if child.var_section else None}")
                            print(f"    declarations: {[type(d).__name__ for d in child.declarations]}")
                            print(f"    stmt_list: {type(child.stmt_list).__name__ if child.stmt_list else None}")
            
            for line in ast.tree:
                print(f"  {line}")
        except Exception as e:
            print(f"  Ошибка при выводе AST: {e}")
            print(f"  AST тип: {type(ast)}")
            print(f"  AST содержимое: {str(ast)}")
        
        # 2. Семантический анализ
        print("\n2. Семантический анализ...")
        analyzer = SemanticAnalyzer()
        analyzer.visit(ast)
        print(" Семантический анализ успешен")
        
        print("\nТаблица символов:")
        print(f"  {analyzer.current_scope}")
        
        # 3. Генерация MSIL кода
        print("\n3. Генерация MSIL кода...")
        codegen = MSILCodeGenerator()
        msil_code = codegen.generate_program(ast)
        print(" Генерация MSIL кода успешна")
        
        print("\nСгенерированный MSIL код:")
        print(msil_code)
        
        # 4. Сохранение MSIL в файл
        il_filename = "test_program.il"
        with open(il_filename, 'w') as f:
            f.write(msil_code)
        print(f"\n MSIL код сохранен в {il_filename}")
        
        # 5. Компиляция в исполняемый файл
        print("\n4. Компиляция в исполняемый файл...")
        success = compile_to_exe(msil_code, "test_program")
        
        if success:
            print(" Успешно скомпилировано в test_program.exe")
            
            # 6. Попытка запуска
            print("\n5. Запуск программы...")
            try:
                import subprocess
                result = subprocess.run(["test_program.exe"], 
                                      capture_output=True, text=True, timeout=5)
                print(f"✓ Программа выполнена. Код возврата: {result.returncode}")
                if result.stdout:
                    print(f"Вывод: {result.stdout}")
                if result.stderr:
                    print(f"Ошибки: {result.stderr}")
            except Exception as e:
                print(f"✗ Ошибка при запуске: {e}")
        else:
            print("✗ Ошибка компиляции в exe")
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()