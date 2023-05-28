from talon import Module, app, cron
import subprocess
from pathlib import PurePath
import os

module = Module()
@module.action_class
class Actions:
    def basic_action_recorder_generate_command_recommendations():
        '''Runs the program to generate command recommendations'''
        cron.after('0ms', generate_recommendations)
    
def generate_recommendations():
    program_path = PurePath(__file__)
    parent = program_path.parent
    programme_name = 'basic_action_record_analysis.py'
    full_path = os.path.join(parent, programme_name)
    subprocess.run(["python", full_path], shell = True)
    app.notify('Recommendations Generated!')
