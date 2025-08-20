import os
from compilers.base import CompilerBase

class JavaScriptCompiler(CompilerBase):
    def __init__(self):
        super().__init__("javascript", timeout=5)
        
    async def _execute(self, code: str, input_data: str, temp_dir: str):
        code = self._sanitize_code(code)
        if not code:
            return {
                "success": False,
                "error": "Code contains forbidden operations"
            }
        
        source_file = os.path.join(temp_dir, "main.js")
        
        # Обёртка для обработки ввода в Node.js
        if input_data:
            wrapped_code = f"""
            const readline = require('readline');
            const rl = readline.createInterface({{
                input: process.stdin,
                output: process.stdout
            }});

            let inputLines = """ + repr(input_data.strip().split("\n")) + """;
            let currentLine = 0;

            global.readLine = function() {{
                if (currentLine < inputLines.length) {{
                    return inputLines[currentLine++];
                }}
                return '';
            }};

            {code}

            rl.close();
            """
        else:
            wrapped_code = code
        
        # Записываем код
        with open(source_file, 'w') as f:
            f.write(wrapped_code)
        
        # Проверка на требования ввода
        input_check = self._check_input_requirements(code)
        if input_check["requiresInput"] and not input_data:
            return {
                "success": False,
                "requiresInput": True,
                "inputDescription": input_check["inputDescription"],
                "error": "Program requires input"
            }
        
        # Запуск Node.js
        run_result = await self._run_process(
            ["node", source_file],
            cwd=temp_dir
        )
        
        # Парсинг ошибок JavaScript
        if not run_result["success"] and run_result.get("error"):
            error_lines = run_result["error"].split('\n')
            for line in error_lines:
                if ".js:" in line:
                    try:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            line_num = int(parts[1])
                            # Поиск сообщения об ошибке
                            for err_line in error_lines:
                                if "Error:" in err_line or "error:" in err_line:
                                    message = err_line.strip()
                                    return {
                                        "success": False,
                                        "error": "Runtime error",
                                        "details": {
                                            "line": line_num,
                                            "message": message
                                        }
                                    }
                    except:
                        pass
        
        return run_result