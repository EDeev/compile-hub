import asyncio, tempfile, os, shutil
import subprocess, uuid

from typing import Dict, Any, Optional


class CompilerBase:
    def __init__(self, language: str, timeout: int = 5):
        self.language = language
        self.timeout = timeout
        self.max_output_size = 1000000  # 1MB
        
    async def compile_and_run(self, code: str, input_data: str = "") -> Dict[str, Any]:
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="compile_")
            result = await self._execute(code, input_data, temp_dir)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Compilation error: {str(e)}"
            }
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    
    async def _execute(self, code: str, input_data: str, temp_dir: str) -> Dict[str, Any]:
        raise NotImplementedError("Subclass must implement _execute method")
    
    async def _run_process(self, cmd: list, input_data: str = "", 
                          cwd: Optional[str] = None) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=self.timeout
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace')[:self.max_output_size]
            stderr_str = stderr.decode('utf-8', errors='replace')[:self.max_output_size]
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr_str or "Execution failed",
                    "output": stdout_str
                }
            
            return {
                "success": True,
                "output": stdout_str,
                "error": stderr_str if stderr_str else None
            }
            
        except asyncio.TimeoutError:
            if 'process' in locals():
                process.kill()
            return {
                "success": False,
                "error": f"Execution timeout ({self.timeout}s exceeded)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
    
    def _sanitize_code(self, code: str) -> str:
        # Базовая очистка кода
        dangerous_patterns = [
            "system(", "exec(", "eval(", "__import__",
            "subprocess", "os.system", "popen"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return ""
        
        return code
    
    def _check_input_requirements(self, code: str) -> Dict[str, Any]:
        # Проверка требований к вводу
        input_keywords = {
            "cpp": ["cin", "scanf", "getline"],
            "python": ["input(", "raw_input"],
            "javascript": ["readline", "prompt"]
        }
        
        keywords = input_keywords.get(self.language, [])
        for keyword in keywords:
            if keyword in code:
                return {
                    "requiresInput": True,
                    "inputDescription": {
                        "variables": [
                            {
                                "name": "input",
                                "type": "string",
                                "description": "Program input data"
                            }
                        ]
                    }
                }
        
        return {"requiresInput": False}