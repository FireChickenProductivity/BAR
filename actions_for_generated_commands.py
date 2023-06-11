from talon import Module, actions
from typing import List

module = Module()
@module.action_class
class Actions:
    def fire_chicken_auto_generated_command_action_insert_formatted_text(text: str, formats: str, separator: str = ''):
        ''''''
        words = get_space_separated_text(text)
        formatter = Formatter(formats, separator)
        formatted_text = formatter.format_text(words)
        actions.insert(formatted_text)
        
class Formatter:
    def __init__(self, formats: str, separator: str):
        self.formats = get_space_separated_text(formats)
        self.format_index = 0
        self.separator = separator
    
    def format_text(self, words: List) -> str:
        formatted_words = [self._format_word(word) for word in words]
        formatted_text = self.separator.join(formatted_words)
        self.format_index = 0
        return formatted_text
    
    def _format_word(self, word: str) -> str:
        formatted_word = apply_format(word, self.formats[self.format_index])
        if self.format_index < len(self.formats) - 1: self.format_index += 1
        return formatted_word
        
def get_space_separated_text(text: str):
    return text.split(' ')

def apply_format(text: str, format: str) -> str:
    if format == 'lower':
        return text.lower()
    elif format == 'upper':
        return text.upper()
    elif format == 'capitalized':
        return text.capitalize()
    else:
        return text
        
        
