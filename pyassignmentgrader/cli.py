import inspect
import sys
from pathlib import Path
from subprocess import PIPE, STDOUT, run

import typer
import yaml
from fspathtree import fspathtree
from rich import print

from pyassignmentgrader import *

from .ui import console as console_view
from .utils import *

app = typer.Typer()


def make_import_statement(func_spec: str):
    module_name, function_call = func_spec.split(":")
    function_toks = function_call.split("(")
    function_name = function_toks[0]
    import_statement = f"from {module_name} import {function_name}"
    import_statement = f"""
try:
    {import_statement}
except Exception as e:
    print("[red]There was a problem trying to import {function_name} from {module_name}.[/red]")
    print(f"[red]Error Message: {{e}}[/red]")
"""
    return import_statement


def make_function_call(func_spec: str):
    module_name, function_call = func_spec.split(":")
    function_toks = function_call.split("(")
    function_name = function_toks[0]
    if len(function_toks) > 1:
        function_args = "(" + function_toks[1]
    else:
        exec(make_import_statement(func_spec))
        function_args = str(eval(f"inspect.signature({function_name})"))

    return function_name + function_args


@app.command()
def setup_grading_files(
    config_file: Path,
    overwrite: bool = typer.Option(
        False, "-x", help="Overwrite the results file if it already exists."
    ),
    update: bool = typer.Option(
        False,
        "-u",
        help="Update the results file with missing checks. i.e. if the rubric has been updated since the results file was created.",
    ),
):
    """
    Setup the grading session described by CONFIG_FILE.

    CONFIG_FILE is a YAML file with keys defining the various files and users in for the session.

    example:

    users:
      - name: jdoe
      - name: rshackleford
    results: HW-01-results.yml
    rubric: HW-01-rubric.yml
    prepressing:
        - mkdir HW-01-grading
        - tar HW-01-submissions.tar.bz2
    """
    if not config_file.exists():
        print(f"[bold red]Config file '{config_file}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    config = fspathtree(yaml.safe_load(config_file.read_text()))
    results_file = Path(config["results"])
    rubric_file = Path(config["rubric"])

    if not overwrite and not update and results_file.exists():
        print(
            f"[bold red]Results file '{results_file}' already exists. Use the `-x` option to overwrite or the `-u` option to update.[/bold red]"
        )
        raise typer.Exit(code=1)

    if not rubric_file.exists():
        print(f"[bold red]Rubric file '{rubric_file}' does not exists.[/bold red]")
        raise typer.Exit(code=1)

    rubric = GradingRubric()
    rubric.load(rubric_file)

    if "students" not in config:
        print(
            f"[bold red]No studenst found in '{config_file}'. You need to add a 'students' section.[/bold red]"
        )
        raise typer.Exit(code=1)

    results = GradingResults()
    if overwrite or not results_file.exists():
        for student in config["students"]:
            results.add_student(student["name"], rubric)

    elif update:
        results.load(results_file)
        for student in config["students"]:
            results.update_student(student["name"], rubric)

    render_tree(results.data)
    results.dump(results_file)

    sys.path.append(str(config_file.absolute().parent))
    for preproc in config.get("preprocessing", []):
        conf = {"type": None, "cmd": "", "working_directory": Path().absolute()}

        if type(preproc) is str and ":" in preproc:
            conf["type"] = "python"
            conf["cmd"] = preproc

        if type(preproc) is str and ":" not in preproc:
            conf["type"] = "shell"
            conf["cmd"] = preproc

        if type(preproc) is fspathtree:
            conf = preproc.tree
            if "type" not in conf:
                if ":" in conf["cmd"]:
                    conf["type"] = "python"
                else:
                    conf["type"] = "shell"

        # expand to multiple commands if needed
        if "{name}" in conf["cmd"]:
            confs = []
            for student in config["students"]:
                confs.append(copy.deepcopy(conf))
                confs[-1]["cmd"] = confs[-1]["cmd"].format(name=student["name"])
        else:
            confs = [conf]

        for conf in confs:
            if conf["type"] == "python":
                exec(make_import_statement(conf["cmd"]))
                wd = Path(conf.get("working_directory", ".")).absolute()
                with working_dir(wd):
                    try:
                        eval(make_function_call(conf["cmd"]))
                    except Exception as e:
                        print(
                            f"[red]There was an error trying to evaluate function call referenced by '{conf['cmd']}'[/red]"
                        )
                        print(f"[red]Error Message: {e}[/red]")

            if conf["type"] == "shell":
                print(f"[green]cmd[/green]: {conf['cmd']}")
                ret = run(conf["cmd"], shell=True, cwd=conf["working_directory"])
                if ret.returncode != 0:
                    print(
                        f"[yellow]Preprocessing command `{conf['cmd']}` returned non-zero exist status.[/yellow]"
                    )


@app.command()
def write_example_config_file(
    config_file: Path,
    overwrite: bool = typer.Option(
        False, "-x", help="Overwrite the config file if it already exists."
    ),
):
    if not overwrite and config_file.exists():
        print(
            f"[bold red]Config file '{config_file}' already exists. Remove and run again, or use the `-x` option.[/bold red]"
        )
        return 1
    data = fspathtree()
    data["students/0/name"] = "jdoe"
    data["students/0/working_directory"] = "HW-01-jdoe"
    data["students/1/name"] = "rshackleford"
    data["students/1/working_directory"] = "HW-01-rshackleford"
    data["rubric_file"] = "HW-01-rubic.yml"
    data["results_file"] = "HW-01-result.yml"
    data["preprocessing/0"] = "mkdir HW-01-grading"
    data["preprocessing/1/cmd"] = "tar -xjf ../gradebook*tar.bz2"
    data["preprocessing/1/working_directory"] = "HW-01-grading"

    config_file.write_text(yaml.safe_dump(data.tree))


@app.command()
def write_example_rubric_file(
    rubric_file: Path,
    overwrite: bool = typer.Option(
        False, "-x", help="Overwrite the results file if it already exists."
    ),
):
    if not overwrite and rubric_file.exists():
        print(
            f"[bold red]Rubric file '{rubric_file}' already exists. Remove and run again, or use the `-x` option.[/bold red]"
        )
        return 1
    data = fspathtree()
    data["checks/0/tag"] = "Problem 1"
    data["checks/0/desc"] = "Checking that something is true..."
    data["checks/0/weight"] = 1
    data["checks/0/handler"] = "manual"
    data["checks/0/working_directory"] = "."
    data["checks/1/tag"] = "Problem 2"
    data["checks/1/desc"] = "Running command to check that something is true..."
    data["checks/1/weight"] = 1
    data["checks/1/handler"] = "test -f tmp.txt"
    data["checks/1/working_directory"] = "."
    data["checks/2/tag"] = "Problem 3"
    data[
        "checks/2/desc"
    ] = "Running python funcgtion to check that something is true..."
    data["checks/2/weight"] = 1
    data["checks/2/handler"] = "HW_01_checks:Problem3"
    data["checks/2/working_directory"] = "."

    rubric_file.write_text(yaml.safe_dump(data.tree))


@app.command()
def run_checks(
    config_file: Path,
    force: bool = typer.Option(False, "-f", help="Force all checks to run."),
    assignment_directory: Path = typer.Option(
        Path(), "-d", help="The working directory to run tests from."
    ),
    student: str = typer.Option(
        None, "--student", "-s", help="Only run checks for given student."
    ),
    tag: str = typer.Option(
        None, "--tag", "-t", help="Only run checks for checks with given tag."
    ),
    ui: str = typer.Option(
        "tui", "--user-interface", "-u", help="Select user interface to use."
    ),
):
    """
    Run checks in a grading results file that have not been run yet.
    """
    config_file = config_file.absolute()
    if not config_file.exists():
        print(f"[bold red]Config file '{config_file}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    config = fspathtree(yaml.safe_load(config_file.read_text()))
    results_file = Path(config["results"])

    if not results_file.exists():
        print(f"[bold red]Results file '{results_file}' does not exists.[/bold red]")
        raise typer.Exit(1)
    results = GradingResults()
    results.load(results_file)

    sys.path.append(str(results_file.absolute().parent))

    workspace_directory = assignment_directory / config.get("workspace_directory", ".")

    if ui == "cli":
        try:
            # with working_dir(workspace_directory):
            for student_name in results.data.tree:
                if student and student_name != student:
                    continue

                print()
                print()
                print(f"Grading assignment for {student_name}")

                wd = Path(
                    results.data.get(f"{student_name}/working_directory", ".")
                ).absolute()
                with working_dir(wd) as student_dir:
                    ctx = fspathtree()
                    ctx["student_name"] = student_name
                    ctx["student_dir"] = student_dir
                    ctx["list_of_checks"] = results.data[student_name]["checks"]
                    ctx["workspace_directory"] = config_file.parent / config.get(
                        "workspace_directory", "grading_workspace"
                    )
                    run_list_of_checks(
                        results.data[student_name]["checks"], tag, ctx, force
                    )

        except Exception as e:
            print("[red]An exception was thrown while trying to run checks.[/red]")
            print(f"[red]Error Message: {e}[/red]")
        finally:
            results.dump(results_file.open("w"))

    elif ui == "tui":
        current_directory = pathlib.Path().absolute()
        try:
            check_paths = list(
                sorted(
                    map(
                        lambda p: results.data[p / ".."].path(),
                        results.data.find("/*/checks/*/result"),
                    ),
                    key=lambda p: int(p.parts[3]),
                )
            )
            controller = console_view.GradingItemController(results, check_paths)
            view = controller.view

            loop = console_view.urwid.MainLoop(
                view.get_ui(),
                view.get_palette(),
                input_filter=view.input_filter,
                unhandled_input=view.input_handler,
            )
            loop.run()
        finally:
            os.chdir(current_directory)
            results.dump(results_file)

    else:
        print(f"[red]Unrecognized user interface '{ui}'[/red]")
        print(f"[red]Please pass 'cli' or 'tui'[/red]")
        raise typer.Exit(1)


def run_list_of_checks(list_of_checks, tag, ctx, force=False):
    for check in list_of_checks:
        if tag is not None and check.get("tag", "NO-TAG") != tag:
            continue
        wd = Path(check.get("working_directory", ".")).absolute()
        with working_dir(wd) as check_dir:
            print()
            ret = run_check(check, ctx, force)
            check["result"] = ret["result"]
            check["notes"] = ret["notes"]
            # check["notes"].tree.clear()
            # for note in ret["notes"]:
            #     check["notes"].tree.append(note)

            if ret["result"] is True:
                print("  [green]PASS[/green]")
            if ret["result"] is False:
                print("  [red]FAIL[/red]")
            if ret["result"] is None:
                print("  [yellow]NO RESULT[/yellow]")
            print("  NOTES:")
            for n in ret["notes"]:
                print("    ", n)

            if check["result"] is False and "secondary_checks" in check:
                wwd = Path(
                    check.get("secondary_checks/working_directory", ".")
                ).absolute()
                with working_dir(wwd) as secondary_checks_dir:
                    run_list_of_checks(check["secondary_checks/checks"], tag, ctx)


def run_check(check, ctx, force=False):
    check_name = f"{ctx['student_name']}>{check['tag']}: {check['desc']}"
    notes = []
    if not force and check["result"] is not None:
        print(f"[green]SKIPPING[/green] - {check_name} has already been ran.")
        return {"result": check["result"], "notes": notes}

    handler = check.get("handler", "manual")
    print(f"Running check for '{check_name}'")
    if handler == "manual":
        # run and return result of manual check
        print("Manual Check")
        response = ""
        while response.lower() not in ["y", "n", "yes", "no", "s", "skip"]:
            if len(response) > 0:
                print(f"Unrecognized response [yellow]{response}[/yellow]")
            response = input("Did this check pass? [y/n] ")
        if response.lower().startswith("s"):
            return {"result": None, "notes": notes}

        result = response.lower().startswith("y")

        if response[0].islower():
            response = input("Add note (enter 'EOF' to stop): ")
            while response.lower() != "eof":
                notes.append(response)
                response = input("Add note (enter 'EOF' to stop): ")

        return {"result": result, "notes": notes}

    if ":" in handler:
        # run and return result of a python function check
        if "{name}" in handler:
            handler = handler.format(name=check.path().parts[1])
        print(f"  Calling '{handler}' as Python function")
        exec(make_import_statement(handler))
        try:
            return eval(make_function_call(handler))
        except Exception as e:
            print(
                f"[red]There was an error trying to evaluate function call referenced by '{handler}'[/red]"
            )
            print(f"[red]Error Message: {e}[/red]")
            return {"result": None, "notes": notes}

    try:
        # run and return result of shell command
        print(f"  Calling '{handler}' as shell command")
        ret = run(handler, shell=True, stdout=PIPE, stderr=STDOUT)
        if ret.returncode == 0:
            return {"result": True, "notes": notes}
        else:
            notes.append("Command finished with a non-zero exit code.")
            notes.append(f"command: {handler}.")
            notes.append("command output:" + ret.stdout.decode("utf-8"))
            return {"result": False, "notes": notes}
    except Exception as e:
        print(f"Unrecognized handler '{handler}'.")
        print(
            "Expecting 'manual', a Python function (i.e. 'hw_01:P1'), or a shell command"
        )
        print("Tried to run handler as a shell command but raised an exception")
        print(f"Exception: {e}")
        return {"result": None, "notes": notes}

    return {"result": None, "notes": notes}


@app.command()
def print_summary(config_file: Path):
    """ """
    if not config_file.exists():
        print(f"[bold red]Config file '{config_file}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    config = fspathtree(yaml.safe_load(config_file.read_text()))
    results_file = Path(config["results"])

    if not results_file.exists():
        print(f"[bold red]Results file '{results_file}' does not exists.[/bold red]")
        raise typer.Exit(1)

    try:
        results = GradingResults()
        results.load(results_file)
        warnings, errors = results.score()
        for w in warnings:
            print(f"[yellow]{w}[/yellow]")
        for e in errors:
            print(f"[red]{e}[/red]")
        print("\n".join(results.summary()))

    except Exception as e:
        print("[red]An exception was thrown while trying to score results.[/red]")
        print(f"[red]Error Message: {e}[/red]")

    finally:
        pass


# @app.command()
# def merge_results(
#     source_results_file: Path, dest_results_file: Path,
#     output_file: Path = typer.Option(
#         None, "--output","-o", help="Output file name."
#     ),
#     overwrite: bool = typer.Option(
#         False, "-x", help="Overwrite the output file if it already exists."
#     ),
# ):
#     """
#     Merge results from source into results of destination.

#     If you make changes to a rubric, then you can use this file to move
#     the results of a partially/fully graded results file into the new
#     results file.

#     All leaf nodes found in source AND dest will be copied to dest.
#     """
#     if not source_results_file.exists():
#         print(
#             f"[bold red]Results file '{source_results_file}' does not exists.[/bold red]"
#         )
#         raise typer.Exit(1)
#     if not dest_results_file.exists():
#         print(
#             f"[bold red]Results file '{source_results_file}' does not exists.[/bold red]"
#         )
#         raise typer.Exit(1)

#     source = fspathtree(yaml.safe_load(source_results_file.read_text()))
#     dest = fspathtree(yaml.safe_load(source_results_file.read_text()))
