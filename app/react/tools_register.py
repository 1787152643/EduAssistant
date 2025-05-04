import inspect
import functools

import json

from typing import Dict, Any, Callable, List, Type, Union, get_type_hints, get_origin, get_args
from datetime import datetime, date
from flask import jsonify, Response
from app.utils.logging import logger
from app.models.base import BaseModel
from app.models.user import User
from playhouse.shortcuts import model_to_dict

class ToolExecutionError(Exception):
    """Exception raised when a tool execution fails."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

# Tool registry
student_tools = {}
teacher_tools = {}
admin_tools = {}

def clean_datetime_fields(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """Recursively remove 'created_at' and 'updated_at' fields from dictionaries.
    
    Args:
        data: The data structure to clean, can be a dictionary, list, or other value.
        
    Returns:
        The cleaned data structure with datetime fields removed.
    """
    if isinstance(data, dict):
        # Create a new dict without datetime fields
        cleaned_dict = {}
        for key, value in data.items():
            # Skip created_at and updated_at fields
            if key in ('created_at', 'updated_at'):
                continue
            # Recursively clean nested structures
            cleaned_dict[key] = clean_datetime_fields(value)
        return cleaned_dict
    elif isinstance(data, list):
        # Recursively clean each item in the list
        return [clean_datetime_fields(item) for item in data]
    else:
        # Return non-dict, non-list values as is
        return data

def model_to_dict_cleaned(model):
    return clean_datetime_fields(model_to_dict(model, exclude=[User.password_hash], max_depth=1))

def result_model_to_dict(results):
    if isinstance(results, BaseModel):
        return model_to_dict_cleaned(results)
    elif isinstance(results, list):
        if len(results) > 0 and isinstance(results[0], BaseModel):  
            return [result_model_to_dict(result) for result in results]
        else:
            return results
    elif isinstance(results, dict):
        if len(results) > 0 and isinstance(next(iter(results.values())), BaseModel):
            return {k: result_model_to_dict(v) for k, v in results.items()}
        else:
            return results
    else:
        return results

def create_tool_executor(func: Callable) -> Callable:
    """Create a function that executes a service method with JSON/Dict parameters.
    
    Args:
        func: The function to execute
        
    Returns:
        A function that accepts JSON/Dict and calls the service method
    
    Raises:
        ToolExecutionError: If the function raises an exception
    """
    def executor(params: Dict[str, Any]) -> Any:
        # Call the method
        try:
            results = func(**params)
            # 如果返回的是BaseModel，则转换为字典
            '''if isinstance(results, BaseModel):
                return model_to_dict_cleaned(results)
            # 如果返回的是列表，则转换为字典列表
            elif isinstance(results, list):
                return [model_to_dict_cleaned(result) for result in results]
            elif isinstance(results, dict):
                return {k: model_to_dict_cleaned(v) for k, v in results.items()}
            # 如果返回的是其他类型，则直接返回
            return results'''
            return result_model_to_dict(results)
        except Exception as e:
            logger.exception(f"Error executing {func.__name__}")
            raise ToolExecutionError(f"Error executing {func.__name__}: {str(e)}", original_error=e)
    
    return executor


def _register_tool(func: Callable, tools: Dict[str, Any]):
    """Register a function to the tool registry."""
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func) or ""
    
    # Get the actual function from staticmethod
    actual_func = func.__func__ if isinstance(func, staticmethod) else func

    # Register the tool with metadata
    tools[func.__name__] = {
        "function": create_tool_executor(actual_func),
        "description": docstring,
        "parameters": {
            name: {
                "type": param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "any",
                "description": "" # You might want to parse docstring for param descriptions
            }
            for name, param in signature.parameters.items() if name != 'self'
        }
    }

def register_as_tool(roles: List[str]) -> Callable:
    """Register a function as a tool for the ReAct agent.

    Returns:
        object: 
    """
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        if "student" in roles:
            _register_tool(func, student_tools)
            logger.info(f"tool registered: {func.__name__} for student")
        if "teacher" in roles:
            _register_tool(func, teacher_tools)
            logger.info(f"tool registered: {func.__name__} for teacher")
        # admin can use all tools
        _register_tool(func, admin_tools)
        
        return wrapper
    
    return decorator
