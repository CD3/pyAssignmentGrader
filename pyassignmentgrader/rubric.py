import fspathtree as ft
import yaml
import copy


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

    def load(self, filehandle):
        self.data = ft.fspathtree(yaml.safe_load(filehandle))

    def dump(self, filehandle):
        text = yaml.safe_dump(self.data.tree, sort_keys=False)
        filehandle.write(text)

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
