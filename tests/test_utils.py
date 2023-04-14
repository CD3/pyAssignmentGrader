from pyassignmentgrader.utils import *
from .utils import *
from pathlib import Path
import pytest
import fspathtree
import yaml

def test_dirstack(setup_temporary_directory):
    with working_dir(setup_temporary_directory) as d:
        Path("level-1.d/level-2.d/level-3.d").mkdir(parents=True)
        cwd = Path().absolute()

        dstack = DirStack()

        assert os.getcwd() == str(cwd)

        dstack.push('level-1.d')
        assert os.getcwd() == str(cwd/'level-1.d')
        assert len(dstack.dirs) == 1

        dstack.push('level-2.d')
        assert os.getcwd() == str(cwd/'level-1.d/level-2.d')
        assert len(dstack.dirs) == 2

        with pytest.raises(FileNotFoundError):
            dstack.push('missing')

        assert len(dstack.dirs) == 2

        dstack.pop()
        assert os.getcwd() == str(cwd/'level-1.d')
        assert len(dstack.dirs) == 1

        dstack.push('level-2.d')
        assert os.getcwd() == str(cwd/'level-1.d/level-2.d')
        assert len(dstack.dirs) == 2

        dstack.pop()
        assert os.getcwd() == str(cwd/'level-1.d')
        assert len(dstack.dirs) == 1

        dstack.pop()
        assert os.getcwd() == str(cwd)
        assert len(dstack.dirs) == 0

        dstack.pop()
        assert os.getcwd() == str(cwd)
        assert len(dstack.dirs) == 0

        dstack.push('level-1.d/level-2.d')
        assert os.getcwd() == str(cwd/'level-1.d/level-2.d')
        assert len(dstack.dirs) == 1

        dstack.push('level-3.d')
        assert os.getcwd() == str(cwd/'level-1.d/level-2.d/level-3.d')
        assert len(dstack.dirs) == 2


        dstack.pop()
        assert os.getcwd() == str(cwd/'level-1.d/level-2.d')
        assert len(dstack.dirs) == 1

        dstack.pop()
        assert os.getcwd() == str(cwd)
        assert len(dstack.dirs) == 0

def test_working_directory_for_nodes(setup_temporary_directory):
    config = fspathtree.fspathtree()
    config['/working_directory'] = 'dir1'
    config['/jdoe/working_directory'] = 'jdoe'
    config['/jdoe/checks/0/working_directory'] = 'dir2'
    config['/jdoe/checks/0/result'] = True
    config['/jdoe/checks/1/result'] = True

    config['/rshack/working_directory'] = 'rshack'
    config['/rshack/checks/0/result'] = True
    config['/rshack/checks/1/working_directory'] = 'dir2'
    config['/rshack/checks/1/result'] = True

    with working_dir(setup_temporary_directory) as d:
        assert get_working_directory_for_node(config['/jdoe/checks/0/']) == "dir1/jdoe/dir2"
        assert get_working_directory_for_node(config['/jdoe/checks/']) == "dir1/jdoe"
        assert get_working_directory_for_node(config['/jdoe']) == "dir1/jdoe"

def test_context_object_for_nodes():
    pass
    txt = '''
jdoe:
    context:
      username: jdoe
      student_id: 1234
    checks:
      - name: check 1
        desc: Checking for file {file} in {username} ({student_id}) homework directory.
        context:
          file: file-1.txt
          directory: "{username}-{student_id}.d"
'''
    config = fspathtree.fspathtree(yaml.safe_load(txt))

    ctx = get_context_for_node(config['/jdoe/checks'])
    assert 'username' in ctx
    assert 'student_id' in ctx
    assert ctx['username'] == 'jdoe'
    assert ctx['student_id'] == 1234


    ctx = get_context_for_node(config['/jdoe/checks/0/'])
    assert 'username' in ctx
    assert 'student_id' in ctx
    assert 'file' in ctx
    assert 'directory' in ctx
    assert ctx['username'] == 'jdoe'
    assert ctx['student_id'] == 1234
    assert ctx['file'] == 'file-1.txt'
    assert ctx['directory'] == 'jdoe-1234.d'


def test_tree_rendering():
    txt = '''
jdoe:
    context:
      username: jdoe
      student_id: 1234
    checks:
      - name: check 1
        desc: Checking for file {file} in {username} ({student_id}) homework directory.
        context:
          file: file-1.txt
          directory: "{username}-{student_id}.d"
'''
    config = fspathtree.fspathtree(yaml.safe_load(txt))

    render_tree(config)

    assert config['/jdoe/checks/0/desc'] == "Checking for file file-1.txt in jdoe (1234) homework directory."
