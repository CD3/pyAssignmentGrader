import contextlib
import os
from pathlib import Path
import subprocess


@contextlib.contextmanager
def working_dir(new_dir: Path):
    old_dir = Path().absolute()
    new_dir = new_dir.absolute()
    try:
        os.chdir(new_dir)
        yield new_dir
    finally:
        os.chdir(old_dir)



def hello_world():
    return "Hello World"

def yield_hello_world():
    yield "Hello"
    yield "World"
    return


def ShellCheck(cmd,cwd):

    result = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',cwd=cwd)
    if result.stdout == "":
        result.stdout = f"command `{cmd}` exited with return code {result.returncode}"

    ret = {}
    ret["result"] = result.returncode == 0
    ret["notes"] = []
    ret["notes"].append("command output:")
    for line in result.stdout.split("\n"):
        ret["notes"].append(f"  {line}")


    return ret



