from pyassignmentgrader.handlers.python_function import *
from pyassignmentgrader.utils import working_dir
from .utils import setup_temporary_directory
import pytest
import os
import pathlib
import sys


def test_python_function_name_parsing():

    result = PythonFunctionHandler.parsers.module_name.parse_string(
        "my_python_module", parse_all=True
    )
    assert result[0] == "my_python_module"

    result = PythonFunctionHandler.parsers.module_name.parse_string(
        "my_python.module", parse_all=True
    )
    assert result[0] == "my_python.module"

    result = PythonFunctionHandler.parsers.function_name.parse_string(
        "my_python_function", parse_all=True
    )
    assert result[0] == "my_python_function"

    with pytest.raises(Exception):
        result = PythonFunctionHandler.parsers.function_name.parse_string(
            "my_python.module", parse_all=True
        )

    result = PythonFunctionHandler.parsers.function_name.parse_string(
        "my_python", parse_all=True
    )
    assert result[0] == "my_python"

    result = PythonFunctionHandler.parsers.function_signature.parse_string(
        "(one,two,three)", parse_all=True
    )
    assert result[0] == "one,two,three"

    result = PythonFunctionHandler.parsers.function_signature.parse_string(
        "(one,two,three)", parse_all=True
    )
    assert result[0] == "one,two,three"

    result = PythonFunctionHandler.parsers.function_specification.parse_string(
        "my_python_module:my_python_function(one,two,three)", parse_all=True
    )
    assert "module_name" in result
    assert result["module_name"] == "my_python_module"
    assert "function_name" in result
    assert result["function_name"] == "my_python_function"
    assert "function_signature" in result
    assert result["function_signature"] == "one,two,three"

    result = PythonFunctionHandler.parsers.function_specification.parse_string(
        "my_python_module:my_python_function", parse_all=True
    )
    assert "module_name" in result
    assert result["module_name"] == "my_python_module"
    assert "function_name" in result
    assert result["function_name"] == "my_python_function"
    assert "function_signature" not in result


def test_calling_builtins():

    handler = PythonFunctionHandler("pyassignmentgrader.utils:hello_world()")
    result = handler.call()
    assert result == "Hello World"

    handler = PythonFunctionHandler("pyassignmentgrader.utils:yield_hello_world()")
    result = handler.yield_next()
    expected = ["Hello", "World"]
    while result is not None:
        assert result == expected.pop(0)
        result = handler.yield_next()

    handler = PythonFunctionHandler("pyassignmentgrader.utils:hello_world()")
    result = handler.yield_next()
    while result is not None:
        print(result)
        result = handler.yield_next()


def test_shell_check_handler(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        pathlib.Path("tmp.txt").write_text("")

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:ShellCheck(cmd="test -e tmp.txt",cwd=".")'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) > 0
        assert result["result"] == True
        assert result["notes"][0] == "command output:"
        assert (
            result["notes"][1]
            == "  command `test -e tmp.txt` exited with return code 0"
        )

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:ShellCheck(cmd="test -e tmp2.txt",cwd=".")'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) > 0
        assert result["result"] == False
        assert result["notes"][0] == "command output:"
        assert (
            result["notes"][1]
            == "  command `test -e tmp2.txt` exited with return code 1"
        )


def test_file_check_handler(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        pathlib.Path("tmp.txt").write_text("")

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:CheckFileExists(filename="tmp.txt",cwd=".")'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) == 0
        result = handler.yield_next()
        assert result is None

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:CheckFileExists(filename="tmp2.txt",cwd=".")'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) == 3
        assert result["result"] == False
        assert result["notes"][0] == "Did not find 'tmp2.txt' in '.'."
        assert result["notes"][1] == "Found these files in '.':"
        assert result["notes"][2] == "  tmp.txt"
        result = handler.yield_next()
        assert result is None

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:CheckFileExists(filename="tmp2.txt",cwd=".",aliases=["tmp.txt"])'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) > 0
        assert result["result"] == True
        assert result["notes"][0] == "Did not find 'tmp2.txt' in '.'."
        assert (
            result["notes"][1]
            == "Found 'tmp.txt' instead, creating a link to expected filename: 'tmp2.txt' -> 'tmp.txt'."
        )
        result = handler.yield_next()
        assert result is None

        assert pathlib.Path("tmp2.txt").is_symlink()


def test_dir_check_handler(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        pathlib.Path("tmp.d").mkdir()

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:CheckDirectoryExists(dirname="tmp.d",cwd=".")'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) == 0
        result = handler.yield_next()
        assert result is None

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:CheckDirectoryExists(dirname="tmp2.d",cwd=".")'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) == 3
        assert result["result"] == False
        assert result["notes"][0] == "Did not find 'tmp2.d' in '.'."
        assert result["notes"][1] == "Found these files in '.':"
        assert result["notes"][2] == "  tmp.d"
        result = handler.yield_next()
        assert result is None

        handler = PythonFunctionHandler(
            'pyassignmentgrader.utils:CheckDirectoryExists(dirname="tmp2.d",cwd=".",aliases=["tmp.d"])'
        )
        result = handler.yield_next()
        assert type(result) == dict
        assert "result" in result
        assert "notes" in result
        assert len(result["notes"]) > 0
        assert result["result"] == True
        assert result["notes"][0] == "Did not find 'tmp2.d' in '.'."
        assert (
            result["notes"][1]
            == "Found 'tmp.d' instead, creating a link to expected filename: 'tmp2.d' -> 'tmp.d'."
        )
        result = handler.yield_next()
        assert result is None

        assert pathlib.Path("tmp2.d").is_symlink()


def test_calling_user_defined(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        checks_file = pathlib.Path("Checks1.py").write_text(
            """
def MyCheck1():
    return {'result':True,'notes':[]}
def MyCheck2():
    yield {'intermediate_result' : True}

    yield {'result':False,'notes':['Doing itermediate checks']}

    yield {'result':True,'notes':[]}

    return
"""
        )
        sys.path.append(str(d.absolute()))

        handler = PythonFunctionHandler("Checks1:MyCheck1()")
        result = handler.yield_next()
        assert "result" in result
        assert "notes" in result
        assert result["result"]
        assert len(result["notes"]) == 0

        handler = PythonFunctionHandler("Checks1:MyCheck2()")
        result = handler.yield_next()
        assert "intermediate_result" in result
        assert "result" not in result
        assert "notes" not in result
        assert result["intermediate_result"]

        result = handler.yield_next()
        assert "intermediate_result" not in result
        assert "result" in result
        assert "notes" in result
        assert result["result"] == False
        assert len(result["notes"]) == 1

        result = handler.yield_next()
        assert "intermediate_result" not in result
        assert "result" in result
        assert "notes" in result
        assert result["result"] == True
        assert len(result["notes"]) == 0

        result = handler.yield_next()
        assert result is None

        sys.path.pop()


def test_passing_context_to_handler(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        checks_file = pathlib.Path("Checks2.py").write_text(
            """
def MyCheck1(arg):
   yield {'result':True,'notes':[],'argument':arg}
   return
"""
        )
        sys.path.append(str(d.absolute()))

        handler = PythonFunctionHandler('Checks2:MyCheck1("{name}")', {"name": "jdoe"})
        result = handler.yield_next()
        assert "result" in result
        assert "notes" in result
        assert "argument" in result
        assert result["result"]
        assert len(result["notes"]) == 0
        assert result["argument"] == "jdoe"

        sys.path.pop()


def test_passing_context_to_handler_function_call(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        checks_file = pathlib.Path("Checks3.py").write_text(
            """
def MyCheck1(arg):
   yield {'result':True,'notes':[],'ctx':arg}
   return
"""
        )
        sys.path.append(str(d.absolute()))

        handler = PythonFunctionHandler("Checks3:MyCheck1(ctx)", {"val1": 1})
        result = handler.yield_next()
        assert "result" in result
        assert "notes" in result
        assert "ctx" in result
        assert result["result"]
        assert len(result["notes"]) == 0
        assert type(result["ctx"]) is dict
        assert "val1" in result["ctx"]
        assert result["ctx"]["val1"] == 1

        sys.path.pop()


def test_error_handling():

    handler = PythonFunctionHandler("pyassignmentgrader.utils:hello_world")

    with pytest.raises(
        Exception,
        match="Could not import function 'helloworld' from module 'pyassignmentgrader.utils'.",
    ) as excinfo:
        handler = PythonFunctionHandler("pyassignmentgrader.utils:helloworld")

    with pytest.raises(
        Exception,
        match=r"Could not parse the function specification 'pyassignmentgrader.utils.hello_world\(\)': Expected.*char 36.*",
    ) as excinfo:
        handler = PythonFunctionHandler("pyassignmentgrader.utils.hello_world")
