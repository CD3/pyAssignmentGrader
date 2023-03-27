import contextlib
import os
from pathlib import Path
import subprocess
from fspathtree import fspathtree


@contextlib.contextmanager
def working_dir(new_dir: Path):
    old_dir = Path().absolute()
    new_dir = new_dir.absolute()
    try:
        os.chdir(new_dir)
        yield new_dir
    finally:
        os.chdir(old_dir)

class DirStack:
    def __init__(self):
        self.dirs = []

    def push(self,path):
        cwd = Path('.').absolute()
        path = Path(path).absolute()
        os.chdir(path)
        self.dirs.append(cwd)

    def pop(self):
        if len(self.dirs):
            path = self.dirs.pop()
            os.chdir(path)

def get_working_directory_for_node(node:fspathtree):
    '''
    Get the path for a working directory of a node
    in tree. For example:

    working_directory : dir1
    checks:
      - working_dir : dir2
        result: True

    The working directory for checks.result is dir1/dir2 and the absolute
    path returned will be root/"dir1/dir2"
    '''
    working_directories = []
    path_parts = node.path().parts[1:] # strip off the "/" part
    root = fspathtree(node.root)
    for i in range(len(path_parts)):
        p = Path('/'.join(path_parts[0:i]))/'working_directory'
        if str(p) in root:
            working_directories.append(root[p])
    if "working_directory" in node:
        working_directories.append(node['working_directory'])
    return "/".join(working_directories)

    


def hello_world():
    return "Hello World"

def yield_hello_world():
    yield "Hello"
    yield "World"
    return


def ShellCheck(cmd,cwd='.'):

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


def CheckFileExists(filename,cwd,aliases=[]):
    return CheckFileOrDirExists(filename,cwd,aliases,filetype='file')
def CheckDirectoryExists(dirname,cwd,aliases=[]):
    return CheckFileOrDirExists(dirname,cwd,aliases,filetype='dir')

def CheckFileOrDirExists(filename,cwd,aliases=[],filetype='file'):
    result = False
    notes = []
    with working_dir(Path(cwd)) as wd:
        if (wd/filename).exists():
            if filetype == 'file' and (wd/filename).is_file():
                result = True
            if filetype == 'dir' and (wd/filename).is_dir():
                result = True
            if filetype == 'link' and (wd/filename).is_symlink():
                result = True

        if result is False:
            notes.append(f"Did not find '{filename}' in '{cwd}'.")
            for alias in aliases:
                if (wd/alias).exists():
                    notes.append(f"Found '{alias}' instead, creating a link to expected filename: '{filename}' -> '{alias}'.")
                    (wd/filename).symlink_to(wd/alias)
                    result = True

            if result is False:
                notes.append(f"Found these files in '{cwd}':")
                for file in wd.glob("*"):
                    notes.append(f"  {file.relative_to(wd)}")



    return {'result':result,'notes':notes}

def ManualCheck(ctx):
    pass

def CheckFileContents(filename,cwd='.'):
    with working_dir(Path(cwd)) as wd:
        ret = {}
        ret['display'] = {}
        ret['display']['File Contents'] = "File not found."
        filepath = wd/filename
        if filepath.exists():
            ret['display']['File Contents'] = filepath.read_text()

    return ret


