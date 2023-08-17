import fspathtree as ft
import pprint
import yaml
import pathlib
from .rubric import GradingRubric
from .utils import render_tree

# import tomllib


class GradingResults:
    def __init__(self):
        self.data = ft.fspathtree()

    def load(self, file:pathlib.Path):
        if hasattr(file,'read_text'):
            self.data = ft.fspathtree(yaml.safe_load(file.read_text()))
            return
        if hasattr(file,'read'):
            self.data = ft.fspathtree(yaml.safe_load(file.read()))
            return

        raise RuntimeError(f"Could not figure out how to read {file}. It does not appear to be a pathlib.Path or file handle.")

    def dump(self, file:pathlib.Path):
        text = yaml.dump(self.data.tree, sort_keys=False)
        if hasattr(file,'write_text'):
            file.write_text(text)
            return
        if hasattr(file,'write'):
            file.write(text)
            return


        raise RuntimeError(f"Could not figure out how to write text to {file}. It does not appear to be a pathlib.Path or file handle.")


    def add_student(self, name: str, rubric: GradingRubric):
        if name not in self.data:
            self.data.tree[name] = rubric.make_empty_grading_results().tree
            # add the student name to a context for this tree so we can use it in
            # sub-nodes.
            self.data[name]['context/name'] = name
        else:
            raise RuntimeError(f"Student '{name}' is already in the grading results.")

    def update_student(self, name: str, rubric: GradingRubric):
        if name not in self.data:
            return self.add_student(name, rubric)

        result_keys = list(self.data[name].get_all_leaf_node_paths())
        empty_results = rubric.make_empty_grading_results()
        missing_keys = empty_results.get_all_leaf_node_paths( predicate = lambda p : p not in result_keys)
        for missing_key in missing_keys:
            self.data[ f"/{name}/{missing_key}"] = empty_results[f"{missing_key}"]

        self.data[name]['context/name'] = name

    # def get_all_check_keys(self):
    #     self.data.get_all_leaf_node_paths(
    #             predicate
    #             )


    def __score(self, list_of_checks):
        warnings = []
        errors = []
        total = 0
        awarded = 0
        for key in list_of_checks.get_all_leaf_node_paths(
            predicate=lambda p: len(p.parts) == 2 and p.name == "result",
        ):
            total += list_of_checks.get(key/"../weight",1)

        user = list_of_checks.path().parts[1]
        for i in range(len(list_of_checks)):
            check = list_of_checks[i]
            if "result" not in check:
                raise RuntimeError(
                    f"Check at {check.path()} does not contain a result."
                )
            if check["result"] is None:
                msg = f"WARNING: {user} has a check that has not been completed."
                msg += f"\n"
                msg += f"         desc: {check['desc']}"
                msg += f"\n"
                msg += f"         I am skipping the check which means that the computed score MAY BE TOO LOW."
                warnings.append(msg)
                continue

            weight = check.get("weight", 1)
            if check["result"] is True:
                awarded += weight
            elif check["result"] is False:
                if "secondary_checks" in check:
                    if "secondary_checks/checks" not in check:
                        raise RuntimeError(
                            f"Check at {check.path()} contains a secondary_check key, but there are no checks underneath it."
                        )
                    if "secondary_checks/weight" not in check:
                        raise RuntimeError(
                            f"Check at {check.path()} contains a secondary_check key, but there is no weight underneath it."
                        )
                    t, a, w, e = self.__score(check["secondary_checks/checks"])
                    warnings += w
                    errors += e
                    awarded += weight * check["secondary_checks/weight"] * a / t
            elif isinstance( check["result"], (int,float) ):
                awarded += weight*check["result"]
            else:
                raise RuntimeError(f"Unexpected result type {type(check['result'])}. Expected a bool, float, or None.")

        return total, awarded, warnings, errors


    def score(self):
        warnings = []
        errors = []
        for user in self.data.tree:
            checks = self.data[f"{user}/checks"]

            t, a, w, e = self.__score(checks)
            warnings += w
            errors += e

            checks["../available"] = t
            checks["../awarded"] = a
            checks["../score"] = a / t

        return warnings, errors

    def __checks_summary(self, list_of_checks, prefix=""):
        lines = []

        def add_line(text):
            lines.append(f"{prefix}{text}")

        for check in list_of_checks:
            tag = check.get("tag", "Check")
            desc = check.get("desc", "")
            add_line(f"{tag}: {desc}")

            weight = check.get("weight", 1)
            add_line(f"  weight: {weight}")

            if check["result"] is None:
                add_line(f"  result: Not Ran")
            elif check["result"] is True:
                add_line(f"  result: PASS")
            else:
                add_line(f"  result: FAIL")

            if "notes" in check:
                add_line(f"  notes:")
                for n in check["notes"]:
                    add_line(f"      {n}")


            if check['result'] == False and "secondary_checks" in check:
                add_line(f"  Secondary Checks:")
                add_line(f"    weight: {check['secondary_checks/weight']}")
                lines += self.__checks_summary(
                    check["secondary_checks/checks"], prefix + "    "
                )
        return lines

    def summary(self, prefix=""):
        lines = []

        def add_line(text):
            lines.append(f"{prefix}{text}")

        for user in self.data.tree:
            add_line(f"Grading report for '{user}':")
            checks = self.data[f"{user}/checks"]
            lines += self.__checks_summary(checks)

            # add_line(f"Points: {self.data[f'{user}/awarded']}")
            # add_line(f"Total: {self.data[f'{user}/available']}")
            add_line(f"Score: {self.data[f'{user}/score']*100:.2f}%")

        return lines
