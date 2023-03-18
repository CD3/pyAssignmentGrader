from pyassignmentgrader.handlers.python_function import *
import pytest



def test_python_function_name_parsing():

    result = PythonFunctionHandler.parsers.module_name.parse_string("my_python_module",parse_all=True)
    assert result[0] == "my_python_module"

    result = PythonFunctionHandler.parsers.module_name.parse_string("my_python.module",parse_all=True)
    assert result[0] == "my_python.module"

    result = PythonFunctionHandler.parsers.function_name.parse_string("my_python_function",parse_all=True)
    assert result[0] == "my_python_function"

    with pytest.raises(Exception):
        result = PythonFunctionHandler.parsers.function_name.parse_string("my_python.module",parse_all=True)

    result = PythonFunctionHandler.parsers.function_name.parse_string("my_python",parse_all=True)
    assert result[0] == "my_python"

    result = PythonFunctionHandler.parsers.function_signature.parse_string("(one,two,three)",parse_all=True)
    assert result[0] == "one,two,three"



    result = PythonFunctionHandler.parsers.function_signature.parse_string("(one,two,three)",parse_all=True)
    assert result[0] == "one,two,three"


    result = PythonFunctionHandler.parsers.function_specification.parse_string("my_python_module:my_python_function(one,two,three)",parse_all=True)
    assert "module_name" in result
    assert result['module_name'] == "my_python_module"
    assert "function_name" in result
    assert result['function_name'] == "my_python_function"
    assert "function_signature" in result
    assert result['function_signature'] == "one,two,three"

    result = PythonFunctionHandler.parsers.function_specification.parse_string("my_python_module:my_python_function",parse_all=True)
    assert "module_name" in result
    assert result['module_name'] == "my_python_module"
    assert "function_name" in result
    assert result['function_name'] == "my_python_function"
    assert 'function_signature' not in result







