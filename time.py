"""time.py is a simple controller designed to show stimuli at specific times.  A
reference for usage is in luminanceCompression2.py

The intended usage of this class is to present a sequence of fixed stimuli, and
log the timings and keyboard responses to them.  Adaptive experiments should
simply instantiate a new StimulusController for each trial, for example -
adaptive logic would be out of place here."""

from SimpleVisionEgg import SimpleVisionEgg, RESERVED_WORDS
from pygame.locals import K_SPACE


class StimulusController:
    # Stimulus related attributes
    stim_list = None
    stim_dict = None
    trials = None
    active_stims = None

    # Attribs for keeping track of experiment
    go_duration = ('forever', )
    trial_times = None
    state = None
    t = 0
    log = None
    responses = None
    response_name = None
    response_ref_time = 0
    trials_to_run = 0 # == run all of them

    # SimpleVisionEgg instance
    vision_egg = None
    keyboard_controller = None

    def __init__(self, stim_dict, trials, vision_egg):
        self.trial_times = []
        self.stim_dict = stim_dict
        self.trials = trials
        self.active_stims = []
        self.vision_egg = vision_egg
        # Break out the oft-used keyboard controller
        self.keyboard_controller = self.vision_egg.keyboard_controller


        self.state = self.state_generator()
        self.vision_egg.set_functions(update=self.update, 
                                      pause_update=self.pause_update)
        self.log = {'trial_times': self.trial_times}
        self.responses = {}

    def run_trials(self, num):
        self.trials_to_run = num
        self.vision_egg.go()

    def compute_go_duration(self, units='seconds'):
        """This should run through the trials, find the latest stimulus and add
        this info up, putting it in go_duration"""
        go_duration = 0
        for trial in self.trials:
            max_time = 0
            for stim in trial:
                for name, parms in stim.items():
                    try:
                        end_time = parms['stop']
                    except KeyError:
                        end_time = parms['start'] + parms['duration']
                    if end_time > max_time:
                        max_time = end_time

            go_duration += max_time

        self.go_duration = (go_duration, units)


    def update(self, t):
        """Wrapper to adapt the state generator into a regular function"""
        print "update called", self.active_stims
        self.t = t
        self.state.next()


    def pause_update(self):
        """I currently can't figure out how to make this work... it doesn't
        depend on whether the duration is 'forever' or not"""
        print "pause called", self.active_stims
        self.stim_dict['text_disp'].parameters.on = True
        self.active_stims = [('text_disp', {'stop': 0})]


    def activate_stims(self, new_stims):
        for name, parms in new_stims:
            parameters = self.stim_dict[name].parameters
            parameters.on = True
            for k, v in parms.items():
                if k not in RESERVED_WORDS:
                    setattr(parameters, k, v)
                elif k == 'log':
                    for log_k, log_v in v.items():
                        try:
                            self.log[log_k].append(log_v)
                        except KeyError:
                            self.log[log_k] = [log_v]
                elif k == 'response':
                    for resp_k, resp_v in v.items():
                        if self.response_name:
                            self.log_response(reset=True)
                        self.response_name = resp_k
                        self.expected_response = resp_v
                        self.response_ref_time = self.t


        self.active_stims.extend(new_stims)
        del new_stims[:]


    def record_response(self, response, rt):
        """Helper function for log_responses"""
        try:
            response_dict = self.responses[self.response_name]
            response_dict['expected'].append(self.expected_response)
            response_dict['response'].append(response)
            response_dict['ref_time'].append(self.response_ref_time)
            response_dict['rt'].append(rt)
        except KeyError:
            response_dict = {}

            response_dict['expected'] = [self.expected_response]
            response_dict['response'] = [response] 
            response_dict['ref_time'] = [self.response_ref_time]
            response_dict['rt'] = [rt]

            self.responses[self.response_name] = response_dict


    def log_response(self, reset=False):
        if self.response_name:
            last_press = \
                    self.keyboard_controller.get_time_last_response_since_go()
            if last_press > self.response_ref_time:
                self.record_response(
                        self.keyboard_controller.get_last_response_since_go(),
                        last_press - self.response_ref_time)

                self.response_name = None
            elif reset:
                self.record_response(None, None)
                self.response_name = None
                
        
    def deactivate_stims(self):
        to_del = []
        for stim_tup in self.active_stims:
            name, parms = stim_tup
            try:
                stop = parms['stop']
            except KeyError:
                stop = parms['start'] + parms['duration']

            if self.t - self.trial_times[-1] >= stop:
                self.stim_dict[name].parameters.on = False
                to_del.append(stim_tup)

        for stim_tup in to_del:
            self.active_stims.remove(stim_tup)

    def state_generator(self):
        # For some reason, update gets called immediately when it's registered
        # as a function controller... so we add this yield to avoid any drawing
        # for that frame
        yield

        new_stims = []
        trial_num = 0
        for trial in self.trials:
            self.trial_times.append(self.t)
            trial_num += 1

            # Note that the order of activates, deactivates and yields is
            # critical for instantaneous stimuli to appear properly (or at all)
            for stimulus in trial:
                for name, parms in stimulus.items():
                    while self.t - self.trial_times[-1] < parms['start']:
                        self.deactivate_stims()
                        self.log_response()
                        self.activate_stims(new_stims)
                        yield

                    new_stims.append((name, parms))

            self.deactivate_stims()
            self.log_response()
            self.activate_stims(new_stims)
            yield

            while True:
                self.deactivate_stims()
                if len(self.active_stims) == 0:
                    break
                self.log_response()
                yield

            self.log_response(reset=True)
            
            if trial_num == self.trials_to_run:
                trial_num = 0
                self.vision_egg.pause()
                yield

        self.vision_egg.pause()
        yield
