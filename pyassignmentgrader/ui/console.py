import urwid
import copy
import os
import yaml
import pprint
import pathlib

from enum import Enum
from ..handlers.python_function import *
from ..utils import ShellCheck, DirStack, get_working_directory_for_node


class GradingItemController:
    class ResultAction(Enum):
        PASS = 1
        FAIL = 2
        CLEAR = 3
        DO_NOT_CHANGE = 4

    def __init__(self, results, check_paths):
        self.results = results
        self.check_paths = check_paths

        self.root_working_directory = pathlib.Path(self.results.data.get("working_directory", ".")).absolute()

        self.view = GradingItemView()
        self.view.ResultSelectButtons[0].set_label("PASS")
        self.view.ResultSelectButtons[0].action = self.ResultAction.PASS
        self.view.ResultSelectButtons[1].set_label("FAIL")
        self.view.ResultSelectButtons[1].action = self.ResultAction.FAIL
        self.view.ResultSelectButtons[2].set_label("Clear")
        self.view.ResultSelectButtons[2].action = self.ResultAction.CLEAR
        self.view.ResultSelectButtons[3].set_label("Do not change")
        self.view.ResultSelectButtons[3].action = self.ResultAction.DO_NOT_CHANGE
        self.view.goto_next_imp = self.action_goto_next
        self.view.goto_next_ungraded_imp = self.action_goto_next_ungraded
        self.view.goto_prev_ungraded_imp = self.action_goto_prev_ungraded
        self.view.goto_prev_imp = self.action_goto_prev
        self.view.save_imp = self.action_save
        self.view.result_action_changed_imp = self.action_result_action_changed
        self.view.pull_from_handler_imp = self.action_pull_from_handler
        self.view.quit_imp = self.action_quit

        self.InfoText = self.view.InfoText
        self.ErrorText = self.view.ErrorText
        self.NotesText = self.view.NotesText

        self.current_check_path_index = -1
        self.current_check = None
        self.current_handler = None
        self.current_handler_output = None

        self.result_action = self.ResultAction.DO_NOT_CHANGE
        self.update_info_text()


    def action_quit(self):
        pass

    def action_result_action_changed(self, btn, state):
        if state:
            self.result_action = btn.action
            self.update_info_text()

    def action_pull_from_handler(self, btn):
        if self.current_handler_output:
            self.current_check["result"] = self.current_handler_output["result"]
            self.current_check["notes"] = copy.copy(
                self.current_handler_output["notes"]
            )
            self.setup_current_check()

    def action_save(self, btn):
        self.save_current_check()
        self.setup_current_check()

    def save_current_check(self):
        if self.current_check:
            self.current_check["notes"] = self.NotesText.get_edit_text().split("\n")
            if self.result_action == self.ResultAction.PASS:
                self.current_check["result"] = True
            if self.result_action == self.ResultAction.FAIL:
                self.current_check["result"] = False
            if self.result_action == self.ResultAction.CLEAR:
                self.current_check["result"] = None

    def action_goto_next(self, btn):
        self.increment_current_check()

    def action_goto_prev(self, btn):
        self.decrement_current_check()

    def action_goto_next_ungraded(self, btn):
        self.increment_current_check()
        while self.current_check is not None and self.current_check.get('result',None) is not None:
            self.increment_current_check()

    def action_goto_prev_ungraded(self, btn):
        self.decrement_current_check()
        while self.current_check is not None and self.current_check.get('result',None) is not None:
            self.decrement_current_check()


    def get_result_action_text(self, r):
        if r == self.ResultAction.PASS:
            return "Set to PASS"
        if r == self.ResultAction.FAIL:
            return "Set to FAIL"
        if r == self.ResultAction.CLEAR:
            return "Clear (set to None)"
        if r == self.ResultAction.DO_NOT_CHANGE:
            return "Do not change result"
        return f"Unknown result action {r}"

    def get_result_text(self, r):
        if r == True:
            return "PASS"
        if r == False:
            return "FAIL"
        if r == None:
            return "Result not set"

        return "UNKNOWN"


    def increment_current_check(self):
        self.save_current_check()
        if self.current_check_path_index < len(self.check_paths):
            self.current_check_path_index += 1
        self.setup_current_check()

    def decrement_current_check(self):
        self.save_current_check()
        if self.current_check_path_index > -1:
            self.current_check_path_index -= 1
        self.setup_current_check()

    def setup_current_check(self):
        self.ErrorText.set_text("")
        if self.current_check_path_index > -1 and self.current_check_path_index < len(
            self.check_paths
        ):
            current_check_path = self.check_paths[self.current_check_path_index]
            self.current_check = self.results.data[current_check_path]
        else:
            self.current_check = None

        for btn in self.view.ResultSelectButtons:
            if btn.action == self.ResultAction.DO_NOT_CHANGE:
                btn.toggle_state()

        os.chdir(self.root_working_directory)
        if self.current_check:
            wd = self.root_working_directory/get_working_directory_for_node(self.current_check)
            try:
                os.chdir(wd)
            except:
                self.ErrorText.set_text(f"Could not cd into directory '{wd}'")

            handler = self.current_check["handler"]
            self.current_handler_output = None
            if handler == "manual":
                pass
            elif ":" in handler:
                func = handler
                handler = PythonFunctionHandler(func, {})
                self.current_handler_output = handler.yield_next()
            else:
                cmd = handler
                cwd = self.current_check.get("working_directory", ".")
                handler = PythonFunctionHandler(
                    f"pyassignmentgrader.utils:ShellCheck(cmd='{cmd}')", {}
                )
                self.current_handler_output = handler.yield_next()

            self.update_notes_text()
        else:
            wd = self.root_working_directory
            os.chdir(wd)
        self.update_info_text()

    def update_notes_text(self):
        lines = self.current_check["notes"]
        self.NotesText.set_edit_text("\n".join(lines))

    def update_info_text(self):
        if self.current_check_path_index == -1:
            self.InfoText.set_text("Press Next to start")
            return
        if self.current_check_path_index == len(self.check_paths):
            self.InfoText.set_text("No more items to grade")
            return
        if self.current_check is None:
            self.InfoText.set_text("No information about current check")
            return

        lines = []
        student_name = self.check_paths[self.current_check_path_index].parts[1]
        lines.append(("default", "Student: "))
        lines.append(("good", student_name))
        lines.append("\n")
        lines.append("\n")
        lines.append(("default", "========="))
        lines.append("\n")
        lines.append("\n")
        lines.append("Current Result: ")
        lines.append(("emph1", self.get_result_text(self.current_check["result"])))
        lines.append("\n")
        lines.append("    New Result: ")
        lines.append(("emph2", self.get_result_action_text(self.result_action)))
        lines.append("\n")
        lines.append("\n")
        check_desc = "None"
        tag = self.current_check.get("tag", "NO TAG")
        desc = self.current_check.get("desc", "NO DESCRIPTION")
        lines.append(f"Check {self.current_check_path_index+1}/{len(self.check_paths)}")
        lines.append("\n")
        lines.append(("emph3", f"{tag} | {desc}"))
        lines.append("\n")
        lines.append("\n")
        lines.append(("default", "========="))
        lines.append("\n")
        lines.append("\n")
        lines.append("Handler: ")
        lines.append(
            (
                "emph2" if self.current_handler_output is None else "emph1",
                self.current_check["handler"],
            )
        )
        lines.append("\n")
        lines.append("RWD: ")
        lines.append(str(self.root_working_directory))
        lines.append("\n")
        lines.append("CWD: ")
        lines.append(str(pathlib.Path().absolute().relative_to(self.root_working_directory)))
        lines.append("\n")
        lines.append("\n")
        if self.current_handler_output:
            if "result" in self.current_handler_output:
                lines.append(("emph3","Result: "))
                lines.append(("emph3",str(self.current_handler_output["result"])))
                lines.append("\n")
                lines.append("\n")
            if "notes" in self.current_handler_output:
                lines.append("Notes: ")
                lines.append("\n")
                for note in self.current_handler_output["notes"]:
                    lines.append(note)
                    lines.append("\n")
                lines.append("\n")
            if "display" in self.current_handler_output:
                for key in self.current_handler_output["display"]:
                    lines.append(('emph1',key))
                    lines.append(": ")
                    lines.append(('emph2',str(self.current_handler_output["display"][key])))
                lines.append("\n")
                lines.append("\n")

        lines.append(("default", "========="))
        lines.append("\n")
        lines.append("\n")

        lines.append("Current Check:")
        lines.append("\n")
        lines.append(yaml.safe_dump(self.current_check.tree))
        lines.append("\n")
        lines.append("\n")

        self.InfoText.set_text(lines)


class GradingItemView:
    def goto_prev(self, *args, **kwargs):
        self.goto_prev_imp(*args, **kwargs)

    def goto_next(self, *args, **kwargs):
        self.goto_next_imp(*args, **kwargs)

    def goto_next_ungraded(self, *args, **kwargs):
        self.goto_next_ungraded_imp(*args, **kwargs)

    def goto_prev_ungraded(self, *args, **kwargs):
        self.goto_prev_ungraded_imp(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.save_imp(*args, **kwargs)

    def pull_from_handler(self, *args, **kwargs):
        self.pull_from_handler_imp(*args, **kwargs)

    def quit(self, *args, **kwargs):
        self.quit_imp(*args, **kwargs)
        raise urwid.ExitMainLoop()

    def result_action_changed(self, *args, **kwargs):
        self.result_action_changed_imp(*args, **kwargs)

    def __init__(self):

        self.ResultSelectButtons = []
        for i in range(4):
            urwid.RadioButton(
                self.ResultSelectButtons,
                "",
                on_state_change=self.result_action_changed,
            )
        self.ResultSelectContainer = urwid.Pile(
            urwid.SimpleListWalker(self.ResultSelectButtons)
        )
        self.ResultSelectArea = urwid.LineBox(
            self.ResultSelectContainer, title="Action", title_align="left"
        )

        self.NotesText = urwid.Edit(multiline=True, wrap="clip")
        self.NotesEditArea = urwid.LineBox(
            self.NotesText, title="Notes", title_align="left"
        )

        self.NavigateButtons = []
        self.NavigateButtons.append(urwid.Button("Prev", on_press=self.goto_prev))
        self.NavigateButtons.append(urwid.Button("Save", on_press=self.save))
        self.NavigateButtons.append(
            urwid.Button("Pull", on_press=self.pull_from_handler)
        )
        self.NavigateButtons.append(urwid.Button("Next", on_press=self.goto_next))
        self.NavigateContainer = urwid.GridFlow(
            [
                self.NavigateButtons[0],
                self.NavigateButtons[1],
                self.NavigateButtons[2],
                self.NavigateButtons[3],
            ],
            9,
            2,
            0,
            "center",
        )

        man_lines = []
        man_lines.append("Keybinding:")
        man_lines.append("  j           - down")
        man_lines.append("  k           - up")
        man_lines.append("  h           - left")
        man_lines.append("  l           - right")
        man_lines.append("  J/Tab       - select next area")
        man_lines.append("  K/Shift-Tab - select previous area")
        man_lines.append("  n           - goto next grading item")
        man_lines.append("  U           - Pull result from current handler output")
        man_lines.append("  p           - goto previous grading item")
        man_lines.append("  N           - goto next ungraded grading item")
        man_lines.append("  P           - goto previous ungraded grading item")
        man_lines.append("  Space/Enter - select")
        man_lines.append("")
        man_lines.append("Commands:")
        man_lines.append("  Prev  - goto previous grading item")
        man_lines.append("  Next  - goto next grading item")
        man_lines.append("  Pull  - pull results from handler output into the")
        man_lines.append("          current grading item.")

        man_lines = [ line for pair in zip(man_lines,["\n"]*len(man_lines)) for line in pair ]
        self.ManualText = urwid.Text(man_lines)
        self.ManualContainer  = urwid.Filler(self.ManualText,"bottom")
        self.ManualArea = urwid.LineBox(self.ManualText,title="Manual",title_align="left")


        # FIXME: we need to figure out a way to scroll the text in this section.
        self.InfoText = urwid.Text("Nothing to display")
        # self.InfoText = urwid.Edit()
        # self.InfoText.set_text = self.InfoText.set_edit_text
        # self.InfoText.set_text("Nothing to display")
        self.InfoDisplayContainer = urwid.Filler(self.InfoText, "top")
        self.InfoDisplayArea = urwid.LineBox(
            self.InfoDisplayContainer, title="Info", title_align="left"
        )
        self.ErrorText = urwid.Text("No errors")
        self.ErrorDisplayContainer = urwid.Filler(self.ErrorText, "top")
        self.ErrorDisplayArea = urwid.LineBox(
            self.ErrorDisplayContainer, title="Errors", title_align="left"
        )

        self.UILeftColumnItems = [self.InfoDisplayArea, self.ErrorDisplayArea]
        self.UIRightColumnItems = [
            self.ResultSelectArea,
            self.NavigateContainer,
            self.NotesEditArea,
            self.ManualArea,
        ]

        self.UILeftColumn = urwid.Pile(
            [
                ("weight", 0.8, urwid.Frame(self.UILeftColumnItems[0])),
                ("weight", 0.2, urwid.Frame(self.UILeftColumnItems[1])),
            ]
        )
        # self.UILeftColumn.keypress = lambda a,b: print("HI")
        self.UIRightColumnListWalker = urwid.SimpleListWalker(self.UIRightColumnItems)
        # We don't want the manual area to recieve focus, so if it does, we will set
        # set the focus to the top of the list.
        def skip_manual_item():
            if self.UIRightColumnListWalker.get_focus()[0] == self.UIRightColumnItems[-1]:
                self.UIRightColumnListWalker.set_focus(0)
        urwid.connect_signal( self.UIRightColumnListWalker, "modified", skip_manual_item )
        self.UIRightColumn = urwid.ListBox(
                self.UIRightColumnListWalker
        )

        self.TopLayout = urwid.Columns(
            [("weight", 0.6, self.UILeftColumn), ("weight", 0.4, self.UIRightColumn)]
        )
        self.TopLayout.focus_position = 1
        # add vi kkey-bindings
        for mapping in [
            ("j", "down"),
            ("k", "up"),
            ("h", "left"),
            ("l", "right"),
        ]:
            self.TopLayout._command_map[mapping[0]] = self.TopLayout._command_map[mapping[1]]



    def last_ui_area_position(self):
        p = 0
        try:
            while True:
                p = self.UIRightColumn.body.next_position(p)
        except:
            pass
        return p

    def focus_next_ui_area(self):
        try:
            next_position = self.UIRightColumn.body.next_position(
                self.UIRightColumn.focus_position
            )
        except:
            next_position = 0
        self.UIRightColumn.focus_position = next_position

    def focus_prev_ui_area(self):
        try:
            prev_position = self.UIRightColumn.body.prev_position(
                self.UIRightColumn.focus_position
            )
        except:
            prev_position = self.last_ui_area_position()
        self.UIRightColumn.focus_position = prev_position

    def get_ui(self):
        return self.TopLayout

    def input_filter(self, keys, raw):
        return keys

    def input_handler(self, key):
        
        if key == "q":
            self.quit()
        if key in ["tab", "J"]:
            self.focus_next_ui_area()
        if key in ["shift tab", "K"]:
            self.focus_prev_ui_area()
        if key in ["n"]:
            self.goto_next(None)
        if key in ["N"]:
            self.goto_next_ungraded(None)
        if key in ["p"]:
            self.goto_prev(None)
        if key in ["P"]:
            self.goto_prev_ungraded(None)
        if key in ["U"]:
            self.pull_from_handler(None)

    def get_palette(self):
        palette = [
            ("emph1", "dark magenta,bold", ""),
            ("emph2", "dark red,bold", ""),
            ("emph3", "dark green,bold", ""),
            ("good", "dark green", ""),
            ("ok", "dark magenta", ""),
            ("warning", "yellow", ""),
            ("bad", "dark red", ""),
            ("default", "default", ""),
        ]

        return palette
