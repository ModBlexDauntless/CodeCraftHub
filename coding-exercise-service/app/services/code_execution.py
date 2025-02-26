import subprocess
import tempfile
import os
import json
from datetime import datetime

class CodeExecutionService:
    def __init__(self, timeout=5):
        self.timeout = timeout
    
    def execute_python(self, code, input_data):
        """
        Execute Python code safely.
        
        Args:
            code (str): Python code to execute
            input_data (str): Input to the code
            
        Returns:
            dict: Execution result
        """
        try:
            # Prepare the code file with input
            with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
                f.write(code)
                f.write(f"\n\nprint({input_data})")
                temp_file = f.name
            
            # Execute the code with timeout
            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout.strip(),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "output": None,
                    "error": result.stderr.strip()
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": None,
                "error": "Execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }