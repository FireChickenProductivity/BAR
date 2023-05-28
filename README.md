# BAR: Basic Action Recorder
The Basic Action Recorder can be used to record basic talon voice actions and output the corresponding talonscript code for them.

# Commands
bar start recording: Causes the BAR to record basic talon actions that are performed by commands. This includes the insert action (used to type text), the key action (used to perform keystrokes), the mouse_click action (used to press mouse buttons), the mouse_move action (used by many commands that move the mouse), and the mouse_scroll action (used to scroll the mouse wheel). Using this command clears the last recording.

bar stop recording: Causes the BAR to stop recording.

bar sleep (non-negative imager) milliseconds: Causes the BAR to record a sleep action for the specified number of milliseconds. A sleep action pauses the active talon command for the specified amount of time. This is used because the BAR cannot record sleep actions directly.

bar type recording: Types out the talon script for the recorded actions. It types each line of talon code and presses enter after each. 

bar play recording: Perform the recorded actions.

bar history show: Show a command history including basic actions, command names, and the names of registered noises (only works with noise recognition configured through noise.register). 

bar history hide: Hide the bar history. 

# Settings
If user.basic_action_recorder_record_in_file is set to any integer other than 0, the basic action history is outputted to the record.txt file in the BAR Data directory. The setting is 0 by default. 

# Command Recommendation Generation
The basic_action_record_analysis.py program can be used to output recommended voice commands to generate to improve productivity based on the previously mentioned record.txt. The program is currently very simplistic and a work in progress. Recommendations get generated in the recommendations.txt file in the BAR Data directory. 
