import os
from compilers.base import CompilerBase

class CppCompiler(CompilerBase):
    def __init__(self):
        super().__init__("cpp", timeout=5)
        
    async def _execute(self, code: str, input_data: str, temp_dir: str):
        code = self._sanitize_code(code)
        if not code:
            return {
                "success": False,
                "error": "Code contains forbidden operations"
            }
        
        source_file = os.path.join(temp_dir, "main.cpp")
        exe_file = os.path.join(temp_dir, "main")
        
        # Записываем код
        with open(source_file, 'w') as f:
            f.write(code)
        
        # Компиляция
        compile_result = await self._run_process(
            ["g++", "-o", exe_file, source_file, "-std=c++17", "-O2", "-Wall"],
            cwd=temp_dir
        )
        
        if not compile_result["success"]:
            # Парсинг ошибок компиляции
            error_lines = compile_result["error"].split('\n')
            for line in error_lines:
                if "error:" in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        try:
                            line_num = int(parts[1])
                            message = ':'.join(parts[3:]).strip()
                            return {
                                "success": False,
                                "error": "Compilation error",
                                "details": {
                                    "line": line_num,
                                    "message": message
                                }
                            }
                        except:
                            pass
            
            return {
                "success": False,
                "error": compile_result["error"]
            }
        
        # Проверка на требования ввода
        input_check = self._check_input_requirements(code)
        if input_check["requiresInput"] and not input_data:
            return {
                "success": False,
                "requiresInput": True,
                "inputDescription": input_check["inputDescription"],
                "error": "Program requires input"
            }
        
        # Запуск
        run_result = await self._run_process(
            [exe_file],
            input_data=input_data,
            cwd=temp_dir
        )
        
        return run_result