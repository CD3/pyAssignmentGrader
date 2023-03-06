import typer
import yaml
import sys
from rich import print
from pathlib import Path
from fspathtree import fspathtree
from pyassignmentgrader import *
from subprocess import run, PIPE, STDOUT

from .utils import *

app = typer.Typer()


def make_import_statement(func_spec: str):
    module_name, function_call = func_spec.split(":")
    function_toks = function_call.split('(')
    function_name = function_toks[0]
    import_statement = f"from {module_name} import {function_name}"
    return import_statement


def make_function_call(func_spec: str):
    module_name, function_call = func_spec.split(":")
    function_toks = function_call.split('(')
    function_name = function_toks[0]
    function_args = ("("+function_toks[1]) if len(function_toks) > 1 else "()"

    return function_name+function_args


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

    config = fspathtree(yaml.safe_load(config_file.open()))
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
    rubric.load(rubric_file.open())

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
        results.load(results_file.open())
        for student in config["students"]:
            results.update_student(student["name"], rubric)

    results.dump(results_file.open("w"))


    sys.path.append(str(config_file.absolute().parent))
    for preproc in config.get('preprocessing',[]):
        conf = {'type':None,'cmd':'','working_directory': Path().absolute()}

        if type(preproc) is str and ':' in preproc:
            conf['type'] = 'python'
            conf['cmd'] = preproc

        if type(preproc) is str and ':' not in preproc:
            conf['type'] = 'shell'
            conf['cmd'] = preproc

        if type(preproc) is fspathtree:
            conf = preproc.tree
            if 'type' not in conf:
                if ":" in conf['cmd']:
                    conf['type'] = 'python'
                else:
                    conf['type'] = 'shell'


        # expand to multiple commands if needed
        if '{name}' in conf['cmd']:
            confs = []
            for student in config["students"]:
                confs.append(copy.deepcopy(conf))
                confs[-1]['cmd'] = confs[-1]['cmd'].format(name=student['name'])
        else:
            confs = [conf]


        for conf in confs:
            if conf['type'] == 'python':
                exec( make_import_statement(conf['cmd'] ) )
                wd = Path(conf.get("working_directory",".")).absolute()
                with working_dir(wd):
                    eval(make_function_call(conf['cmd']))
            if conf['type'] == 'shell':
                print(f"[green]cmd[/green]: {conf['cmd']}")
                ret = run(conf['cmd'], shell=True,cwd=conf['working_directory'])
                if ret.returncode != 0:
                    print(f"[yellow]Preprocessing command `{conf['cmd']}` returned non-zero exist status.[/yellow]")



@app.command()
def write_condig_file(
    config_file: Path,
    overwrite: bool = typer.Option(
        False, "-x", help="Overwrite the results file if it already exists."
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

    yaml.safe_dump(data.tree, config_file.open("w"))

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

    yaml.safe_dump(data.tree, rubric_file.open("w"))


@app.command()
def run_checks(
    config_file: Path,
    force: bool = typer.Option(False, "-f", help="Force all checks to run."),
    working_directory: Path = typer.Option(
        Path(), "-d", help="The working directory to run tests from."
    ),
):
    """
    Run checks in a grading results file that have not been run yet.
    """
    if not config_file.exists():
        print(f"[bold red]Config file '{config_file}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    config = fspathtree(yaml.safe_load(config_file.open()))
    results_file = Path(config["results"])

    if not results_file.exists():
        print(f"[bold red]Results file '{results_file}' does not exists.[/bold red]")
        raise typer.Exit(1)
    results = GradingResults()
    results.load(results_file.open())
    results_file.with_suffix(results_file.suffix).write_text(results_file.read_text())

    sys.path.append(str(results_file.absolute().parent))

    with working_dir(working_directory) as assignment_dir:
        for student in results.data.tree:
            wd = Path(results.data.get(f"{student}/working_directory", ".")).absolute()
            with working_dir(wd) as student_dir:
                for key in list(
                    results.data.get_all_leaf_node_paths(
                        predicate=lambda p: len(p.parts) > 1
                        and p.parts[1] == student
                        and p.name == "result"
                    )
                ):
                    ret = run_check(results.data[key / ".."], force)
                    results.data[key] = ret["result"]
                    results.data[key / "../notes"].tree.clear()
                    # if len(ret['notes']) > 0:
                    # if key/'../notes' not in results.data:
                    for note in ret["notes"]:
                        results.data[key / "../notes"].tree.append(note)
    results.dump(results_file.open("w"))


def run_check(check_spec, force=False):
    wd = Path(check_spec.get("working_directory", ".")).absolute()
    check_name = f"{check_spec['tag']}: {check_spec['desc']}"
    if not force and check_spec["result"] is not None:
        print(f"[green]SKIPPING[/green] - {check_name} has already been ran.")
        print()
        return {"result": check_spec["result"], "notes": []}

    with working_dir(wd) as check_dir:
        handler = check_spec.get("handler", "manual")
        if handler == "manual":
            print(check_name)
            response = ""
            notes = []
            while response.lower() not in ["y", "n", "yes", "no"]:
                if len(response) > 0:
                    print(f"Unrecognized response [yellow]{response}[/yellow]")
                response = input("Did this check pass? [y/n] ")
            result = response.lower().startswith("y")

            response = input("Notes? [y/n] ")
            if response.lower().startswith("y"):
                response = input("Add note (enter 'EOF' to stop): ")
                while response.lower() != "eof":
                    notes.append(response)
                    response = input("Add note (enter 'EOF' to stop): ")

            return {"result": result, "notes": notes}

        if ":" in handler:
            print(f"Running check for {check_name}")
            print(f"Calling {handler}")
            exec(make_import_statement(handler))
            return eval(make_function_call(handler))

        try:
            print(f"Running check for {check_name}")
            print(f"Calling '{handler}' as shell command")
            print()
            ret = run(handler, shell=True, stdout=PIPE, stderr=STDOUT)
            if ret.returncode == 0:
                return {"result": True, "notes": []}
            else:
                notes = []
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

        return {"result": None, "notes": []}


@app.command()
def print_summary(results_file: Path):
    """ """
    if not results_file.exists():
        print(f"[bold red]Results file '{results_file}' does not exists.[/bold red]")
        raise typer.Exit(1)

    results = GradingResults()
    results.load(results_file.open())
    results.score()

    print("\n".join(results.summary()))
