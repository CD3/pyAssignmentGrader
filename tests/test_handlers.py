from pyassignmentgrader.handlers.python_function import *
from pyassignmentgrader.utils import working_dir
from .utils import setup_temporary_directory
import pytest
import os
import pathlib



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





def test_calling_builtins():

    handler = PythonFunctionHandler('pyassignmentgrader.utils:hello_world')
    result = handler.call()
    assert result == "Hello World"


    handler = PythonFunctionHandler('pyassignmentgrader.utils:yield_hello_world')
    result = handler.yield_next()
    expected = ["Hello","World"]
    while result is not None:
        assert result == expected.pop(0)
        result = handler.yield_next()

    handler = PythonFunctionHandler('pyassignmentgrader.utils:hello_world')
    result = handler.yield_next()
    while result is not None:
        print(result)
        result = handler.yield_next()


def test_shell_check_handler(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        pathlib.Path("tmp.txt").write_text("")

        handler = PythonFunctionHandler('pyassignmentgrader.utils:ShellCheck(cmd="test -e tmp.txt",cwd=".")')
        result = handler.yield_next()
        assert type(result) == dict
        assert 'result' in result
        assert 'notes' in result
        assert len(result['notes']) > 0
        assert result['result'] == True
        assert result['notes'][0] == "command output:"
        assert result['notes'][1] == "  command `test -e tmp.txt` exited with return code 0"


        handler = PythonFunctionHandler('pyassignmentgrader.utils:ShellCheck(cmd="test -e tmp2.txt",cwd=".")')
        result = handler.yield_next()
        assert type(result) == dict
        assert 'result' in result
        assert 'notes' in result
        assert len(result['notes']) > 0
        assert result['result'] == False
        assert result['notes'][0] == "command output:"
        assert result['notes'][1] == "  command `test -e tmp2.txt` exited with return code 1"


def test_calling_user_defined(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        pass
