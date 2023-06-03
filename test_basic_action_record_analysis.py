import unittest

class TestPotentialCommandInformation(unittest.TestCase):
    def test_potential_command_information_for_press_a_has_one_action(self):
        potential_command_information = generate_potential_command_information_on_press_a()
        self.assertEqual(potential_command_information.get_number_of_actions(), 1)
    
    def test_potential_command_information_for_press_a_with_single_word_has_average_number_of_words_dictated_one(self):
        self._assert_potential_command_information_for_press_a_with_words_dictated_has_specified_number_of_average_words_dictated('air', 1)
    
    def test_potential_command_information_for_press_a_with_two_words_dictated_has_average_number_of_words_dictated_two(self):
        self._assert_potential_command_information_for_press_a_with_words_dictated_has_specified_number_of_average_words_dictated('press air', 2)
    
    def test_potential_command_information_for_press_a_with_sequence_dictated_has_correct_average_number_of_words_dictated(self):
        self._assert_potential_command_information_for_press_a_with_words_dictated_has_specified_number_of_average_words_dictated(['air', 'chicken', 'this is a test'], 2)

    def test_potential_command_information_for_press_a_reports_single_usage_with_single_usage(self):
        potential_command_information = generate_potential_command_information_on_press_a()
        potential_command_information.process_usage('this is a test')
        self.assertEqual(potential_command_information.get_number_of_times_used(), 1)
    
    def test_potential_command_information_for_press_a_reports_two_usages_with_two_usages(self):
        potential_command_information = generate_potential_command_information_on_press_a()
        potential_command_information.process_usage('this is a test')
        potential_command_information.process_usage('chicken')
        self.assertEqual(potential_command_information.get_number_of_times_used(), 2)

    def test_potential_command_information_with_two_actions_has_correct_number_of_actions(self):
        self._assert_potential_command_information_with_key_actions_has_correct_number_of_actions(['a', 'ctrl-c'])

    def _assert_potential_command_information_for_press_a_with_words_dictated_has_specified_number_of_average_words_dictated(self, words, number):
        potential_command_information = generate_potential_command_information_on_press_a()
        if isinstance(words, str):
            potential_command_information.process_usage(words)
        else:
            for utterance in words:
                potential_command_information.process_usage(utterance)
        self.assertEqual(potential_command_information.get_average_words_dictated(), number)
    
    def _assert_potential_command_information_with_key_actions_has_correct_number_of_actions(self, keystrokes):
        potential_command_information = PotentialCommandInformation(generate_multiple_key_pressing_actions(keystrokes))
        self.assertEqual(potential_command_information.get_number_of_actions(), len(keystrokes))

class TestCommandSet(unittest.TestCase):
    def test_command_set_with_single_command_used_once_gives_correct_information(self):
        command_set = CommandInformationSet()
        command = generate_copy_all_command_chain(0, 0)
        command_set.process_command_usage(command)
        potential_command_information = command_set.get_commands_meeting_condition(return_true)
        self.assertEqual(len(potential_command_information), 1)
        command_information: PotentialCommandInformation = potential_command_information[0]
        self.assertEqual(command_information.get_average_words_dictated(), 2)
        self.assertEqual(command_information.get_number_of_actions(), 2)
        self.assertEqual(command_information.get_number_of_times_used(), 1)
    
    def test_command_set_handles_multiple_commands_with_multiple_uses(self):
        command_set = CommandInformationSet()
        press_a = generate_press_a_command()
        copy_all = generate_copy_all_command()

        command_set.process_command_usage(generate_press_a_command_chain(0, 1))
        command_set.process_command_usage(generate_copy_all_command_chain(1, 1))
        command_set.process_command_usage(generate_copy_all_command_chain(2, 1))
        command_set.process_command_usage(generate_press_a_command_chain(3, 1))
        command_set.process_command_usage(generate_press_a_command_chain(4, 1))

        expected_press_a_information = generate_potential_command_information_with_uses(generate_press_a_action_list(), [press_a.get_name()]*3)
        expected_copy_all_information = generate_potential_command_information_with_uses(generate_copy_all_action_list(), [copy_all.get_name()]*2)
        press_a_information = get_command_set_information_matching_actions(command_set, press_a.get_actions())
        copy_all_information = get_command_set_information_matching_actions(command_set, copy_all.get_actions())
        
        self.assertTrue(potential_command_informations_match(press_a_information, expected_press_a_information))
        self.assertTrue(potential_command_informations_match(copy_all_information, expected_copy_all_information))

class TestCommandSimplification(unittest.TestCase):
    def test_repeat_simplify_command_does_nothing_to_press_a(self):
        command = generate_press_a_command_chain()
        expected_command = generate_press_a_command_chain()
        simplified_command = compute_repeat_simplified_command_chain(command)
        self.assertEqual(simplified_command.get_actions(), expected_command.get_actions())
    
    def test_repeat_simplify_command_handles_multiple_repetitions(self):
        command = CommandChain('test', generate_multiple_key_pressing_actions(['b', 'b', 'c', 'd', 'd', 'd', 'a', 'l', 'l']))
        expected_actions = [generate_key_press_action('b'), BasicAction('repeat', [1]), generate_key_press_action('c'), generate_key_press_action('d'), BasicAction('repeat', [2]), 
        generate_key_press_action('a'), generate_key_press_action('l'), BasicAction('repeat', [1])]
        expected_command = CommandChain('test', expected_actions)

        simplified_command = compute_repeat_simplified_command_chain(command)

        self.assertEqual(simplified_command.get_actions(), expected_command.get_actions())

class TestGeneratingCommandSetFromRecord(unittest.TestCase):
    def test_can_handle_simple_record(self):
        record = generate_simple_command_record()
        command_set = create_command_information_set_from_record(record, 100, verbose = True)

        rain_information = generate_potential_command_information_with_uses(generate_rain_as_down_command().get_actions(), ['rain'])
        copy_all_information = generate_potential_command_information_with_uses(generate_copy_all_command().get_actions(), ['copy all'])
        air_information = generate_potential_command_information_with_uses(generate_press_a_command().get_actions(), ['air'])
        rain_copy_all_information = generate_potential_command_information_with_uses(generate_multiple_key_pressing_actions(['down', 'ctrl-a', 'ctrl-c']), ['rain copy all'])
        rain_copy_all_air_information = generate_potential_command_information_with_uses(generate_multiple_key_pressing_actions(['down', 'ctrl-a', 'ctrl-c', 'a']), ['rain copy all air'])
        copy_all_air_information = generate_potential_command_information_with_uses(generate_multiple_key_pressing_actions(['ctrl-a', 'ctrl-c', 'a']), ['copy all air'])

        expected_command_information = [rain_information, copy_all_information, air_information, 
                                        rain_copy_all_information, rain_copy_all_air_information, copy_all_air_information]
        self.assertTrue(command_set_matches_expected_potential_command_information(command_set, expected_command_information))

def command_set_matches_expected_potential_command_information(command_set, expected):
    if command_set.get_size() != len(expected):
        print(f'Incorrect size! Expected {len(expected)} but received {command_set.get_size()}')
        print('Received: ', str(command_set))
        return False
    for command_information in expected:
        matching_command_information = get_command_set_information_matching_actions(command_set, command_information.get_actions())
        if not potential_command_informations_match(matching_command_information, command_information):
            print(f'Potential commands do not match: Received: {matching_command_information} Expected: {command_information}')
            return False
    return True

def generate_simple_command_record():
    record = [generate_rain_as_down_command(), generate_copy_all_command(), generate_press_a_command()]
    return record

def get_command_set_information_matching_actions(command_set, actions):
    def search_condition(command):
        return command.get_actions() == actions
    matching_actions = command_set.get_commands_meeting_condition(search_condition)
    return matching_actions[0]

def generate_potential_command_information_with_uses(actions, invocations):        
    information = PotentialCommandInformation(actions)
    for invocation in invocations:
        information.process_usage(invocation)
    return information
        
def potential_command_informations_match(original, other):
    return original.get_average_words_dictated() == other.get_average_words_dictated() and original.get_number_of_actions() == other.get_number_of_actions() and \
            original.get_number_of_times_used() == other.get_number_of_times_used() and original.get_actions() == other.get_actions()

def return_true(value):
    return True

def generate_potential_command_information_on_press_a():
    return PotentialCommandInformation(generate_press_a_action_list())

def generate_press_a_command_chain(chain: int = 0, chain_ending_index: int = 0):
    return CommandChain('air', generate_press_a_action_list(), chain, chain_ending_index)

def generate_press_a_command():
    return Command('air', generate_press_a_action_list())

def generate_press_a_action_list():
    return [generate_press_a_action()]

def generate_press_a_action():
    return generate_key_press_action('a')

def generate_copy_all_command_chain(chain, chain_ending_index):
    copy_all_command = generate_copy_all_command()
    return CommandChain(copy_all_command.get_name(), copy_all_command.get_actions(), chain, chain_ending_index)

def generate_copy_all_command():
    return generate_multiple_key_pressing_command('copy all', generate_copy_all_keystroke_list())

def generate_copy_all_action_list():
    return generate_multiple_key_pressing_actions(generate_copy_all_keystroke_list())

def generate_copy_all_keystroke_list():
    return ['ctrl-a', 'ctrl-c']

def generate_rain_as_down_command():
    return generate_key_pressing_command('rain', 'down')

def generate_multiple_key_pressing_command(name: str, keystrokes):
    actions = generate_multiple_key_pressing_actions(keystrokes)
    command = Command(name, actions)
    return command

def generate_multiple_key_pressing_actions(keystrokes):
    actions = [generate_key_press_action(keystroke) for keystroke in keystrokes]
    return actions

def generate_key_pressing_command(name: str, keystroke: str):
    action = generate_key_press_action(keystroke)
    command = Command(name, [action])
    return command

def generate_key_press_action(keystroke: str):
    return BasicAction('key', [keystroke])

if __name__ == '__main__':
    from basic_action_record_analysis import *
    from action_records import *
    unittest.main()
