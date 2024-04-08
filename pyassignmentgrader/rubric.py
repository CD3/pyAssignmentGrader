import fspathtree as ft
import yaml
import copy
import pathlib


class GradingRubric:
    '''
    A rubric that describes what checks are to be performed for an assignment.

    Spec

    checks:
      - tag: string
        desc: string
        weight: float
        handler: string
        working_directory: string
      - tag: string
        desc: string
        weight: float
        handler: string
        working_directory: string
        on_sucess:
            handler: string
        secondary_checks:
          weight: float
          checks:
            - tag: string
              desc: string
              weight: float
              handler: string
              working_directory: string
    '''
    def __init__(self):
        self.data = None

    def load(self, file:pathlib.Path):
        if hasattr(file,'read_text'):
            self.data = ft.fspathtree(yaml.safe_load(file.read_text()))
        elif hasattr(file,'read'):
            self.data = ft.fspathtree(yaml.safe_load(file.read()))

        if self.data is None:
            raise RuntimeError(f"Could not figure out how to read {file}. It does not appear to be a pathlib.Path or file handle.")



    def dump(self, file:pathlib.Path):
        text = yaml.safe_dump(self.data.tree, sort_keys=False)
        file.write_text(text)

    def make_empty_grading_results(self):
        results = ft.fspathtree()
        results.tree = copy.deepcopy(self.data.tree)
        def add_results_keys(list_of_checks):
            for check in list_of_checks:
                check['result'] = None
                check['notes'] = []
                if 'secondary_checks' in check:
                    add_results_keys(check['secondary_checks/checks'])

        add_results_keys(results["checks"])
        return results
