import json
from talon import actions

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