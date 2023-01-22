# BAR: Basic Action Recorder
The Basic Action Recorder can be used to record basic talon voice actions and output the corresponding talon script for them.

# Commands
bar start recording: Causes the BAR to record basic talon actions that are performed by commands. This includes the insert action (used to type text), the key action (used to perform keystrokes), the mouse_click action (used to press mouse buttons), the mouse_move action (used by many commands that move the mouse), and the mouse_scroll action (used to scroll the mouse wheel). Using this command clears the last recording.

bar stop recording: Causes the BAR to stop recording.

bar sleep (non-negative imager) milliseconds: Causes the BAR to record a sleep action for the specified number of milliseconds. A sleep action pauses the active talon command for the specified amount of time. This is used because the BAR cannot record sleep actions directly.

bar type recording: Types out the talon script for the recorded actions.
