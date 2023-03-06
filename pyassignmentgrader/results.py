import fspathtree as ft
import pprint
import yaml
from .rubric import GradingRubric

# import tomllib


class GradingResults:
    def __init__(self):
        self.data = ft.fspathtree()

    def load(self, filehandle):
        self.data = ft.fspathtree(yaml.safe_load(filehandle))

    def dump(self, filehandle):
        text = yaml.safe_dump(self.data.tree, sort_keys=False)
        filehandle.write(text)

    def add_student(self, name:str, rubric:GradingRubric):
        if name not in self.data:
            self.data.tree[name] = rubric.make_empty_grading_results().tree
            for key in self.data.get_all_leaf_node_paths(predicate = lambda p : len(p.parts) > 1 and p.parts[1] == name and p.name == "working_directory"):
                self.data[key] = self.data[key].format(name=name)
        else:
            raise RuntimeError(f"Student '{name}' is already in the grading results.")

    def __score(self, list_of_checks):
        warnings = []
        errors = []
        total = 0
        awarded = 0
        for key in list_of_checks.get_all_leaf_node_paths(
            transform=lambda p: str(p)[1:],
            predicate=lambda p: len(p.parts) == 3 and p.name == "weight",
        ):
            total += list_of_checks[key]

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

            weight = check.get("weight", 1)
            if check["result"] is True:
                awarded += weight
            else:
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

            if check["result"] is True:
                add_line(f"  result: PASS")
            else:
                add_line(f"  result: FAIL")

            if "secondary_checks" in check:
                add_line(f"  Secondary Checks:")
                add_line(f"    weight: {check['secondary_checks/weight']}")
                lines += self.__checks_summary(check['secondary_checks/checks'],prefix+"    ")
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
