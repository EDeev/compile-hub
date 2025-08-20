import os
from compilers.base import CompilerBase

class PythonCompiler(CompilerBase):
    def __init__(self):
        super().__init__("python", timeout=5)
        
    async def _execute(self, code: str, input_data: str, temp_dir: str):
        code = self._sanitize_code(code)
        if not code:
            return {
                "success": False,
                "error": "Code contains forbidden operations"
            }
        
        source_file = os.path.join(temp_dir, "main.py")
        
        # Записываем код
        with open(source_file, 'w') as f:
            f.write(code)
        
        # Проверка на требования ввода
        input_check = self._check_input_requirements(code)
        if input_check["requiresInput"] and not input_data:
            return {
                "success": False,
                "requiresInput": True,
                "inputDescription": input_check["inputDescription"],
                "error": "Program requires input"
            }
        
        # Запуск Python
        run_result = await self._run_process(
            ["python3", source_file],
            input_data=input_data,
            cwd=temp_dir
        )
        
        # Парсинг ошибок Python
        if not run_result["success"] and run_result.get("error"):
            error_lines = run_result["error"].split('\n')
            for i, line in enumerate(error_lines):
                if "line" in line:
                    try:
                        # Извлечение номера строки
                        parts = line.split(',')
                        for part in parts:
                            if "line" in part:
                                line_num = int(part.split()[-1])
                                # Поиск сообщения об ошибке
                                if i + 1 < len(error_lines):
                                    for j in range(i, len(error_lines)):
                                        if "Error:" in error_lines[j]:
                                            message = error_lines[j].strip()
                                            return {
                                                "success": False,
                                                "error": "Runtime error",
                                                "details": {
                                                    "line": line_num,
                                                    "message": message
                                                }
                                            }
                                break
                    except:
                        pass
        
        return run_result