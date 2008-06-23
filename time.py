class StimulusController:
    trial_info = TrialInfo()
    trial_iter = None
    state = None
    t = 0
    first_update = False

    def __init__(self, trials):
        self.trial_iter = trials.__iter__()
        self.state = self.state_generator()

    def update(self, t):
        self.t = t
        self.state.next()

    def state_generator(self):
        while True:
            while self.t - self.last < self.trial_info.length:
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

