"""time.py is a simple controller designed to show stimuli at specific times.  A
reference for usage is in luminanceCompression2.py"""

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

    # KeyboardController from VisionEgg
    keyboard_controller = None


    def __init__(self, stim_dict, trials, keyboard_controller=None):
        self.trial_times = []
        self.stim_dict = stim_dict
        self.trials = trials
        self.active_stims = []
        self.keyboard_controller=keyboard_controller

        self.state = self.state_generator()
        self.log = {'trial_times': self.trial_times}
        self.responses = {}

    def compute_go_duration(self):
        """This should run through the trials, find the latest stimulus and add
        this info up, putting it in go_duration"""
        pass


    def update(self, t):
        # print "update called with t=%f" % t
        self.t = t
        self.state.next()


    def pause(self):
        """I currently can't figure out how to make this work... it doesn't
        depend on whether the duration is 'forever' or not"""
        print "pause called"
        self.stim_dict['text_disp'].parameters.on = True
        self.active_stims = [('text_disp', {'stop': 0})]
        yield


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
                            self.log[log_k].append(v)
                        except KeyError:
                            self.log[log_k] = [v]
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
        for t in self.active_stims:
            name, parms = t
            try:
                stop = parms['stop']
            except KeyError:
                stop = parms['start'] + parms['duration']

            if self.t - self.trial_times[-1] > stop:
                self.stim_dict[name].parameters.on = False
                to_del.append(t)

        for t in to_del:
            self.active_stims.remove(t)

    def state_generator(self):
        self.stim_dict['text_disp'].parameters.on = True
        self.active_stims = [('text_disp', {'stop': 0})]
        yield

        new_stims = []
        for trial in self.trials:
            self.trial_times.append(self.t)

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

            while len(self.active_stims) > 0:
                self.deactivate_stims()
                self.log_response()
                yield

            self.log_response(reset=True)
