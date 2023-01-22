from talon import Module, actions, Context

class ActionRecorder:
    def __init__(self):
        self.actions = []
        self.start_accepting_actions()
    
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
    
    def compute_talon_script(self):
        code = []
        for action in self.actions:
            code.append(action.compute_talon_script())
        return code
    
class BasicAction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
    
    def compute_talon_script(self):
        code = self.name + '(' + ', '.join(self.compute_arguments_converted_to_string()) + ')'
        return code
    
    def compute_arguments_converted_to_string(self):
        result = []
        for argument in self.arguments:
            if type(argument) == str:
                converted_argument = self.compute_string_argument(argument)
            else:
                converted_argument = str(argument)
            result.append(converted_argument)
        return result
    
    def compute_string_argument(self, argument: str):
        string_argument = "'" + argument.replace("'", "\\'") + "'"
        return string_argument

class TalonTimeSpecification:
    def __init__(self, amount: int, unit: str):
        self.amount = amount
        self.unit = unit
    
    def __str__(self) -> str:
        return str(self.amount) + self.unit
    
    def __repr__(self) -> str:
        return self.__str__()

recorder = ActionRecorder()

RECORDING_TAG_NAME = 'basic_action_recorder_recording'
recording_context = Context()
recording_context.matches = 'tag: user.' + RECORDING_TAG_NAME

@recording_context.action_class("main")
class MainActions:
    def insert(text: str):
        recorder.stop_accepting_actions()
        actions.next(text)
        recorder.start_accepting_actions()
        recorder.record_basic_action('insert', [text])

    def key(key: str):
        actions.next(key)
        recorder.record_basic_action('key', [key])

    def mouse_click(button: int = 0):
        actions.next(button)
        recorder.record_basic_action('mouse_click', [button])

    def mouse_move(x: float, y: float):
        actions.next(x, y)
        recorder.record_basic_action('mouse_move', [x, y])

    def mouse_scroll(y: float = 0, x: float = 0, by_lines: bool = False):
        actions.next(y, x, by_lines)
        recorder.record_basic_action('mouse_scroll', [y, x, by_lines])

module = Module()
module.tag(RECORDING_TAG_NAME)
context = Context()

@module.action_class
class Actions:
    def basic_action_recorder_start_recording():
        '''Causes the basic action recorder to start recording actions'''
        start_recording()
        recorder.clear()
    
    def basic_action_recorder_stop_recording():
        '''Causes the basic action recorder to stop recording actions'''
        stop_recording()
    
    def basic_action_recorder_type_talon_script():
        '''Types out the talon script of the recorded actions'''
        stop_recording()
        code = recorder.compute_talon_script()
        for line_of_code in code:
            actions.insert(line_of_code)
            actions.key('enter')
    
    def basic_action_recorder_record_millisecond_sleep(milliseconds: int):
        '''Records a sleep action for the specified number of milliseconds in the basic action recorder'''
        time_specification = TalonTimeSpecification(milliseconds, 'ms')
        recorder.record_basic_action('sleep', [time_specification])

def start_recording():
    context.tags = ['user.' + RECORDING_TAG_NAME]

def stop_recording():
    context.tags = []

def log(*args):
    string_arguments = []
    for argument in args:
        string_arguments.append(str(argument))
    text = ' '.join(string_arguments)
    print('Basic Action Recorder:', text)