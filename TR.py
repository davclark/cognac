import VisionEgg
from VisionEgg.Core import get_default_screen, 
from VisionEgg.FlowControl import Presentation
from VisionEgg.ResponseControl import KeyboardResponseController

#################################
# Set some VisionEgg Defaults:  #
#################################

VisionEgg.config.VISIONEGG_SCREEN_W = 1024
VisionEgg.config.VISIONEGG_SCREEN_H = 768
VisionEgg.config.VISIONEGG_FULLSCREEN = 1


class TRStimulusController:
    """This is a relatively simple controller that simply updates what's on the
    screen every TR (which is the next occurrence of keyboard input of '5' after
    the TR length is exceeded.  Currently it sets one stimulus on, and all
    others off, though we may want to change that to turn a list of stimuli on
    eventually"""
    
    # Expected length of 1 TR
    TR = 2.0
    # Time interval after which we assume we missed the trigger
    eps = 0.1

    t = 0
    trial_times = None

    keyboard_controller = None
    presentation = None
    screen = None

    def __init__(self, stims, stim_seq, TR=None, eps=None):
        if TR:
            self.TR = TR 

        self.stims = stims
        self.stim_seq = stim_seq

        self.trial_times = []
        self.state = self.state_generator()


        self.screen = get_default_screen()
        # background black (RGBA)
        self.screen.parameters.bgcolor = (0.0,0.0,0.0,0.0)

        self.keyboard_controller = KeyboardResponseController()
        viewport = Viewport(screen=screen,
                    size=screen.size,
                    stimuli=self.stims)

        # compute total length and then adjust our TR
        go_duration = (self.TR * len(stim_seq), 'seconds')
        self.presentation = Presentation(go_duration=go_duration,
                viewports=[viewport])
        self.presentation.add_controller(None, None, 
                FunctionController(during_go_func=self.update) )
        self.presentation.add_controller(None, None, keyboard_response)


    def run(self):
        self.presentation.go()
        self.screen.close()    

    def update(self, t):
        self.t = t
        self.state.next()

    def blank_all_stims(self):
        for stim in self.stims:
            stim.parameters.on=False

    def state_generator(self):
        for stim in self.stim_seq:
            self.trial_times.append(self.t)
            self.blank_all_stims()
            stim.parameters.on=True

            # Don't even bother 'til we're close to the expected TR time
            while self.t - self.trial_times < self.TR - self.eps:
                yield

            while self.t - self.trial_times < self.TR + self.eps:
                # Handle the rare case when a key might register between
                # function calls
                while True:
                    keys = self.keyboard_controller.get_responses_since_go()
                    times = 
                        self.keyboard_controller.get_time_responses_since_go()
                    if len(keys) == len(times):
                        break
                keys.reverse()
                times.reverse()
                i = keys.index('5')
                if i and times[i] > self.trial_times:
                    break
                else:
                    yield
