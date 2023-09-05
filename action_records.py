import json

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
    
    def get_name(self):
        return self.name
    
    def get_arguments(self):
        return self.arguments
    
    def to_json(self) -> str:
        return json.dumps({'name': self.name, 'arguments': self.arguments}, cls = BasicActionEncoder)
    
    @staticmethod
    def from_json(text: str):
        representation = json.loads(text)
        return BasicAction(representation['name'], representation['arguments'])
    
    def __eq__(self, other) -> bool:
        return other is not None and self.name == other.name and self.arguments == other.arguments
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return self.to_json()

class BasicActionEncoder(json.JSONEncoder):
    def default(self, object):
        if isinstance(object, TalonCapture):
            return object.to_json()
        return json.JSONEncoder.default(self, object)

def compute_talon_script_boolean_value(value: bool):
    if value:
        return 1
    return 0

class TalonCapture:
    def __init__(self, name: str, instance: int, postfix: str = ''):
        self.name = name
        self.instance = instance
        self.postfix = postfix
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return self.name + '_' + str(self.instance) + self.postfix
    
    def compute_command_component(self):
        return f'<{self.name}>'
    
    def to_json(self):
        return json.dumps({'name': self.name, 'instance': self.instance})
    
    @staticmethod
    def from_json(json):
        attributes = json.loads(json)
        return TalonCapture(attributes['name'], attributes['instance'])

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.instance == other.instance and self.postfix == other.postfix

class Command:
    def __init__(self, name: str, actions, seconds_since_action: int = None):
        self.name = name
        self.actions = actions
        self.seconds_since_action = seconds_since_action
    
    def get_name(self) -> str:
        return self.name
    
    def get_actions(self):
        return self.actions
    
    def copy(self):
        return Command(self.name, self.actions[:])
    
    def has_same_actions_as(self, other) -> bool:
        return self.actions == other.actions
    
    def set_name(self, name: str) -> None:
        self.name = name
    
    def is_time_information_available(self) -> bool:
        return self.seconds_since_action is not None
    
    def get_seconds_since_action(self) -> int:
        return self.seconds_since_action

    def is_command_record(self):
        return True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        representation =  f'Command({self.name}{", " + str(self.seconds_since_action) if self.is_time_information_available() else ""},\n'
        for action in self.actions: representation += str(action) + '\n'
        representation += ')'
        return representation

class CommandChain(Command):
    def __init__(self, name: str, actions, chain_number: int = 0, chain_size: int = 0):
        super().__init__(name, actions)
        self.chain_number: int = chain_number
        self.chain_size: int = chain_size

    def append_command(self, command):
        if self.name is None:
            self.name = command.get_name()
        else:
            self.name += f' {command.get_name()}'
        self.actions.extend(command.get_actions())
        self.chain_size += 1
    
    def get_chain_number(self):
        return self.chain_number
    
    def get_chain_ending_index(self):
        return self.get_next_chain_index() - 1
    
    def get_next_chain_index(self):
        return self.chain_number + self.chain_size
    
    def get_size(self):
        return self.chain_size

class RecordingStart:
    def is_command_record(self):
        return False

COMMAND_NAME_PREFIX = 'Command: '
RECORDING_START_MESSAGE = 'START'
TIME_DIFFERENCE_PREFIX = 'T'

class RecordParser:
    def __init__(self, path: str):
        self.commands = []
        self.current_command_name = ''
        self.current_command_actions = []
        self.seconds_since_last_action = None
        self.seconds_since_last_action_for_next_command = None
        self.time_information_found_after_command = False
        self.parse_path(path)

    def parse_path(self, path: str):
        with open(path, 'r') as file:
            line = file.readline()
            while line:
                self.process_line(line)
                line = file.readline()
            if len(self.current_command_actions) > 0:
                self.commands.append(Command(self.current_command_name, self.current_command_actions[:], self.seconds_since_last_action_for_next_command)) 
    
    def process_line(self, line: str):
        line_without_trailing_newline = line.strip()
        if is_action(line_without_trailing_newline):
            self.add_action_based_on_line(line_without_trailing_newline)
        elif is_line_command_start(line):
            self.process_command_start(line_without_trailing_newline)
        elif is_line_time_deference(line):
            self.process_time_difference(line_without_trailing_newline)
        if is_line_recording_start(line_without_trailing_newline):
            self.process_recording_start()
        if is_line_command_ending(line_without_trailing_newline):
            self.reset_command_information_except_name()
     
    def add_action_based_on_line(self, line_without_trailing_newline: str):
        self.current_command_actions.append(BasicAction.from_json(line_without_trailing_newline))

    def process_command_start(self, line_without_trailing_newline: str):
        if len(self.current_command_actions) > 0:
            self.add_current_command()
        self.current_command_name = compute_command_name_without_prefix(line_without_trailing_newline)

    def add_current_command(self):
        self.commands.append(Command(self.current_command_name, self.current_command_actions[:], self.seconds_since_last_action))

    def process_time_difference(self, line_without_trailing_newline):
        self.seconds_since_last_action = self.seconds_since_last_action_for_next_command
        self.seconds_since_last_action_for_next_command = compute_seconds_since_last_action(line_without_trailing_newline)
        self.time_information_found_after_command = True

    def process_recording_start(self):
        self.commands.append(RecordingStart())
        self.current_command_name = ''

    def reset_command_information_except_name(self):
        self.current_command_actions = []
        self.seconds_since_last_action = None
        if not self.time_information_found_after_command:
            self.seconds_since_last_action_for_next_command = None
        self.time_information_found_after_command = False

    def get_record(self):
        return self.commands


def read_file_record(path: str):
    '''Obtains a list of the basic actions performed by the commands in the specified record file'''
    parser = RecordParser(path)
    return parser.get_record()

def compute_command_name_without_prefix(command_name: str):
    return command_name[len(COMMAND_NAME_PREFIX):]

def compute_seconds_since_last_action(time_record: str) -> int:
    return time_record[1:]

def is_action(text: str):
    return text.startswith('{')

def compute_time_difference_text(difference: int) -> str:
    return TIME_DIFFERENCE_PREFIX + str(difference)

def is_line_command_ending(line_without_trailing_newline: str):
    return is_line_command_start(line_without_trailing_newline) or is_line_recording_start(line_without_trailing_newline)

def is_line_command_start(line: str):
    return line.startswith(COMMAND_NAME_PREFIX)

def is_line_time_deference(line: str):
    return line.startswith(TIME_DIFFERENCE_PREFIX)

def is_line_recording_start(line_without_trailing_newline: str):
    return line_without_trailing_newline == RECORDING_START_MESSAGE

result = read_file_record('C:\\Users\\Samuel\\AppData\\Roaming\\talon\\user\\BAR Data\\record short.txt')
for command in result:
    if command.is_command_record():
        print(command)
    else:
        print('recordings start')