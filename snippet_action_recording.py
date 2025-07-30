from talon import actions, Context

from .basic_action_recorder import recording_context, temporarily_stop_recording, resume_recording, recorder, history, RECORDING_TAG_NAME

vscode_recording_context = Context()
vscode_recording_context.matches = r"""app: vscode
tag: user.""" + RECORDING_TAG_NAME

def compute_snippet_description(name: str):
    return f"Insert Snippet: {name}"

def compute_snippet_with_phrase_description(name: str, phrase: str):
    return f"Insert Snippet ({name}) with phrase: {phrase}"

def compute_snippet_next_description():
    return "Go to next snippet placeholder"

@vscode_recording_context.action_class("user")
class VsCodeActions:
    def move_cursor_to_next_snippet_stop():
        history_was_recording = temporarily_stop_recording()
        actions.next()
        resume_recording(history_was_recording)
        recorder.record_basic_action('user.move_cursor_to_next_snippet_stop', [])
        history.record_action(compute_snippet_next_description())

@recording_context.action_class("user")
class UserActions:
    def move_cursor_to_next_snippet_stop():
        if recorder.is_temporarily_rejecting_actions():
            actions.next()
        else:
            history_was_recording = temporarily_stop_recording()
            actions.next()
            resume_recording(history_was_recording)
            recorder.record_basic_action('user.move_cursor_to_next_snippet_stop', [])
            history.record_action(compute_snippet_next_description())

    def insert_snippet_by_name(
            name: str,
            substitutions: dict[str, str] = None,
        ):
        if substitutions:
            actions.next(name, substitutions)
        else:
            history_was_recording = temporarily_stop_recording()
            actions.next(name, substitutions)
            resume_recording(history_was_recording)
            name = str(name)
            recorder.record_basic_action('user.insert_snippet_by_name', [name])
            history.record_action(compute_snippet_description(name))

    def insert_snippet_by_name_with_phrase(name: str, phrase: str):
        history_was_recording = temporarily_stop_recording()
        actions.next(name, phrase)
        resume_recording(history_was_recording)
        name = str(name)
        phrase = str(phrase)
        recorder.record_basic_action('user.insert_snippet_by_name_with_phrase', [name, phrase])
        history.record_action(compute_snippet_with_phrase_description(name, phrase))