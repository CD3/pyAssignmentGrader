from typer.testing import CliRunner
from pyassignmentgrader.cli import app
from pyassignmentgrader.utils import working_dir
import pytest
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
def setup_grading_example(tmp_path_factory):
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



def test_grading_example(setup_grading_example):
    with working_dir(setup_grading_example) as d:
        results = runner.invoke(app, ["setup-grading-files","HW-00-config.yml"])

        assert pathlib.Path("HW-00-results.yml").exists()

        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))

        assert "jdoe" in grading_results
        assert grading_results['jdoe/checks/0/tag'] == "P1"
        assert grading_results['jdoe/checks/0/result'] == None


        results = runner.invoke(app, ["run-checks","HW-00-config.yml"])

        grading_results = fspathtree.fspathtree(yaml.safe_load(pathlib.Path("HW-00-results.yml").open()))

        assert "jdoe" in grading_results
        assert grading_results['jdoe/checks/0/result'] == False




def test_updating_grading_results_file(setup_grading_example):
    with working_dir(setup_grading_example) as d:
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


