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

class Command:
    def __init__(self, name: str, actions):
        self.name = name
        self.actions = actions
    
    def get_name(self):
        return self.name
    
    def get_actions(self):
        return self.actions
    
    def copy(self):
        return Command(self.name, self.actions[:])
    
    def has_same_actions_as(self, other):
        return self.actions == other.actions

class CommandChain(Command):
    def __init__(self, name: str, actions, chain_number: int = 0):
        super().__init__(name, actions)
        self.chain_number: int = chain_number
        self.chain_size: int = 0

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

COMMAND_NAME_PREFIX = 'Command: '

def read_file_record(path: str):
    '''Obtains a list of the basic actions performed by the commands in the specified record file'''
    commands = []
    current_command_name = ''
    current_command_actions = []
    with open(path, 'r') as file:
        line = file.readline()
        while line:
            line_without_trailing_newline = line.strip()
            if is_action(line_without_trailing_newline):
                current_command_actions.append(BasicAction.from_json(line_without_trailing_newline))
            elif line.startswith(COMMAND_NAME_PREFIX):
                if len(current_command_actions) > 0:
                    commands.append(Command(current_command_name, current_command_actions[:])) 
                current_command_name = compute_command_name_without_prefix(line_without_trailing_newline)
                current_command_actions = []
            line = file.readline()
        if len(current_command_actions) > 0:
            commands.append(Command(current_command_name, current_command_actions[:])) 
    return commands

def compute_command_name_without_prefix(command_name: str):
    return command_name[len(COMMAND_NAME_PREFIX):]
 


def is_action(text: str):
    return text.startswith('{')
