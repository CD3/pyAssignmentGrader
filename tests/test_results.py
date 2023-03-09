from pyassignmentgrader.results import *
from pyassignmentgrader.rubric import *
from io import StringIO
import pytest


def test_loading_results_file():

    results = GradingResults()
    file = StringIO('''
jdoe:
  checks:
    - tag: Problem 1
    ''')

    newfile = StringIO()


    results.load(file)
    results.dump(newfile)

    assert newfile.getvalue().startswith("jdoe")

def test_scoring_results():

    results = GradingResults()
    file = StringIO('''
jdoe:
  checks:
    - tag: Problem 1
      desc: Checking that all temporary files have been removed
      weight: 1
      result: True
      notes:
        - Looks good
    - tag: Problem 2
      desc: Checking that script runs
      weight: 1
      result: False
      notes:
        - Could not run script with command `./myScript.sh`

    - tag: Problem 2
      desc: Checking that tmp.txt was created
      weight: 1
      result: NULL
      notes: []

    ''')


    results.load(file)
    warnings,errors = results.score()

    assert len(warnings) == 1
    assert warnings[0].startswith("WARNING")
    assert "jdoe" in warnings[0]
    assert "not been completed" in warnings[0]
    assert results.data["jdoe/available"] == 3
    assert results.data["jdoe/awarded"] == 1
    assert results.data["jdoe/score"] == pytest.approx(0.333,0.01)


    # for warning in warnings:
    #     print(warning)

    # pprint.pprint(results.data.tree)




def test_scoring_with_sub_checks_results():

    results = GradingResults()
    file = StringIO('''
jdoe:
  checks:
    - tag: Problem 1
      weight: 1
      result: True
    - tag: Problem 2
      weight: 1
      result: False
      secondary_checks:
        weight: 0.8
        checks:
            - result : True
              weight : 2
            - result:  False
              weight : 1

    - tag: Problem 3
      weight: 1
      result: True

    ''')


    results.load(file)
    warnings,errors = results.score()

    assert len(warnings) == 0
    assert results.data["jdoe/available"] == 3
    assert results.data["jdoe/awarded"] == pytest.approx( 2 + 0.8*0.666666, 0.01)
    assert results.data["jdoe/score"] == pytest.approx(0.66666 + 0.3333*0.8*0.666666,0.01)


    results = GradingResults()
    file = StringIO('''
jdoe:
  checks:
    - tag: Problem 1
      weight: 1
      result: True
    - tag: Problem 2
      weight: 1
      result: False
      secondary_checks:
        weight: 0.8
        checks:
            - result : True
              weight : 2
            - result:  False
              weight : 1
              secondary_checks:
                weight: 0.5
                checks:
                  - result: True
                    weight: 1
                  - result: False
                    weight: 1

    - tag: Problem 3
      weight: 1
      result: True

    ''')


    results.load(file)
    warnings,errors = results.score()

    assert len(warnings) == 0
    assert results.data["jdoe/available"] == 3
    assert results.data["jdoe/awarded"] == pytest.approx( 2 + 0.8*0.666666 + 0.8*0.3333*0.5*0.5, 0.01)
    assert results.data["jdoe/score"] == pytest.approx(0.66666 + 0.3333*0.8*(0.666666 + 0.33333*0.5*0.5),0.01)



def test_summarizing():

    results = GradingResults()
    file = StringIO('''
jdoe:
  checks:
    - tag: Problem 1
      desc: Check 1 for Problem 1
      weight: 1
      result: True
      notes:
        - Note 1 for Problem 1
    - tag: Problem 2
      desc: Check 1 for Problem 2
      weight: 1
      result: False
      secondary_checks:
        weight: 0.8
        checks:
            - result : True
              desc: Secondary check 1 for Problem 2
              weight : 2
            - result:  False
              desc: Secondary check 2 for Problem 2
              weight : 1
              secondary_checks:
                weight: 0.5
                checks:
                  - result: True
                    desc: Secondary check 2.1 for Problem 2
                    weight: 1
                  - result: False
                    desc: Secondary check 2.2 for Problem 2
                    weight: 1

    - tag: Problem 3
      weight: 1
      result: True
    ''')


    results.load(file)
    warnings,errors = results.score()
    lines = results.summary()

    assert len(lines) > 0
    assert lines[0] == "Grading report for 'jdoe':"

    # print()
    # print("\n".join(lines))


def test_adding_new_student_with_rubric():
    rubric = GradingRubric()
    rubric_file = StringIO('''
checks:
  - tag: Problem 1
    desc: Check 1
    weight: 1
    handler: manual
  - tag: Problem 2
    desc: Checking that script runs
    weight: 1
    handler: manual
  ''')


    rubric.load(rubric_file)

    results = GradingResults()

    results.add_student("jdoe",rubric)
    results.add_student("rshackleford",rubric)

    assert results.data['jdoe/checks/0/tag'] == "Problem 1"
    assert results.data['jdoe/checks/0/result'] == None
    assert results.data['rshackleford/checks/0/tag'] == "Problem 1"
    assert results.data['rshackleford/checks/0/result'] == None

    with pytest.raises(RuntimeError) as e_info:
        results.add_student("jdoe",rubric)

