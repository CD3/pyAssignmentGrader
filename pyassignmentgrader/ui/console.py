import urwid
from enum import Enum


class GradingItemController:
    class ResultAction(Enum):
        PASS = 1
        FAIL = 2
        CLEAR = 3
        DO_NOT_CHANGE = 4

    def __init__(self, results, check_paths):
        self.results = results
        self.check_paths = check_paths
        self.current_check_path_index = -1
        self.current_check = None
        self.InfoText = urwid.Text("Nothing to display")
        self.NotesText = urwid.Edit(multiline=True, wrap="clip")
        self.current_result = True
        self.current_notes = []
        self.current_handler_output = None
        self.result_action = self.ResultAction.DO_NOT_CHANGE
        self.update_info_text()

        self.goto_next(None)

    def quit(self):
        pass  # save state

    def result_action_changed(self, btn, state, user_data):
        self.result_action = user_data
        if state:
            self.result_action = user_data
            self.update_info_text()

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

    def get_result_text_style(self, r):
        if r == True:
            return "good"
        if r == False:
            return "bad"
        if r == None:
            return "ok"

        return "ok"

    def save(self, btn):
        pass

    def save_current_check(self):
        if self.current_check:
            self.current_check["notes"] = self.NotesText.get_edit_text().split()
            result = self.current_check["result"]
            if self.result_action == self.ResultAction.PASS:
                result = True
            if self.result_action == self.ResultAction.FAIL:
                result = False
            if self.result_action == self.ResultAction.CLEAR:
                result = None
            self.current_check["result"] = result

    def goto_next(self, btn):
        self.increment_current_check()

    def goto_prev(self, btn):
        self.decrement_current_check()

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
        if self.current_check_path_index > -1 and self.current_check_path_index < len(
            self.check_paths
        ):
            current_check_path = self.check_paths[self.current_check_path_index]
            self.current_check = self.results.data[current_check_path]
        else:
            self.current_check = None
        self.update_info_text()
        self.update_notes_text()

    def update_notes_text(self):
        if self.current_check_path_index == -1:
            return
        lines = self.current_check.get("notes", [])
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
        lines.append(('emph1',self.get_result_text(self.current_result)))
        lines.append("\n")
        lines.append("    New Result: ")
        lines.append(('emph2',self.get_result_action_text(self.result_action)))
        lines.append("\n")
        lines.append("\n")
        check_desc = "None"
        tag = self.current_check.get("tag", "NO TAG")
        desc = self.current_check.get("desc", "NO DESCRIPTION")
        lines.append(("emph3", f"{tag}|{desc}"))
        lines.append("\n")
        lines.append("\n")
        lines.append(("default", "========="))
        lines.append("\n")
        lines.append("\n")
        lines.append("Handler: ")
        lines.append(( "emph2" if self.current_handler_output is None else "emph1", self.current_check['handler']))

        # lines.append("")
        # lines.append("Current Notes:")
        # lines += self.current_notes
        # lines.append("")

        self.InfoText.set_text(lines)


class GradingItemView:
    def __init__(self, controller):

        self.controller = controller
        self.ResultSelectButtons = []
        for action in [
            controller.ResultAction.PASS,
            controller.ResultAction.FAIL,
            controller.ResultAction.CLEAR,
            controller.ResultAction.DO_NOT_CHANGE,
        ]:
            label = controller.get_result_action_text(action)
            urwid.RadioButton(
                self.ResultSelectButtons,
                label,
                on_state_change=controller.result_action_changed,
                user_data=action,
            )
        self.ResultSelectContainer = urwid.Pile(
            urwid.SimpleListWalker(self.ResultSelectButtons)
        )
        self.ResultSelectArea = urwid.LineBox(
            self.ResultSelectContainer, title="Action", title_align="left"
        )

        self.NotesEditArea = urwid.LineBox(
            self.controller.NotesText, title="Notes", title_align="left"
        )

        self.NavigateButtons = []
        self.NavigateButtons.append(urwid.Button("Prev", on_press=controller.goto_prev))
        self.NavigateButtons.append(urwid.Button("Save", on_press=controller.save))
        self.NavigateButtons.append(urwid.Button("Next", on_press=controller.goto_next))
        self.NavigateContainer = urwid.GridFlow(
            [self.NavigateButtons[0], self.NavigateButtons[1], self.NavigateButtons[2]],
            9,
            2,
            0,
            "center",
        )

        self.InfoDisplayContainer = urwid.Filler(self.controller.InfoText, "top")
        self.InfoDisplayArea = urwid.LineBox(
            self.InfoDisplayContainer, title="Info", title_align="left"
        )

        self.UILeftColumnItems = self.InfoDisplayArea
        self.UIRightColumnItems = [
            self.ResultSelectArea,
            self.NavigateContainer,
            self.NotesEditArea,
        ]

        # self.UILeftColumn = urwid.ListBox(
        #     urwid.SimpleListWalker(self.UILeftColumnItems)
        # )
        self.UILeftColumn = self.UILeftColumnItems
        self.UIRightColumn = urwid.ListBox(
            urwid.SimpleListWalker(self.UIRightColumnItems)
        )

        self.TopLayout = urwid.Columns(
            [("weight", 0.6, self.UILeftColumn), ("weight", 0.4, self.UIRightColumn)]
        )

    def get_ui(self):
        return self.TopLayout

    def input_handler(self, key):
        if key == "q":
            self.quit()

    def quit(self):
        self.controller.quit()
        raise urwid.ExitMainLoop()

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
