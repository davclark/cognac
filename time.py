"""time.py is a simple controller designed to show stimuli at specific times.  A
reference for usage is in luminanceCompression2.py"""

from SimpleVisionEgg import SimpleVisionEgg
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


    def __init__(self, stim_dict, trials):
        self.trial_times = []
        self.stim_dict = stim_dict
        self.trials = trials
        self.active_stims = []

        self.state = self.state_generator()

    def compute_go_duration(self):
        """This should run through the trials, find the latest stimulus and add
        this info up, putting it in go_duration"""
        pass


    def update(self, t):
        self.t = t
        self.state.next()

    def deactivate_stims(self):
        for s in self.active_stims:
            if self.t - self.trial_times
            s.parameters.on = False

    def state_generator(self):
        for trial in self.trials:
            self.trial_times.append(self.t)

            for stimulus in trial:
                for name, parms in stimulus:
                    while self.t - self.trial_times[-1] < parms['start']:
                        self.deactivate_stims()
                        yield

                    self.active_stims.append(stim_dict[name])
                    self.active_stims[-1].parameters.on = True

            while len(self.active_stims) > 0:
                yield

            # Start of Trial - White fixation
            self.trial_info = self.trial_iter.next()
            # left_circle.parameters.color = (1.0, 1.0, 1.0)
            left_circle.parameters.on = True
            self.last = self.t

            # while self.t - self.last < self.trial_info.warning:
            #     yield

            # # Warning - change white to black
            # left_circle.parameters.color = (0,0,0)

            if self.trial_info.saccade < self.trial_info.first_bar:
                while self.t - self.last < self.trial_info.saccade:
                    yield

                # Saccade
                left_circle.parameters.on = False
                right_circle.parameters.on = True

                while self.t - self.last < self.trial_info.first_bar:
                    yield

                # First bar
                top_bar.parameters.on = True
                yield # We drop right back in here on the next frame
                top_bar.parameters.on = False

                while self.t - self.last < self.trial_info.second_bar:
                    yield

                # Second bar
                bottom_bar.parameters.on = True
                yield # We drop right back in here on the next frame
                bottom_bar.parameters.on = False
            else:
                while self.t - self.last < self.trial_info.first_bar:
                    yield

                # First bar
                top_bar.parameters.on = True
                yield # We drop right back in here on the next frame
                top_bar.parameters.on = False

                while self.t - self.last < self.trial_info.second_bar:
                    yield

                # Second bar
                bottom_bar.parameters.on = True
                yield # We drop right back in here on the next frame
                bottom_bar.parameters.on = False

                while self.t - self.last < self.trial_info.saccade:
                    yield

                # Saccade
                left_circle.parameters.on = False
                right_circle.parameters.on = True


            while self.t - self.last < self.trial_info.first_bar2:
                yield

            # First bar 2
            top_bar.parameters.on = True
            yield # We drop right back in here on the next frame
            top_bar.parameters.on = False
 
            while self.t - self.last < self.trial_info.second_bar2:
                yield

            # Second bar 2
            bottom_bar.parameters.on = True
            yield # We drop right back in here on the next frame
            bottom_bar.parameters.on = False

            while self.t - self.last < self.trial_info.blank:
                yield

            # Blank 
            right_circle.parameters.on = False

            while keyboard_response.get_time_last_response_since_go() < \
                self.last + self.trial_info.blank:
                    yield

            last_press = keyboard_response.get_time_last_response_since_go()
            time_disp.parameters.text = \
                    str(int(round((self.trial_info.second_bar2 - 
                        self.trial_info.first_bar2) * 1000)))
            time_disp.parameters.on = True

            while keyboard_response.get_time_last_response_since_go() <= \
                last_press + 0.5:
                    yield

            if keyboard_response.get_last_response_since_go() == 'q':
                exit()

            time_disp.parameters.on = False

