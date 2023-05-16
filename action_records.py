import json
from talon import actions, Module

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
    
    def perform(self):
        function = getattr(actions, self.name)
        if len(self.arguments) > 0:
            function(*self.arguments)
        else:
            function()
    
    def to_json(self) -> str:
        return json.dumps({'name': self.name, 'arguments': self.arguments})
    
    @staticmethod
    def from_json(text: str):
        representation = json.loads(text)
        return BasicAction(representation['name'], representation['arguments'])

def compute_talon_script_boolean_value(value: bool):
    if value:
        return 1
    return 0

class Command:
    def __init__(self, name: str, actions):
        self.name = name
        self.actions = actions
    
    def get_name(self):
        return self.name
    
    def get_actions(self):
        return self.actions


module = Module()
@module.action_class
class Actions:
    def basic_action_recorder_read_file_record(path: str):
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
                elif line.startswith('Command: '):
                    commands.append(Command(current_command_name, current_command_actions)) 
                    current_command_name = line_without_trailing_newline
                    current_command_name = []
 
def is_action(text: str):
    return text.startswith('{')
