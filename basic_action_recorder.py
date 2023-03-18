from talon import Module, actions, Context, imgui, speech_system

module = Module()
history_size = module.setting(
    'basic_action_recorder_history_size',
    type = int,
    default = 20,
    desc = 'How many basic actions to show at a time in the basic action recorder history'
)

class ActionRecorder:
    def __init__(self):
        self.actions = []
        self.stop_accepting_actions()
    
    def clear(self):
        self.actions.clear()
    
    def empty(self):
        return len(self.actions) == 0

    def record_action(self, action):
        self.actions.append(action)
    
    def record_basic_action(self, name, arguments):
        if self.will_accept_actions:
            action = BasicAction(name, arguments)
            self.record_action(action)
            log('action recorded:', name, arguments, 'code', action.compute_talon_script())
    
    def stop_accepting_actions(self):
        self.will_accept_actions = False
    
    def start_accepting_actions(self):
        self.will_accept_actions = True
    
    def is_accepting_actions(self):
        return self.will_accept_actions
    
    def compute_talon_script(self):
        code = []
        for action in self.actions:
            code.append(action.compute_talon_script())
        return code

class ActionHistory:
    def __init__(self):
        self.actions = []
        self.should_record_history = False
    
    def record_action(self, description: str):
        if self.should_record_history:
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


class BasicAction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
    
    def compute_talon_script(self):
        code = self.name + '(' + ', '.join(self.compute_arguments_converted_to_talon_script_string()) + ')'
        return code
    
    def compute_arguments_converted_to_talon_script_string(self):
        result = []
        for argument in self.arguments:
            if type(argument) == str:
                converted_argument = self.compute_string_argument(argument)
            elif type(argument) == bool:
                converted_argument = str(compute_talon_script_boolean_value(argument))
            else:
                converted_argument = str(argument)
            result.append(converted_argument)
        return result
    
    def compute_string_argument(self, argument: str):
        string_argument = "'" + argument.replace("'", "\\'") + "'"
        return string_argument

def compute_talon_script_boolean_value(value: bool):
    if value:
        return 1
    return 0

class TalonTimeSpecification:
    def __init__(self, amount: int, unit: str):
        self.amount = amount
        self.unit = unit
    
    def __str__(self) -> str:
        return str(self.amount) + self.unit
    
    def __repr__(self) -> str:
        return self.__str__()

recorder = ActionRecorder()
history = ActionHistory()
RECORDING_TAG_NAME = 'basic_action_recorder_recording'
module.tag(RECORDING_TAG_NAME)
recording_context = Context()
recording_context.matches = 'tag: user.' + RECORDING_TAG_NAME

@recording_context.action_class("main")
class MainActions:
    def insert(text: str):
        recorder_was_recording = recorder.is_accepting_actions()
        history_was_recording = history.is_recording_history()
        recorder.stop_accepting_actions()
        history.stop_recording_history()
        actions.next(text)
        if recorder_was_recording:
            recorder.start_accepting_actions()
        if history_was_recording:
            history.start_recording_history()
        recorder.record_basic_action('insert', [text])
        history.record_action(compute_insert_description(text))

    def key(key: str):
        actions.next(key)
        recorder.record_basic_action('key', [key])
        history.record_action(compute_key_description(key))

    def mouse_click(button: int = 0):
        actions.next(button)
        recorder.record_basic_action('mouse_click', [button])
        history.record_action(compute_mouse_click_description(button))

    def mouse_move(x: float, y: float):
        actions.next(x, y)
        recorder.record_basic_action('mouse_move', [x, y])
        history.record_action(compute_mouse_movement_description(x, y))

    def mouse_scroll(y: float = 0, x: float = 0, by_lines: bool = False):
        actions.next(y, x, by_lines)
        recorder.record_basic_action('mouse_scroll', [y, x, by_lines])

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

context = Context()

@module.action_class
class Actions:
    def basic_action_recorder_start_recording():
        '''Causes the basic action recorder to start recording actions'''
        start_recording()
        recorder.clear()
        recorder.start_accepting_actions()
    
    def basic_action_recorder_stop_recording():
        '''Causes the basic action recorder to stop recording actions'''
        recorder.stop_accepting_actions()
        stop_recording_if_nothing_listening()
    
    def basic_action_recorder_type_talon_script():
        '''Types out the talon script of the recorded actions'''
        recorder.stop_accepting_actions()
        stop_recording_if_nothing_listening()
        code = recorder.compute_talon_script()
        for line_of_code in code:
            actions.insert(line_of_code)
            actions.key('enter')
    
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

def start_recording():
    context.tags = ['user.' + RECORDING_TAG_NAME]

def stop_recording_if_nothing_listening():
    if not (recorder.is_accepting_actions() or history.is_recording_history()):
        context.tags = []

def log(*args):
    string_arguments = []
    for argument in args:
        string_arguments.append(str(argument))
    text = ' '.join(string_arguments)
    print('Basic Action Recorder:', text)

def on_phrase(j):
    global history
    if history.is_recording_history() and actions.speech.enabled():
        words = j.get('text')
        if words:
            command_chain = ' '.join(words)
            history.record_action('Command: ' + command_chain)

speech_system.register('phrase', on_phrase)

@imgui.open(y=0)
def gui(gui: imgui.GUI):
    global history
    gui.text("Basic Action History")
    gui.line()
    
    for description in history.get_action_history():
        gui.text(description)
