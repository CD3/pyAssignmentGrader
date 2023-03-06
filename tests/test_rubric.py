from pyassignmentgrader.rubric import *
from pyassignmentgrader.results import *
from io import StringIO
import pytest
import pprint
import yaml

def test_loading_rubric_file():
    rubric = GradingRubric()
    file = StringIO('''
checks:
  - tag: Problem 1
    desc: Checking that all temporary files have been removed
    weight: 1
    handler: manual
  - tag: Problem 2
    desc: Checking that script runs
    weight: 1
    handler: manual
  - tag: Problem 2
    desc: Checking that tmp.txt was created
    weight: 1
    handler: manual
    secondary_checks:
      weight: 0.8
      checks:
        - tag: Problem 2 - SC 1
          handler: manual
  ''')


    rubric.load(file)
    results = rubric.make_empty_grading_results()


def test_writing_results_file():
    rubric = GradingRubric()
    rubric_file = StringIO('''
checks:
  - tag: Problem 1
    desc: Checking that all temporary files have been removed
    weight: 1
    handler: manual
  - tag: Problem 2
    desc: Checking that script runs
    weight: 1
    handler: manual
  - tag: Problem 2
    desc: Checking that tmp.txt was created
    weight: 1
    handler: manual
    secondary_checks:
      weight: 0.8
      checks:
        - tag: Problem 2 - SC 1
          handler: manual
  ''')


    rubric.load(rubric_file)

    results_file = StringIO()
    yaml.safe_dump({'jdoe':rubric.make_empty_grading_results().tree}, results_file)

    results = GradingResults()
    results_file.seek(0)
    results.load(results_file)

    assert 'jdoe' in results.data
    assert results.data['jdoe/checks/0/tag'] == "Problem 1"
    assert results.data['jdoe/checks/0/desc'] == "Checking that all temporary files have been removed"
    assert results.data['jdoe/checks/0/weight'] == 1
    assert results.data['jdoe/checks/0/handler'] == "manual"
    assert results.data['jdoe/checks/0/notes'].tree == []
    assert results.data['jdoe/checks/0/result'] is None


