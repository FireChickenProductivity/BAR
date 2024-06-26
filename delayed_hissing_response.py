from talon import cron, Module, settings

module = Module()
hissing_start_time_setting_name = 'basic_action_recorder_hissing_recognition_start_delay'
hissing_start_time = 'user.' + hissing_start_time_setting_name
module.setting(
    hissing_start_time_setting_name,
    type = int,
    default = 350,
    desc = 'How long the basic action recorder will wait before recognizing the start of a hiss in milliseconds'
)

class DelayedHissingJobHandler:
    def __init__(self, callback):
        self.job = None
        self.hiss_successfully_started = False
        self.callback = callback
    
    def handled_delayed_hiss(self, active):
        if active:
            self.start_delayed_hiss()
        else:
            self.stop_delayed_hiss()
    
    def start_delayed_hiss(self):
        self.job = cron.after(f'{settings.get(hissing_start_time)}ms', self.start_hiss_if_not_canceled)
        
    def start_hiss_if_not_canceled(self):
        self.callback(True)
        self.hiss_successfully_started = True
        self.job = None
    
    def stop_delayed_hiss(self):
        self.cancel_job()
        if self.hiss_successfully_started:
            self.callback(False)
            self.hiss_successfully_started = False
    
    def cancel_job(self):
        if self.job:
            cron.cancel(self.job)
        self.job = None
