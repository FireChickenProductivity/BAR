from talon import Module, actions, Context, imgui, speech_system, app, settings
from .action_records import BasicAction, RECORDING_START_MESSAGE
from .time_difference import TimeDifference
import os
from typing import Callable

module = Module()
history_size = module.setting(
    'basic_action_recorder_history_size',
    type = int,
    default = 20,
    desc = 'How many basic actions to show at a time in the basic action recorder history.'
)

should_record_in_file = module.setting(
    'basic_action_recorder_record_in_file',
    type = int,
    default = 0,
    desc = 'Determines if the basic action recorder should record actions in a file for analysis. 0 means false and any other integer means true.'
)

should_record_time_information = module.setting(
    'basic_action_recorder_record_time_information_in_file',
    type = int,
    default = 1,
    desc = '''Determines if the basic action recorder should record time information in the record file when recording in the file. 
    0 means false and any other integer means true.'''
)

OUTPUT_DIRECTORY = None
PRIMARY_OUTPUT_FILE_NAME = 'record'
PRIMARY_OUTPUT_FILE_EXTENSION = '.txt'
record_file_name_postfix = ''
primary_output_path = None
def set_up():
    global OUTPUT_DIRECTORY, primary_output_path
    OUTPUT_DIRECTORY = os.path.join(actions.path.talon_user(), 'BAR Data')
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
    update_record_file_name_to_most_recent()
    start_recording_when_should_record_in_file(should_record_in_file.get())

def update_record_file_name_to_most_recent():
    name = compute_most_recently_updated_record_file_name(OUTPUT_DIRECTORY)
    postfix = ''
    if name != PRIMARY_OUTPUT_FILE_NAME and name != '': postfix = compute_record_name_postfix(name)
    update_record_file_name(postfix)

def compute_record_name_postfix(name: str) -> str:
    postfix = ''
    if name == PRIMARY_OUTPUT_FILE_NAME + PRIMARY_OUTPUT_FILE_EXTENSION:
        postfix = ''
    else:
        postfix = name[len(PRIMARY_OUTPUT_FILE_NAME):-len(PRIMARY_OUTPUT_FILE_EXTENSION)]
    return postfix

def update_record_file_name(postfix: str):
    global primary_output_path
    record_filename = PRIMARY_OUTPUT_FILE_NAME + postfix + PRIMARY_OUTPUT_FILE_EXTENSION
    primary_output_path = os.path.join(OUTPUT_DIRECTORY, record_filename)

def compute_most_recently_updated_record_file_name(directory):
    files_in_directory = os.listdir(directory)
    record_file_names_in_directory = filter_for_record_file_names(files_in_directory)
    name = compute_most_recently_updated_file_name_given_names_and_directory(record_file_names_in_directory, directory)
    return name

def filter_for_record_file_names(file_names):
    filtered_names = [name for name in file_names if is_record_file_name(str(name))]
    return filtered_names

def is_record_file_name(name: str) -> bool:
    return name.startswith('record') and name.endswith('.txt')

def compute_most_recently_updated_file_name_given_names_and_directory(names, directory) -> str:
    most_recently_updated_filename = ''
    most_recent_update_time = 0
    for name in names:
        path = os.path.join(directory, name)
        update_time = os.path.getmtime(path)
        if update_time > most_recent_update_time:
            most_recently_updated_filename = name
            most_recent_update_time = update_time
    return most_recently_updated_filename

class ActionRecorder:
    def __init__(self):
        self.actions = []
        self.stop_recording_actions_in_primary_memory()
        self.temporarily_rejecting_actions = False
    
    def clear(self):
        self.actions.clear()
    
    def empty(self):
        return len(self.actions) == 0

    def record_action(self, action):
        self.actions.append(action)
        log('action recorded:', action.get_name(), action.get_arguments(), 'code', action.compute_talon_script())
    
    def record_basic_action(self, name, arguments):
        if not self.temporarily_rejecting_actions and self.should_record_when_not_temporarily_rejecting_actions():
            action = BasicAction(name, arguments)
            if self.recording_actions_in_primary_memory: self.record_action(action)
            if should_record_in_file.get(): record_output_to_file(action.to_json())
            if callback_manager.is_listening(): callback_manager.handle_action(action)
    
    def should_record_when_not_temporarily_rejecting_actions(self):
        return self.recording_actions_in_primary_memory or should_record_in_file.get() or callback_manager.is_listening()

    def stop_recording_actions_in_primary_memory(self):
        self.recording_actions_in_primary_memory = False
    
    def start_recording_actions_in_primary_memory(self):
        self.recording_actions_in_primary_memory = True
    
    def temporarily_reject_actions(self):
        self.temporarily_rejecting_actions = True

    def stop_temporarily_rejecting_actions(self):
        self.temporarily_rejecting_actions = False

    def is_accepting_actions(self):
        return self.recording_actions_in_primary_memory
    
    def compute_talon_script(self):
        code = []
        for action in self.actions:
            code.append(action.compute_talon_script())
        return code
    
    def perform_actions(self):
        for action in self.actions:
            perform_basic_action(action)

def perform_basic_action(action: BasicAction):
    function = getattr(actions, action.get_name())
    if action.get_name() == 'sleep': #Special case for sleep because it cannot be recorded directly
        duration = action.get_arguments()[0]
        function(str(duration))
    elif len(action.get_arguments()) > 0:
        function(*action.get_arguments())
    else:
        function()

class ActionHistory:
    def __init__(self):
        self.actions = []
        self.should_record_history = False
    
    def record_action(self, description: str):
        if self.should_record_history:
            previous_number_of_times = None
            previous_action = ''
            if len(self.actions) > 0:
                previous_number_of_times, previous_action = compute_action_recording_parts(self.actions[-1])
            if previous_action == description and previous_number_of_times is not None:
                self.actions[-1] = f'{previous_number_of_times + 1}X {description}'
            else:
                self.actions.append(description)
                if len(self.actions) > history_size.get():
                    self.actions.pop(0)
    
    def is_recording_history(self):
        return self.should_record_history
    
    def start_recording_history(self):
        self.should_record_history = True
    
    def stop_recording_history(self):
        self.should_record_history = False
    
    def get_action_history(self):
        return self.actions

def compute_action_recording_parts(recording: str):
    prefix, _, description = recording.partition('X ')
    if prefix != '' and prefix.isdigit():
        return int(prefix), description
    return 1, recording

class TalonTimeSpecification:
    def __init__(self, amount: int, unit: str):
        self.amount = amount
        self.unit = unit
    
    def __str__(self) -> str:
        return str(self.amount) + self.unit
    
    def __repr__(self) -> str:
        return self.__str__()

class CallbackManager:
    def __init__(self):
        self.functions = {}
    
    def insert_callback_function_with_name(self, callback_function, name: str):
        self.functions[name] = callback_function
    
    def remove_callback_function_with_name(self, name: str):
        self.functions.pop(name, 'Function not found')
    
    def is_listening(self):
        return len(self.functions) > 0
    
    def handle_action(self, action):
        for function_name in self.functions: self.functions[function_name](action)

time_difference_manager = TimeDifference()
recorder = ActionRecorder()
history = ActionHistory()
callback_manager = CallbackManager()
RECORDING_TAG_NAME = 'basic_action_recorder_recording'
module.tag(RECORDING_TAG_NAME)
recording_context = Context()
recording_context.matches = 'tag: user.' + RECORDING_TAG_NAME

@recording_context.action_class("main")
class MainActions:
    def insert(text: str):
        recorder.temporarily_reject_actions()
        history_was_recording = history.is_recording_history()
        history.stop_recording_history()
        actions.next(text)
        recorder.stop_temporarily_rejecting_actions()
        if history_was_recording:
            history.start_recording_history()
        recorder.record_basic_action('insert', [str(text)])
        history.record_action(compute_insert_description(text))

    def key(key: str):
        actions.next(key)
        recorder.record_basic_action('key', [str(key)])
        history.record_action(compute_key_description(key))

    def mouse_click(button: int = 0):
        actions.next(button)
        recorder.record_basic_action('mouse_click', [int(button)])
        history.record_action(compute_mouse_click_description(button))

    def mouse_move(x: float, y: float):
        actions.next(x, y)
        recorder.record_basic_action('mouse_move', [float(x), float(y)])
        history.record_action(compute_mouse_movement_description(x, y))

    def mouse_scroll(y: float = 0, x: float = 0, by_lines: bool = False):
        actions.next(y, x, by_lines)
        recorder.record_basic_action('mouse_scroll', [float(y), float(x), bool(by_lines)])
        history.record_action(compute_mouse_scroll_description(y, x, by_lines))

def compute_insert_description(text: str):
    return f"Type: {text}"

def compute_key_description(keystroke: str):
    return f'Press: {keystroke}'

def compute_mouse_click_description(button: int):
    if button == 0:
        return 'Left click'
    elif button == 1:
        return 'Right click'
    elif button == 2:
        return 'Middle Click'

def compute_mouse_movement_description(x, y):
    return f'Mouse moved to {x}, {y}'

def compute_mouse_scroll_description(y: float, x: float, by_lines: bool):
    text: str = ''
    if y != 0:
        text += compute_mouse_scroll_partial_description(y, True, by_lines)
    if x != 0:
        if text != '':
            text += ' and '
        text += compute_mouse_scroll_partial_description(x, False, by_lines)
    return text

def compute_mouse_scroll_partial_description(amount: float, is_vertical: bool, by_lines: bool):
    text: str = 'Scroll '
    if is_vertical:
        if amount >= 0:
            text += 'Down '
        else:
            text += 'Up '
    else:
        if amount >= 0:
            text += 'Right '
        else:
            text += 'Left '
    text += str(abs(amount))
    if by_lines:
        text += ' Lines'
    return text


context = Context()

@module.action_class
class Actions:
    def basic_action_recorder_start_recording():
        '''Causes the basic action recorder to start recording actions'''
        start_recording()
        recorder.clear()
        recorder.start_recording_actions_in_primary_memory()
    
    def basic_action_recorder_stop_recording():
        '''Causes the basic action recorder to stop recording actions'''
        recorder.stop_recording_actions_in_primary_memory()
        stop_recording_if_nothing_listening()
    
    def basic_action_recorder_type_talon_script():
        '''Types out the talon script of the recorded actions'''
        recorder.stop_recording_actions_in_primary_memory()
        stop_recording_if_nothing_listening()
        code = recorder.compute_talon_script()
        for line_of_code in code:
            actions.insert(line_of_code)
            actions.key('enter')
    
    def basic_action_recorder_play_recording():
        '''Plays the actions recorded by the basic action recorder'''
        recorder.perform_actions()

    def basic_action_recorder_record_millisecond_sleep(milliseconds: int):
        '''Records a sleep action for the specified number of milliseconds in the basic action recorder'''
        time_specification = TalonTimeSpecification(milliseconds, 'ms')
        recorder.record_basic_action('sleep', [time_specification])
    
    def basic_action_recorder_record_history():
        '''Causes the basic action recorder to record the history of actions performed'''
        history.start_recording_history()
        start_recording()
    
    def basic_action_recorder_stop_recording_history():
        '''Causes the basic action recorder to stop recording the history of actions performed'''
        history.stop_recording_history()
        stop_recording_if_nothing_listening()
    
    def basic_action_recorder_show_history():
        '''Shows the basic action recorder history of actions performed'''
        gui.show()
    
    def basic_action_recorder_hide_history():
        '''Stops displaying the basic action recorder history of actions performed'''
        gui.hide()
    
    def basic_action_recorder_register_callback_function_with_name(callback_function: Callable, name: str):
        '''Registers a callback function with specified name to receive basic actions performed'''
        callback_manager.insert_callback_function_with_name(callback_function, name)
        start_recording()
    
    def basic_action_recorder_unregister_callback_function_with_name(name: str):
        '''Unregisters the specified callback function using the name it was registered with'''
        callback_manager.remove_callback_function_with_name(name)
        stop_recording_if_nothing_listening()
    
    def basic_action_recorder_update_active_record_name(postfix: str):
        '''Updates the name of the active record that the basic action recorder will record to when
            recording the basic action history is enabled'''
        new_postfix = postfix
        if len(postfix) > 0: new_postfix = ' ' + new_postfix
        update_record_file_name(new_postfix)

    def basic_action_recorder_insert_data_directory_path():
        '''Types out the path to the basic action recorder data directory'''
        actions.insert(OUTPUT_DIRECTORY)

def start_recording():
    context.tags = ['user.' + RECORDING_TAG_NAME]

def stop_recording_if_nothing_listening():
    if not (recorder.should_record_when_not_temporarily_rejecting_actions() or history.is_recording_history()):
        context.tags = []

def start_recording_when_should_record_in_file(should_record_in_file):
    if should_record_in_file:
        start_recording()
        record_recording_start_to_file_if_needed()
    else:
        stop_recording_if_nothing_listening()
    
settings.register('user.basic_action_recorder_record_in_file', start_recording_when_should_record_in_file)

def log(*args):
    string_arguments = []
    for argument in args:
        string_arguments.append(str(argument))
    text = ' '.join(string_arguments)
    print('Basic Action Recorder:', text)

def record_recording_start_to_file_if_needed():
    if should_record_time_information.get():
        record_output_to_file(RECORDING_START_MESSAGE)

def record_command_start_to_file_record(text: str):
    output = [text]
    if should_record_time_information.get():
        time_difference_manager.receive_current_time()
        time_difference = time_difference_manager.get_difference()
        time_difference_text = compute_time_difference_text(time_difference)
        output.append(time_difference_text)
    record_outputs_to_file(output)

def record_outputs_to_file(outputs):
    with open(primary_output_path, 'a') as file:
        for output in outputs:
            write_output_line_to_file(output, file)

def record_output_to_file(text: str):
    with open(primary_output_path, 'a') as file:
        write_output_line_to_file(text, file)

def write_output_line_to_file(output, file):
    file.write(output + '\n')

def on_phrase(j):
    global history
    if actions.speech.enabled() and (history.is_recording_history() or should_record_in_file.get() != 0):
        words = j.get('text')
        if words:
            command_chain = ' '.join(words)
            if history.is_recording_history():
                history.record_action('Command: ' + command_chain)
            if should_record_in_file.get() != 0:
                record_output_to_file('Command: ' + command_chain)

speech_system.register('phrase', on_phrase)

def on_noise(name: str, finished: bool):
    if history.is_recording_history():
        history.record_action(f'Noise: {name} {compute_noise_postfix(finished)}')
    
    if should_record_in_file.get():
        record_output_to_file('Command: ' + 'noise_' + name + '_' + compute_noise_postfix(finished))

def compute_noise_postfix(finished: bool):
    return "start" if finished else "end"

from talon import noise
noise.register("", on_noise)

@imgui.open(y=0)
def gui(gui: imgui.GUI):
    global history
    gui.text("Basic Action History")
    gui.line()
    
    for description in history.get_action_history():
        gui.text(description)

app.register('ready', set_up)   
