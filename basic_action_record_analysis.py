import json
import math
from pathlib import PurePath

try:
    from action_records import BasicAction, read_file_record, Command, TalonCapture
except ImportError:
    pass
import os

DATA_FOLDER = 'BAR Data'
EXPECTED_PARENT = 'user'
EXPECTED_GRANDPARENT = 'talon'
INPUT_FILENAME = 'record.txt'
OUTPUT_FILENAME = 'recommendations.txt'
COMMANDS_TO_IGNORE_FILENAME = 'commands_to_ignore.txt'

class PotentialCommandInformation:
    def __init__(self, actions):
        self.actions = actions
        self.number_of_times_used: int = 0
        self.total_number_of_words_dictated: int = 0
        self.number_of_actions: int = len(self.actions)
        for action in self.actions:
            argument = action.get_arguments()[0]
            if action.get_name() == 'repeat' and type(argument) == int:
                self.number_of_actions += argument - 1
    
    def get_number_of_actions(self):
        return len(self.actions)
    
    def get_average_words_dictated(self):
        return self.total_number_of_words_dictated/self.number_of_times_used
    
    def get_number_of_times_used(self):
        return self.number_of_times_used

    def get_actions(self):
        return self.actions
    
    def update_actions(self, new_actions):
        self.actions = new_actions
    
    def process_usage(self, words_dictated: str):
        words = words_dictated.split(' ')
        number_of_words = len(words)
        self.total_number_of_words_dictated += number_of_words
        self.number_of_times_used += 1
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f'actions: {CommandSet.compute_representation(self)}, number of times used: {self.number_of_times_used}, total number of words dictated: {self.total_number_of_words_dictated}'

class CommandSet:
    def __init__(self):
        self.commands = {}
    
    def insert_command(self, command, representation):
        self.commands[representation] = command
    
    def process_command_usage(self, command, *, is_abstract_representation = False):
        representation = CommandSet.compute_representation(command)
        if representation not in self.commands:
            self.insert_command(PotentialCommandInformation(command.get_actions()), representation)
            if not is_abstract_representation:
                if should_make_abstract_repeat_representation(command):
                    abstract_repeat_representation = make_abstract_repeat_representation_for(command)
                    self.process_command_usage(abstract_repeat_representation, is_abstract_representation = True)
        self.commands[representation].process_usage(command.get_name())

    @staticmethod
    def compute_representation(command):
        actions = command.get_actions()
        representation = compute_string_representation_of_actions(actions)
        return representation
    
    def get_commands_meeting_condition(self, condition):
        commands_to_output = []
        for command in self.commands.values():
            if condition(command):
                commands_to_output.append(command)
        return commands_to_output
    
    def contains_command_with_representation(self, representation: str):
        return representation in self.commands
    
    def contains_command(self, command):
        representation = CommandSet.compute_representation(command)
        return self.contains_command_with_representation(representation)

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        representation: str = ''
        for command in self.commands.values():
            representation += str(command) + '\n'
        return representation

def compute_string_representation_of_actions(actions):
    representation = ''
    for action in actions:
        representation += action.to_json()
    return representation

def should_make_abstract_repeat_representation(command):
    actions = command.get_actions()
    if len(actions) <= 2:
        return False
    return any(action.get_name() == 'repeat' for action in actions)

def make_abstract_repeat_representation_for(command):
    actions = command.get_actions()
    instances = 0
    new_actions = []
    new_name = command.get_name()
    for action in actions:
        if action.get_name() == 'repeat':
            instances += 1
            argument = TalonCapture('number_small', instances)
            repeat_action = BasicAction('repeat', [argument])
            new_actions.append(repeat_action)
            new_name += ' ' + argument.compute_command_component()
        else:
            new_actions.append(action)
    new_command = Command(new_name, new_actions)
    return new_command

def basic_command_filter(command: PotentialCommandInformation):
    return command.get_average_words_dictated() > 1 and command.get_number_of_times_used() > 1 and (command.get_number_of_actions()/command.get_average_words_dictated() < 2 or command.get_number_of_actions()*math.sqrt(command.get_number_of_times_used()) > command.get_average_words_dictated())

class ProgramDirectoryInvalidException(Exception):
    pass

def compute_data_directory():
    program_path = PurePath(__file__)
    parent = program_path.parent
    while parent.stem != EXPECTED_PARENT:
        parent = parent.parent
    if parent.parent.stem != EXPECTED_GRANDPARENT:
        raise ProgramDirectoryInvalidException('The program must be stored in the talon user directory!')
    return os.path.join(parent, DATA_FOLDER)

def compute_target_path(output_directory):
    return os.path.join(output_directory, INPUT_FILENAME)

def create_file_if_nonexistent(path):
    if not os.path.exists(path):
        with open(path, 'w') as file:
            pass

def create_file_at_directory_if_nonexistent(directory, file):
    path = os.path.join(directory, file)
    create_file_if_nonexistent(path)

def read_commands_to_ignore(directory):
    create_file_at_directory_if_nonexistent(directory, COMMANDS_TO_IGNORE_FILENAME)
    path = os.path.join(directory, COMMANDS_TO_IGNORE_FILENAME)
    commands = CommandSet()
    current_command_actions = []
    with open(path, 'r') as file:
        line = file.readline()
        while line:
            line_without_trailing_newline = line.strip()
            if line_without_trailing_newline:
                current_command_actions.append(BasicAction.from_json(line_without_trailing_newline))
            else:
                commands.process_command_usage(Command('', current_command_actions))
                current_command_actions = []
            line = file.readline()
        if current_command_actions:
            commands.process_command_usage(Command('', current_command_actions))
    return commands

def compute_record_without_stuff_to_ignore(directory, record):
    commands_to_ignore = read_commands_to_ignore(directory)
    filtered_record = [command for command in record if not commands_to_ignore.contains_command(command)]
    return filtered_record

def obtain_file_record(directory):
    target_path = compute_target_path(directory)
    record = read_file_record(target_path)
    filtered_record = compute_record_without_stuff_to_ignore(directory, record)
    return filtered_record

def output_recommendations(recommended_commands, output_directory):
    output_path = os.path.join(output_directory, OUTPUT_FILENAME)
    with open(output_path, 'w') as file:
        for command in recommended_commands:
            file.write(f'#Number of times used: {command.get_number_of_times_used()}\n')
            for action in command.get_actions():
                file.write('\t' + action.compute_talon_script() + '\n')
            file.write('\n\n')

def compute_repeat_simplified_command(command):
    new_actions = []
    last_non_repeat_action = None
    repeat_count: int = 0
    for action in command.get_actions():
        if action == last_non_repeat_action:
            repeat_count += 1
        else:
            if repeat_count > 0:
                new_actions.append(BasicAction('repeat', [repeat_count]))
                repeat_count = 0
            new_actions.append(action)
            last_non_repeat_action = action
    if repeat_count > 0:
        new_actions.append(BasicAction('repeat', [repeat_count]))
        repeat_count = 0
    new_command = Command(command.get_name(), new_actions)
    return new_command

def compute_recommendations_from_record(record, max_command_chain_considered = 100):
    command_set: CommandSet = CommandSet()
    for command in record:
        simplified_command = compute_repeat_simplified_command(command)
        command_set.process_command_usage(simplified_command)
    
    for i in range(len(record) - 1):
        rolling_command: Command = record[i].copy()
        roll_target = min(len(record), i + max_command_chain_considered)
        for j in range(i + 1, roll_target):
            rolling_command.append_command(record[j])
            simplified_rolling_command = compute_repeat_simplified_command(rolling_command)
            command_set.process_command_usage(simplified_rolling_command)
        print('roll', i + 1, 'out of', len(record) - 1, 'target: ', roll_target - 1)
    recommended_commands = command_set.get_commands_meeting_condition(basic_command_filter)
    sorted_recommended_commands = sorted(recommended_commands, key = lambda command: command.get_number_of_times_used(), reverse = True)
    return sorted_recommended_commands

def generate_recommendations(directory):
    record = obtain_file_record(directory)
    print('finished reading record')
    recommendations = compute_recommendations_from_record(record)
    print('outputting recommendations')
    output_recommendations(recommendations, directory)
    print('completed')

def main():
    directory = compute_data_directory()
    generate_recommendations(directory)

if __name__ == '__main__':
    main()
