"""
CoFound.ai Code Generator Tool

This module provides code generation capabilities for the developer agent.
It uses LLMs to generate, revise, and debug code based on task descriptions and feedback.
"""

from typing import Dict, List, Any, Optional


class CodeGenerator:
    """
    Tool for generating, revising, and debugging code using LLMs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the code generator.
        
        Args:
            config: Configuration settings for the code generator
        """
        self.config = config
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.2)
        # In a real implementation, this would set up API clients, etc.
        
    def generate_code(self, task_description: str, language: str, 
                     framework: str = "", existing_code: str = "", 
                     architecture_info: str = "") -> Dict[str, Any]:
        """
        Generate code based on task description and context.
        
        Args:
            task_description: Description of the task
            language: Programming language to use
            framework: Framework to use (default: "")
            existing_code: Existing codebase for context (default: "")
            architecture_info: Architecture information for context (default: "")
            
        Returns:
            Dictionary containing generated code and metadata
        """
        # In a real implementation, this would call the LLM API
        # For now, we'll return a simple example
        
        if language.lower() == "python":
            code = self._generate_python_sample(task_description, framework)
        elif language.lower() == "javascript":
            code = self._generate_javascript_sample(task_description, framework)
        else:
            code = f"// Generated code for {language}\n\n// Task: {task_description}\n\n"
            
        return {
            "code": code,
            "language": language,
            "framework": framework,
            "dependencies": self._extract_dependencies(code, language),
            "imports": self._extract_imports(code, language),
            "file_path": self._suggest_file_path(task_description, language, framework)
        }
    
    def revise_code(self, original_code: str, feedback: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revise code based on feedback.
        
        Args:
            original_code: Original code to revise
            feedback: Feedback for revision
            context: Additional context
            
        Returns:
            Dictionary containing revised code and changes
        """
        # In a real implementation, this would call the LLM API
        # For now, we'll simulate a simple revision
        
        language = context.get("language", "python")
        revised_code = f"{original_code}\n\n# Code revised based on feedback: {feedback}\n"
        
        changes = [{
            "type": "Revision",
            "description": f"Applied feedback: {feedback}"
        }]
        
        return {
            "code": revised_code,
            "language": language,
            "changes": changes,
            "file_path": context.get("file_path", "")
        }
    
    def debug_code(self, code: str, error_message: Optional[str], 
                  context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Debug code based on error message.
        
        Args:
            code: Code to debug
            error_message: Error message to fix
            context: Additional context
            
        Returns:
            Dictionary containing debugged code and fixes
        """
        # In a real implementation, this would call the LLM API
        # For now, we'll simulate a simple debug
        
        language = context.get("language", "python")
        
        if error_message:
            debugged_code = f"{code}\n\n# Fixed error: {error_message}\n"
            fixes = [{
                "type": "Bug fix",
                "description": f"Fixed error: {error_message}",
                "location": "unknown"
            }]
        else:
            debugged_code = f"{code}\n\n# General code improvements made\n"
            fixes = [{
                "type": "Improvement",
                "description": "General code improvements",
                "location": "unknown"
            }]
        
        return {
            "code": debugged_code,
            "language": language,
            "fixes": fixes,
            "file_path": context.get("file_path", "")
        }
    
    def _generate_python_sample(self, task_description: str, framework: str) -> str:
        """
        Generate sample Python code.
        
        Args:
            task_description: Description of the task
            framework: Framework to use
            
        Returns:
            Generated Python code
        """
        if "flask" in framework.lower():
            return (
                "from flask import Flask, request, jsonify\n"
                "\n"
                "app = Flask(__name__)\n"
                "\n"
                "@app.route('/api/data', methods=['GET'])\n"
                "def get_data():\n"
                "    \"\"\"API endpoint to get data\"\"\"\n"
                "    return jsonify({'message': 'Data retrieved successfully', 'data': [1, 2, 3]})\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    app.run(debug=True)\n"
            )
        elif "django" in framework.lower():
            return (
                "from django.http import JsonResponse\n"
                "from django.views import View\n"
                "\n"
                "class DataView(View):\n"
                "    def get(self, request):\n"
                "        \"\"\"API endpoint to get data\"\"\"\n"
                "        return JsonResponse({'message': 'Data retrieved successfully', 'data': [1, 2, 3]})\n"
            )
        else:
            return (
                "def process_data(data):\n"
                "    \"\"\"\n"
                f"    Process data for task: {task_description}\n"
                "    \n"
                "    Args:\n"
                "        data: Input data to process\n"
                "    \n"
                "    Returns:\n"
                "        Processed data\n"
                "    \"\"\"\n"
                "    result = []\n"
                "    for item in data:\n"
                "        result.append(item * 2)\n"
                "    return result\n"
                "\n"
                "def main():\n"
                "    data = [1, 2, 3, 4, 5]\n"
                "    processed_data = process_data(data)\n"
                "    print(f\"Processed data: {processed_data}\")\n"
                "\n"
                "if __name__ == \"__main__\":\n"
                "    main()\n"
            )
    
    def _generate_javascript_sample(self, task_description: str, framework: str) -> str:
        """
        Generate sample JavaScript code.
        
        Args:
            task_description: Description of the task
            framework: Framework to use
            
        Returns:
            Generated JavaScript code
        """
        if "express" in framework.lower():
            return (
                "const express = require('express');\n"
                "const app = express();\n"
                "const port = 3000;\n"
                "\n"
                "app.get('/api/data', (req, res) => {\n"
                "  res.json({ message: 'Data retrieved successfully', data: [1, 2, 3] });\n"
                "});\n"
                "\n"
                "app.listen(port, () => {\n"
                "  console.log(`Server listening at http://localhost:${port}`);\n"
                "});\n"
            )
        elif "react" in framework.lower():
            return (
                "import React, { useState, useEffect } from 'react';\n"
                "\n"
                "const DataComponent = () => {\n"
                "  const [data, setData] = useState([]);\n"
                "  const [loading, setLoading] = useState(true);\n"
                "\n"
                "  useEffect(() => {\n"
                "    const fetchData = async () => {\n"
                "      try {\n"
                "        const response = await fetch('/api/data');\n"
                "        const result = await response.json();\n"
                "        setData(result.data);\n"
                "      } catch (error) {\n"
                "        console.error('Error fetching data:', error);\n"
                "      } finally {\n"
                "        setLoading(false);\n"
                "      }\n"
                "    };\n"
                "\n"
                "    fetchData();\n"
                "  }, []);\n"
                "\n"
                "  if (loading) return <div>Loading...</div>;\n"
                "\n"
                "  return (\n"
                "    <div>\n"
                "      <h2>Data List</h2>\n"
                "      <ul>\n"
                "        {data.map((item, index) => (\n"
                "          <li key={index}>{item}</li>\n"
                "        ))}\n"
                "      </ul>\n"
                "    </div>\n"
                "  );\n"
                "};\n"
                "\n"
                "export default DataComponent;\n"
            )
        else:
            return (
                "/**\n"
                f" * Process data for task: {task_description}\n"
                " * @param {Array} data - Input data to process\n"
                " * @returns {Array} - Processed data\n"
                " */\n"
                "function processData(data) {\n"
                "  const result = [];\n"
                "  for (const item of data) {\n"
                "    result.push(item * 2);\n"
                "  }\n"
                "  return result;\n"
                "}\n"
                "\n"
                "function main() {\n"
                "  const data = [1, 2, 3, 4, 5];\n"
                "  const processedData = processData(data);\n"
                "  console.log(`Processed data: ${processedData}`);\n"
                "}\n"
                "\n"
                "main();\n"
            )
    
    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """
        Extract dependencies from code.
        
        Args:
            code: Generated code
            language: Programming language
            
        Returns:
            List of dependencies
        """
        # In a real implementation, this would analyze the code
        # For now, we'll return sample dependencies
        
        if language.lower() == "python":
            if "flask" in code.lower():
                return ["flask"]
            elif "django" in code.lower():
                return ["django"]
            else:
                return []
        elif language.lower() == "javascript":
            if "express" in code.lower():
                return ["express"]
            elif "react" in code.lower():
                return ["react", "react-dom"]
            else:
                return []
        else:
            return []
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """
        Extract imports from code.
        
        Args:
            code: Generated code
            language: Programming language
            
        Returns:
            List of imports
        """
        # In a real implementation, this would analyze the code
        # For now, we'll return sample imports
        
        if language.lower() == "python":
            if "flask" in code.lower():
                return ["from flask import Flask, request, jsonify"]
            elif "django" in code.lower():
                return ["from django.http import JsonResponse", "from django.views import View"]
            else:
                return []
        elif language.lower() == "javascript":
            if "express" in code.lower():
                return ["const express = require('express');"]
            elif "react" in code.lower():
                return ["import React, { useState, useEffect } from 'react';"]
            else:
                return []
        else:
            return []
    
    def _suggest_file_path(self, task_description: str, language: str, framework: str) -> str:
        """
        Suggest file path for generated code.
        
        Args:
            task_description: Description of the task
            language: Programming language
            framework: Framework to use
            
        Returns:
            Suggested file path
        """
        # In a real implementation, this would analyze the task
        # For now, we'll return sample file paths
        
        if language.lower() == "python":
            if "flask" in framework.lower():
                return "app.py"
            elif "django" in framework.lower():
                return "views.py"
            else:
                return "main.py"
        elif language.lower() == "javascript":
            if "express" in framework.lower():
                return "server.js"
            elif "react" in framework.lower():
                return "DataComponent.jsx"
            else:
                return "main.js"
        else:
            return f"main.{language.lower()}" 