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

bar use main record: Causes the basic action recorder to store its recording in record.txt if recording into a file is enabled.

bar record in (say a name here): Causes the basic action recorder to store its recording in "record (the dictated name).txt" if recording into a file is enabled.

bar insert data path: Types out the path to BAR data.

# Registering Callback Functions

The following action can be used to register a callback function that gets called when a basic action is performed with a corresponding BasicAction object:

user.basic_action_recorder_register_callback_function_with_name(callback_function: Callable, name: str):

BasicAction objects have get_name() and get_arguments() methods that return the name of the action and the arguments passed to it respectively.

The following action can be used to unregister a callback function using the name it was registered with: 

basic_action_recorder_unregister_callback_function_with_name(name: str)

# Settings
If user.basic_action_recorder_record_in_file is set to any integer other than 0, the basic action history is outputted to the record file in the BAR Data directory. The setting is 0 by default. By default, the basic action recorder will store any recordings in the most recently updated record file on startup. Which record is used can be changed with the above record commands. 

If user.should_record_time_information is set to any integer other than 0, the basic action history will include information on how many seconds has passed between the start of a command and the last action as well as when recording has started (such as after a restart or a setting change). 