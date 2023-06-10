import math
from pathlib import PurePath
from typing import List

try:
    from action_records import BasicAction, read_file_record, TalonCapture, CommandChain
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
        self.count_repetitions_appropriately_for_number_of_actions()
        self.chain = None
        
    def count_repetitions_appropriately_for_number_of_actions(self):
        for action in self.actions: self.count_repetition_appropriately_for_a_number_of_actions(action)
    
    def count_repetition_appropriately_for_a_number_of_actions(self, action):
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
    
    def is_abstract(self):
        return False

    def process_usage(self, command_chain):
        if self.should_process_usage(command_chain.get_chain_number()):
            self.process_relevant_usage(command_chain)
    
    def should_process_usage(self, chain):
        return self.chain is None or chain > self.chain

    def process_relevant_usage(self, command_chain):
        self.number_of_times_used += 1
        self.chain = command_chain.get_chain_ending_index()
        words = command_chain.get_name().split(' ')
        self.total_number_of_words_dictated += len(words)

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f'actions: {CommandInformationSet.compute_representation(self)}, number of times used: {self.number_of_times_used}, total number of words dictated: {self.total_number_of_words_dictated}'

class PotentialAbstractCommandInformation(PotentialCommandInformation):
    def __init__(self, actions):
        self.instantiation_set = ActionSequenceSet()
        super().__init__(actions)
    
    def process_usage(self, command_chain, instantiation):
        if self.should_process_usage(command_chain.get_chain_number()):
            self.instantiation_set.insert(instantiation.get_actions())
            self.process_relevant_usage(command_chain)
    
    def get_number_of_instantiations(self):
        return self.instantiation_set.get_size()
    
    def is_abstract(self):
        return True

def compute_repeat_simplified_command_chain(command_chain):
    new_actions = []
    last_non_repeat_action = None
    repeat_count: int = 0
    for action in command_chain.get_actions():
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
    new_command = CommandChain(command_chain.get_name(), new_actions, command_chain.get_chain_number(), command_chain.get_size())
    return new_command

def compute_insert_simplified_command_chain(command_chain):
    new_actions = []
    current_insert_text = ''
    for action in command_chain.get_actions():
        if action.get_name() == 'insert':
            current_insert_text += action.get_arguments()[0]
        else:
            if current_insert_text:
                new_actions.append(BasicAction('insert', [current_insert_text]))
                current_insert_text = ''
            new_actions.append(action)
    if current_insert_text: new_actions.append(BasicAction('insert', [current_insert_text]))
    new_command = CommandChain(command_chain.get_name(), new_actions, command_chain.get_chain_number(), command_chain.get_size())
    return new_command

class CommandInformationSet:
    def __init__(self):
        self.commands = {}

    def insert_command(self, command, representation):
        self.commands[representation] = command
    
    def process_abstract_command_usage(self, command_chain, abstract_command_chain):
        representation = CommandInformationSet.compute_representation(abstract_command_chain)
        if representation not in self.commands:
            self.insert_command(PotentialAbstractCommandInformation(abstract_command_chain.get_actions()), representation)
        self.commands[representation].process_usage(abstract_command_chain, command_chain)

    def create_abstract_commands(self, command_chain):
        commands = []
        if should_make_abstract_repeat_representation(command_chain):
            abstract_repeat_representation = make_abstract_repeat_representation_for(command_chain)
            commands.append(abstract_repeat_representation)
        return commands
    
    def handle_needed_abstract_commands(self, command_chain):
        abstract_commands = self.create_abstract_commands(command_chain)
        for abstract_command in abstract_commands: self.process_abstract_command_usage(command_chain, abstract_command)

    def process_command_usage(self, command_chain):
        representation = CommandInformationSet.compute_representation(command_chain)
        if representation not in self.commands:
            self.insert_command(PotentialCommandInformation(command_chain.get_actions()), representation)
        self.commands[representation].process_usage(command_chain)
        self.handle_needed_abstract_commands(command_chain)
    
    def process_partial_chain_usage(self, record, command_chain):
        command_chain.append_command(record[command_chain.get_next_chain_index()])
        simplified_command_chain = compute_repeat_simplified_command_chain(command_chain)
        simplified_command_chain = compute_insert_simplified_command_chain(simplified_command_chain)
        self.process_command_usage(simplified_command_chain)

    def process_chain_usage(self, record, chain, max_command_chain_considered, verbose = False):
        command_chain: CommandChain = CommandChain(None, [], chain)
        chain_target = min(len(record), chain + max_command_chain_considered)
        for chain_ending_index in range(chain, chain_target): self.process_partial_chain_usage(record, command_chain)
        if verbose: print('chain', chain + 1, 'out of', len(record) - 1, 'target: ', chain_target - 1)

    @staticmethod
    def compute_representation(command):
        actions = command.get_actions()
        representation = compute_string_representation_of_actions(actions)
        return representation
    
    def get_commands_meeting_condition(self, condition):
        commands_to_output = [command for command in self.commands.values() if condition(command)]
        return commands_to_output
    
    def contains_command_with_representation(self, representation: str):
        return representation in self.commands
    
    def contains_command(self, command):
        representation = CommandInformationSet.compute_representation(command)
        return self.contains_command_with_representation(representation)

    def get_size(self):
        return len(self.commands)

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        representation: str = ''
        for command in self.commands.values():
            representation += str(command) + '\n'
        return representation

class ActionSequenceSet:
    def __init__(self):
        self.set = set()
    
    def insert(self, actions):
        representation = compute_string_representation_of_actions(actions)
        self.set.add(representation)
    
    def contains(self, actions):
        return compute_string_representation_of_actions(actions) in self.set
    
    def contains_command_actions(self, command):
        return self.contains(command.get_actions())
    
    def get_size(self):
        return len(self.set)

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

def make_abstract_repeat_representation_for(command_chain):
    actions = command_chain.get_actions()
    instances = 0
    new_actions = []
    new_name = command_chain.get_name()
    for action in actions:
        if action.get_name() == 'repeat':
            instances += 1
            argument = TalonCapture('number_small', instances, ' - 1')
            repeat_action = BasicAction('repeat', [argument])
            new_actions.append(repeat_action)
            new_name += ' ' + argument.compute_command_component()
        else:
            new_actions.append(action)
    new_command = CommandChain(new_name, new_actions, command_chain.get_chain_number(), command_chain.get_size())
    return new_command

def is_character_alpha(character: str):
    return character.isalpha()

class TextSeparation:
    def __init__(self, string: str, character_filter):
        self.separated_parts = []
        self.separators = []
        self.current_separated_part = ''
        self.current_separator = ''
        self.text_prefix = ''
        for character in string: self._process_character(character, character_filter)
        if not self.current_separated_part: self._handle_separator()
        if not self.current_separator: self._add_separated_part()
    
    def _process_character(self, character, character_filter):
        if character_filter(character): 
            if not self.current_separated_part: self._handle_separator()
            self.current_separated_part += character
        else:
            if not self.current_separator and self.current_separated_part: self._add_separated_part()
            self.current_separator += character

    def _handle_separator(self):
        if len(self.separated_parts) > 0:
            self.separators.append(self.current_separator)
        else:
            self.text_prefix = self.current_separator
        self.current_separator = ''
    
    def _add_separated_part(self):
        self.separated_parts.append(self.current_separated_part)
        self.current_separated_part = ''
    
    def get_separated_parts(self):
        return self.separated_parts

    def get_separators(self):
        return self.separators
    
    def get_prefix(self):
        return self.text_prefix

class TextSeparationAnalyzer:
    def __init__(self, text: str, character_filter = is_character_alpha):
        self.text_separation = TextSeparation(text, character_filter)
        self.prose_index = None
        self.final_prose_index_into_separated_parts = None
        self.prose_beginning_index = None
        self.prose_ending_index = None
        self.number_of_prose_words = None
        self.found_prose: bool = False
        self.prose: str = None

    def search_for_prose_beginning_at_separated_part_index(self, words, separated_parts, index):
        initial_separated_part = separated_parts[index].lower()
        first_word = words[0]
        if initial_separated_part.endswith(first_word): self.prose_beginning_index = initial_separated_part.rfind(first_word)
    
    def search_for_prose_at_separated_part_index_beginning(self, prose_without_spaces, separated_parts, index):
        if prose_without_spaces in separated_parts[index].lower(): 
            self.prose_beginning_index = separated_parts[index].lower().find(prose_without_spaces)
            self.prose_ending_index = len(prose_without_spaces) + self.prose_beginning_index
            self.found_prose = True
            self.final_prose_index_into_separated_parts = index
    
    def is_prose_middle_different_from_separated_parts_at_index(self, words, separated_parts, index):
        for prose_index in range(1, len(words) - 1):
            word = words[prose_index]
            separated_part: str = separated_parts[prose_index + index].lower()
            if separated_part != word: return True
        return False
    
    def perform_final_prose_search_at_index(self, words, separated_parts, index):
        if len(words) == 1:
            self.found_prose = True
            self.final_prose_index_into_separated_parts = self.prose_index
        else:
            self.final_prose_index_into_separated_parts = index + len(words) - 1
            final_separated_part = separated_parts[self.final_prose_index_into_separated_parts].lower()
            last_word = words[-1]
            if final_separated_part.startswith(last_word): 
                self.prose_ending_index = len(last_word)
                self.found_prose = True
    
    def reset_indices(self):
        self.prose_beginning_index = None
        self.prose_index = None
        self.prose_ending_index = None
        self.final_prose_index_into_separated_parts = None

    def search_for_prose_at_separated_part_index(self, prose_without_spaces: str, words, index: int):
        self.reset_indices()
        
        separated_parts = self.text_separation.get_separated_parts()

        self.search_for_prose_at_separated_part_index_beginning(prose_without_spaces, separated_parts, index)
        if self.found_prose: return
        if len(words) + index > len(separated_parts): return

        self.search_for_prose_beginning_at_separated_part_index(words, separated_parts, index)
        if self.prose_beginning_index is None: return

        if self.is_prose_middle_different_from_separated_parts_at_index(words, separated_parts, index): return 

        self.perform_final_prose_search_at_index(words, separated_parts, index)
    
    def search_for_prose_in_separated_part(self, prose: str):
        lowercase_prose = prose.lower()
        prose_without_spaces = lowercase_prose.replace(' ', '')
        words = lowercase_prose.split(' ')
        self.number_of_prose_words = len(words)
        self.prose = prose
        for index in range(len(self.text_separation.get_separated_parts())):
            self.search_for_prose_at_separated_part_index(prose_without_spaces, words, index)
            self.prose_index = index
            if self.found_prose: return
        self.found_prose = False
        return
    
    def is_separator_consistent(self, starting_index: int = 0, ending_index: int = -1):
        separators = self.text_separation.get_separators()[starting_index:ending_index]
        if len(separators) <= 1: return True
        initial_separator = separators[0]
        for index in range(1, len(separators)):
            if separators[index] != initial_separator: return False
        return True

    def get_prose_index(self):
        return self.prose_index
    
    def get_prose_beginning_index(self):
        return self.prose_beginning_index
    
    def get_prose_ending_index(self):
        return self.prose_ending_index

    def is_prose_separator_consistent(self):
        return self.is_separator_consistent(self.prose_index, self.final_prose_index_into_separated_parts)

    def has_found_prose(self):
        return self.found_prose
    
    def compute_text_before_prose(self) -> str:
        text: str = self.text_separation.get_prefix()
        separated_parts = self.text_separation.get_separated_parts()
        separators = self.text_separation.get_separators()
        for index in range(self.prose_index):
            text += separated_parts[index]
            text += separators[index]
        text += separated_parts[self.prose_index][0:self.prose_beginning_index]
        return text
    
    def compute_text_after_prose(self) -> str:
        separated_parts = self.text_separation.get_separated_parts()
        separators = self.text_separation.get_separators()
        text: str = ''
        first_word: str = separated_parts[self.final_prose_index_into_separated_parts]
        if self.prose_ending_index < len(first_word): text += first_word[self.prose_ending_index:]
        if self.prose_index < len(separators): text += separators[self.final_prose_index_into_separated_parts] 
        for index in range(self.final_prose_index_into_separated_parts + 1, len(separated_parts)):
            text += separated_parts[index]
            if index < len(separators): text += separators[index]
        return text
    
    def _compute_prose_portion_of_nonseparated_text(self):
        words = self.prose.split(' ')
        prose_portion_of_text_as_string = self.text_separation.get_separated_parts()[self.prose_index][self.prose_beginning_index:self.prose_ending_index]
        word_starting_index = 0
        words_from_text = []
        for word in words:
            word_ending_index = word_starting_index + len(word)
            word_from_text = prose_portion_of_text_as_string[word_starting_index:word_ending_index]
            words_from_text.append(word_from_text)
            word_starting_index = word_ending_index
        return words_from_text

    def _compute_prose_portion_of_separated_text(self, prose_final_index):
        prose_words = []
        separated_parts = self.text_separation.get_separated_parts()
        prose_words.append(separated_parts[self.prose_index][self.prose_beginning_index:])
        prose_words.extend([separated_parts[index] for index in range(self.prose_index + 1, prose_final_index)])
        prose_words.append(separated_parts[prose_final_index][:self.prose_ending_index])
        return prose_words

    def compute_prose_portion_of_text(self) -> List[str]:
        if self.prose_index == self.final_prose_index_into_separated_parts: return self._compute_prose_portion_of_nonseparated_text()
        else: return self._compute_prose_portion_of_separated_text(self.final_prose_index_into_separated_parts)

def is_prose_inside_inserted_text_with_consistent_separator(prose: str, text: str) -> bool:
    text_separation_analyzer = TextSeparationAnalyzer(text)
    text_separation_analyzer.search_for_prose_in_separated_part(prose)
    text_separation_analyzer.is_prose_separator_consistent()
    return text_separation_analyzer.has_found_prose()

class InvalidCaseException(Exception): pass

def compute_case_string(text: str) -> str:
    if text.islower(): return 'lower'
    elif text.isupper(): return 'upper'
    elif text[0].isupper() and text[1:].islower(): return 'capitalized'
    else: raise InvalidCaseException()

def compute_case_string_for_prose(analyzer: TextSeparationAnalyzer):
    prose = analyzer.compute_prose_portion_of_text()
    case_strings = [compute_case_string(prose_word) for prose_word in prose]
    case_string = ' '.join(case_strings)
    return case_string

def basic_command_filter(command: PotentialCommandInformation):
    return command.get_average_words_dictated() > 1 and command.get_number_of_times_used() > 1 and \
            (not command.is_abstract() or command.get_number_of_instantiations() > 2) and \
            (command.get_number_of_actions()/command.get_average_words_dictated() < 2 or \
            command.get_number_of_actions()*math.sqrt(command.get_number_of_times_used()) > command.get_average_words_dictated())

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
    commands = ActionSequenceSet()
    current_command_actions = []
    with open(path, 'r') as file:
        line = file.readline()
        while line:
            line_without_trailing_newline = line.strip()
            if line_without_trailing_newline:
                current_command_actions.append(BasicAction.from_json(line_without_trailing_newline))
            else:
                commands.insert(current_command_actions)
                current_command_actions = []
            line = file.readline()
        if current_command_actions:
            commands.insert(current_command_actions)
    return commands

def compute_record_without_stuff_to_ignore(directory, record):
    commands_to_ignore = read_commands_to_ignore(directory)
    filtered_record = [command for command in record if not commands_to_ignore.contains_command_actions(command)]
    return filtered_record

def obtain_file_record(directory):
    target_path = compute_target_path(directory)
    record = read_file_record(target_path)
    filtered_record = compute_record_without_stuff_to_ignore(directory, record)
    return filtered_record

def write_command_to_file(file, command):
    file.write(f'#Number of times used: {command.get_number_of_times_used()}\n')
    if command.is_abstract(): file.write(f'#Number of instantiations of abstract command: {command.get_number_of_instantiations()}\n')
    for action in command.get_actions(): file.write('\t' + action.compute_talon_script() + '\n')
    file.write('\n\n')

def output_recommendations(recommended_commands, output_directory):
    output_path = os.path.join(output_directory, OUTPUT_FILENAME)
    with open(output_path, 'w') as file:
        for command in recommended_commands: write_command_to_file(file, command)

def create_command_information_set_from_record(record, max_command_chain_considered, *, verbose = False):
    command_set: CommandInformationSet = CommandInformationSet()    
    for chain in range(len(record)): command_set.process_chain_usage(record, chain, max_command_chain_considered, verbose = verbose)
    return command_set

def compute_recommendations_from_record(record, max_command_chain_considered = 100, *, verbose = False):
    command_set = create_command_information_set_from_record(record, max_command_chain_considered, verbose = verbose)
    recommended_commands = command_set.get_commands_meeting_condition(basic_command_filter)
    sorted_recommended_commands = sorted(recommended_commands, key = lambda command: command.get_number_of_times_used(), reverse = True)
    return sorted_recommended_commands

def generate_recommendations(directory):
    record = obtain_file_record(directory)
    print('finished reading record')
    recommendations = compute_recommendations_from_record(record, verbose = True)
    print('outputting recommendations')
    output_recommendations(recommendations, directory)
    print('completed')

def main():
    directory = compute_data_directory()
    generate_recommendations(directory)

if __name__ == '__main__':
    main()
