from typer.testing import CliRunner
from pyassignmentgrader.cli import app
from pyassignmentgrader.utils import working_dir
import pytest
import pprint
import fspathtree
import os
import pathlib
import yaml



runner = CliRunner()


def test_help():
    results = runner.invoke(app, ["--help"])
    assert results.exit_code == 0
    assert "Usage: root [OPTIONS] COMMAND [ARGS]..." in results.stdout


@pytest.fixture(scope="function")
def setup_simple_grading_example(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("grading_example")
    with working_dir(tmpdir) as d:
        rubric = fspathtree.fspathtree()
        config = fspathtree.fspathtree()

        rubric["checks/0/tag"] = "P1"
        rubric["checks/0/desc"] = "Check for P1"
        rubric["checks/0/handler"] = "test -e tmp.txt"

        config["students/0/name"] = "jdoe"
        config["rubric"] = "HW-00-rubric.yml"
        config["results"] = "HW-00-results.yml"

        yaml.safe_dump(rubric.tree, pathlib.Path("HW-00-rubric.yml").open('w'))
        yaml.safe_dump(config.tree, pathlib.Path("HW-00-config.yml").open('w'))



    return tmpdir



@pytest.fixture(scope="function")
def setup_basic_grading_example_without_secondary_checks(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("grading_example")
    with working_dir(tmpdir) as d:
        rubric = fspathtree.fspathtree()
        config = fspathtree.fspathtree()

        rubric["workspace_directory"] = "workspace"
        rubric["checks/0/tag"] = "P1"
        rubric["checks/0/desc"] = "Check for P1"
        rubric["checks/0/handler"] = "test -e tmp.txt"
        rubric["checks/0/working_directory"] = "{name}"
        rubric["checks/1/tag"] = "P2"
        rubric["checks/1/desc"] = "Check for P2"
        rubric["checks/1/handler"] = "HW_00_checks:P2Check"
        rubric["checks/1/working_directory"] = "{name}"

        config["students/0/name"] = "jdoe"
        config["rubric"] = "HW-00-rubric.yml"
        config["results"] = "HW-00-results.yml"

        yaml.safe_dump(rubric.tree, pathlib.Path("HW-00-rubric.yml").open('w'))
        yaml.safe_dump(config.tree, pathlib.Path("HW-00-config.yml").open('w'))

        pathlib.Path("HW_00_checks.py").write_text('''
def P2Check():
  return {'result':False,'notes':[]}

        ''')

        pathlib.Path("workspace/jdoe").mkdir(parents=True)
        pathlib.Path("workspace/jdoe/tmp.txt").write_text("")



    return tmpdir


@pytest.fixture(scope="function")
def setup_basic_grading_example_with_secondary_checks(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("grading_example")
    with working_dir(tmpdir) as d:
        rubric = fspathtree.fspathtree()
        config = fspathtree.fspathtree()

        rubric["workspace_directory"] = "workspace"
        rubric["checks/0/tag"] = "P1"
        rubric["checks/0/desc"] = "Check for P1"
        rubric["checks/0/handler"] = "test -e tmp.txt"
        rubric["checks/0/working_directory"] = "{name}"
        rubric["checks/1/tag"] = "P2"
        rubric["checks/1/desc"] = "Check for P2"
        rubric["checks/1/handler"] = "HW_00_checks:P2Check"
        rubric["checks/1/working_directory"] = "{name}"
        rubric["checks/1/secondary_checks/weight"] = 0.5
        rubric["checks/1/secondary_checks/checks/0/tag"] = "P2.1"
        rubric["checks/1/secondary_checks/checks/0/desc"] = "Secondary check for P2"
        rubric["checks/1/secondary_checks/checks/0/weight"] = 1
        rubric["checks/1/secondary_checks/checks/0/handler"] = "pwd && ls && test -e tmp.txt"

        config["students/0/name"] = "jdoe"
        config["rubric"] = "HW-00-rubric.yml"
        config["results"] = "HW-00-results.yml"

        yaml.safe_dump(rubric.tree, pathlib.Path("HW-00-rubric.yml").open('w'))
        yaml.safe_dump(config.tree, pathlib.Path("HW-00-config.yml").open('w'))

        pathlib.Path("HW_00_checks.py").write_text('''
def P2Check():
  return {'result':False,'notes':[]}

        ''')

        pathlib.Path("workspace/jdoe").mkdir(parents=True)
        pathlib.Path("workspace/jdoe/tmp.txt").write_text("")



    return tmpdir





def test_grading_example(setup_simple_grading_example):
    with working_dir(setup_simple_grading_example) as d:
        results = runner.invoke(app, ["setup-grading-files","HW-00-config.yml"])

        assert pathlib.Path("HW-00-results.yml").exists()

        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))

        assert "jdoe" in grading_results
        assert grading_results['jdoe/checks/0/tag'] == "P1"
        assert grading_results['jdoe/checks/0/result'] == None


        rtn = runner.invoke(app, ["run-checks","HW-00-config.yml"])
        print(rtn.stdout)

        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))
        pprint.pprint(grading_results.tree)

        assert "jdoe" in grading_results
        assert grading_results['jdoe/checks/0/result'] == False




def test_updating_grading_results_file(setup_simple_grading_example):
    with working_dir(setup_simple_grading_example) as d:
        runner.invoke(app, ["setup-grading-files","HW-00-config.yml"])

        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))
        assert "jdoe" in grading_results
        assert len(grading_results['jdoe/checks']) == 1
        assert grading_results['jdoe/checks/0/tag'] == "P1"
        assert grading_results['jdoe/checks/0/result'] == None

        grading_results['jdoe/checks/0/result'] = True

        yaml.safe_dump( grading_results.tree, pathlib.Path("HW-00-results.yml").open('w') )


        runner.invoke(app, ["setup-grading-files","HW-00-config.yml"])
        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))
        assert "jdoe" in grading_results
        assert len(grading_results['jdoe/checks']) == 1
        assert grading_results['jdoe/checks/0/tag'] == "P1"
        assert grading_results['jdoe/checks/0/result'] == True


        grading_rubric = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-rubric.yml").open()))

        grading_rubric['/checks/1/tag'] = "P2"
        grading_rubric['/checks/1/desc'] = "Check foir P2"
        grading_rubric['/checks/1/handler'] = "test -d tmp.d"

        yaml.safe_dump( grading_rubric.tree, pathlib.Path("HW-00-rubric.yml").open('w') )


        rtn = runner.invoke(app, ["setup-grading-files","HW-00-config.yml"])

        assert rtn.exit_code == 1
        assert "already exists" in rtn.stdout
        assert "the `-x`" in rtn.stdout
        assert "the `-u`" in rtn.stdout

        rtn = runner.invoke(app, ["setup-grading-files","HW-00-config.yml", "-u"])
        print(rtn.stdout)

        assert rtn.exit_code == 0

        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))
        assert "jdoe" in grading_results
        assert len(grading_results['jdoe/checks']) == 2
        assert grading_results['jdoe/checks/0/tag'] == "P1"
        assert grading_results['jdoe/checks/0/result'] == True
        assert grading_results['jdoe/checks/1/tag'] == "P2"
        assert grading_results['jdoe/checks/1/result'] == None


def test_grading_simple_assignment(setup_basic_grading_example_without_secondary_checks):
    with working_dir(setup_basic_grading_example_without_secondary_checks) as d:
        rtn = runner.invoke(app, ["setup-grading-files","HW-00-config.yml"])
        print(rtn.stdout)
        assert rtn.exit_code == 0
        rtn = runner.invoke(app, ["run-checks","HW-00-config.yml"])
        print(rtn.stdout)
        if rtn.exception:
            print(rtn.exception)
        assert rtn.exit_code == 0
        rtn = runner.invoke(app, ["print-summary","HW-00-config.yml"])
        print(rtn.stdout)
        if rtn.exception:
            print(rtn.exception)
        assert rtn.exit_code == 0

        assert "Score: 50.00%" in rtn.stdout


        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))
        assert "jdoe" in grading_results
        assert len(grading_results['jdoe/checks']) == 2
        assert grading_results['jdoe/checks/0/tag'] == "P1"
        assert grading_results['jdoe/checks/0/result'] == True
        assert grading_results['jdoe/checks/1/result'] == False







def test_grading_simple_assignment_with_secondary_checks(setup_basic_grading_example_with_secondary_checks):
    with working_dir(setup_basic_grading_example_with_secondary_checks) as d:
        rtn = runner.invoke(app, ["setup-grading-files","HW-00-config.yml"])
        print(rtn.stdout)
        assert rtn.exit_code == 0
        rtn = runner.invoke(app, ["run-checks","HW-00-config.yml"])
        print(rtn.stdout)
        if rtn.exception:
            print(rtn.exception)
        assert rtn.exit_code == 0
        rtn = runner.invoke(app, ["print-summary","HW-00-config.yml"])
        print(rtn.stdout)
        if rtn.exception:
            print(rtn.exception)
        assert rtn.exit_code == 0
        return

        assert "Score: 75.00%" in rtn.stdout


        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))
        pprint.pprint(grading_results.tree)
        assert "jdoe" in grading_results
        assert len(grading_results['jdoe/checks']) == 2
        assert grading_results['jdoe/checks/0/tag'] == "P1"
        assert grading_results['jdoe/checks/0/result'] == True
        assert grading_results['jdoe/checks/1/result'] == False
        # assert grading_results['jdoe/checks/1/secondary_results/checks/0/result'] == True







