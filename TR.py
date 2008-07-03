"""stim.TR is a library for running simple stimuli in the scanner.  It just
returns all the buttons pressed - it doesn't do anything clever in terms of
responding to subject input.  It is used by simpleComplex_OneGo.py, if you want
to refer to an example of how to use this"""

import VisionEgg
from VisionEgg.Core import get_default_screen, Viewport
from VisionEgg.FlowControl import Presentation, FunctionController
from VisionEgg.ResponseControl import KeyboardResponseController

# I *really* think you need this:
from VisionEgg.DaqKeyboard import KeyboardTriggerInController
from pygame.locals import K_5

import yaml

#################################
# Set some VisionEgg Defaults:  #
#################################

VisionEgg.start_default_logging()
VisionEgg.watch_exceptions()

VisionEgg.config.VISIONEGG_SCREEN_W = 1024
VisionEgg.config.VISIONEGG_SCREEN_H = 768
VisionEgg.config.VISIONEGG_FULLSCREEN = 1

class MultiStimHelper:
    """Meant to be embedded in MultiStim"""
    stims = None

    def __init__(self, stims):
        # We need to do this because of our __setattr__
        self.__dict__['stims'] = stims

    def __setattr__(self, name, value):
        for s in self.stims:
           setattr(s.parameters, name, value)

    def __getattr__(self, name):
        return [getattr(s.parameters, name) for s in self.stims]


class MultiStim:
    """Very simple surrogate class to get or set values of multiple classes at
    once."""
    parameters = None

    def __init__(self, *stims):
        self.parameters = MultiStimHelper(stims)


class TRStimController:
    """This is a relatively simple controller that simply updates what's on the
    screen every TR (which is the next occurrence of keyboard input of '5' after
    the TR length is exceeded.  Currently it sets one stimulus on, and all
    others off, though we may want to change that to turn a list of stimuli on
    eventually"""
    # 3T laptop forp sends TTL pulses as "5"; buttons as "1","2","3","4"
    # John used to do things this way:
    # trigger_in_controller = KeyboardTriggerInController(pygame.locals.K_5)
    
    # Expected length of 1 TR
    TR = 2.0
    # Time interval after which we assume we missed the trigger
    eps = 0.1

    t = 0
    trial_times = None
    missed_trigs = None
    stim_list = []
    stim_dict = {}
    stim_seq = []

    keyboard_controller = None
    presentation = None
    screen = None

    def __init__(self, TR=None, eps=None):
        # Get the initial setup
        if TR:
            self.TR = TR 
        if eps:
            self.eps = eps

        self.trial_times = []
        self.missed_trigs = []
        self.state = self.state_generator()

        self.screen = get_default_screen()

        # background black (RGBA)
        self.screen.parameters.bgcolor = (0.0,0.0,0.0,0.0)

        self.keyboard_controller = KeyboardResponseController()
        self.firstTTL_trigger = KeyboardTriggerInController(K_5)
        
    def set_stims(self, stim_list, stim_dict, stim_seq_file): 
        self.stim_list = stim_list
        self.stim_dict = stim_dict
        self.stim_seq = yaml.load(stim_seq_file)

        viewport = Viewport(screen=self.screen,
                    size=self.screen.size,
                    stimuli=self.stim_list)

        # Need to at least wait for the first trigger if this is going to work.
        go_duration = (self.TR * len(self.stim_seq), 'seconds')
        self.presentation = Presentation(go_duration=go_duration,
                trigger_go_if_armed=0,
                viewports=[viewport])

        self.presentation.add_controller(None, None, 
                FunctionController(during_go_func=self.update) )
        self.presentation.add_controller(None, None, self.keyboard_controller)
        # Adding this so that we can start the stimuli ahead of time
        self.presentation.add_controller(self.presentation,'trigger_go_if_armed',
                                    self.firstTTL_trigger)

    def run(self):
        self.presentation.go()
        self.screen.close()    

    def update(self, t):
        self.t = t
        try:
            self.state.next()
        except StopIteration:
            # shouldn't really happen, what with epsilon and all...
            self.blank_all_stims()

    def blank_all_stims(self):
        for stim in self.stim_list:
            stim.parameters.on=False

    def state_generator(self):
        for stim_info in self.stim_seq:
            self.trial_times.append(self.t)
            self.blank_all_stims()
            try:
                for stim_name, params in stim_info.items():
                    stim = self.stim_dict[stim_name]
                    stim.parameters.on = True
                    try:
                        for name, value in params.items():
                            setattr(stim.parameters, name, value)
                    except AttributeError:
                        # params was None or something else we don't deal with
                        pass
            except AttributeError:
                # We assume a no-colon single token / key
                self.stim_dict[stim_info].parameters.on = True


            # Don't even bother 'til we're close to the expected TR time
            while self.t - self.trial_times[-1] < self.TR - 2*self.eps:
                yield

            while self.t - self.trial_times[-1] < self.TR + self.eps:
                # Handle the rare case when a key might register between
                # function calls
                while True:
                    keys = self.keyboard_controller.get_responses_since_go()
                    times = \
                        self.keyboard_controller.get_time_responses_since_go()
                    if len(keys) == len(times):
                        break

                i = None
                try:
                    # Find the last value of '5' without inline reversal of keys/times
                    # VisionEgg returns "responses" as a list of lists of chars, not just a list of chars...
                    i = len(keys)-1-list(reversed(keys)).index(['5'])
                except ValueError:
                    pass
                
                # If anybody presses the escape key, quit entirely.
                try:
                    needToQuit = keys.index(['escape'])
                    #self.presentation = None
                    #exit()
                except ValueError:
                    pass

                if i and times[i] > self.trial_times[-1]:
                    break
                else:
                    yield

            if self.t - self.trial_times[-1] >= self.TR + self.eps:
                # We missed a TR (we think)
                self.missed_trigs.append(self.t)
                self.t = self.trial_times[-1] + self.TR


    def get_responses(self, timeToSubtract=0, min_interval=2.0/60):
        """
        This function isn't especially elegant, but it's functional.

        VisionEgg's keyboard libraries records a keypress and timestamp every
        time something is down.  So if a key is held down for 100 ms, there will
        be an entry in the keylist for every sample during that 100ms.  This is
        a bit much; I'd rather just save onsets and offsets for every key.  This
        function evaluates that.
        """

        ''' 
        If we're using the FORP, this isn't necessary, as events have no duration; 
        they are represented as instantaneous keypresses.

        -- John
        '''

        response = self.keyboard_controller.get_responses_since_go()
        responseTime = self.keyboard_controller.get_time_responses_since_go()

        # If I've only got one item in my response list, then it's silly to worry about onset/offset.  Just keep it.
        if len(response) < 2:
            return (response,responseTime)
        
        # Save the first response, as by definition that's the first onset:
        goodResp = [response[0]]
        goodRespTime = [responseTime[0]-timeToSubtract]

        # Now step through every other item in the response list to check for unique-ness.
        for i in range(1,len(responseTime)):

            if (not(response[i] == response[i-1]) or \
                    (responseTime[i] - responseTime[i-1] > \
                         min_interval)):
                # ie, if something changed, or we have a long gap:
                
                offsetResp = [] # we might want to save an offset
                for item in response[i-1]: # loop through last item's data
                    if (responseTime[i] - responseTime[i-1] < \
                            min_interval) and \
                            not(item in response[i]):
                        # Bit clunky.  Basically, holding down a key while pressing another creates
                        # a unique response.  So if you only let up one of those keys, code the
                        # offset just for that key.
                        offsetResp.append(item+'_Off')
                    else:
                        # it's been long enough that everything that was on should be called off.
                        offsetResp.append(item+'_Off')

                if len(offsetResp) > 0:
                    # If there's offset stuff to worry about, save it.
                    goodResp.append(offsetResp)
                    goodRespTime.append(responseTime[i-1]-timeToSubtract)
                
                # Save the new (onset) response.
                goodResp.append(response[i])
                goodRespTime.append(responseTime[i]-timeToSubtract)

        # The final event should be an offset for whatever was down.
        offsetResp = []
        for item in response[-1]:
            offsetResp.append(item+'_Off')
        goodResp.append(offsetResp) #goodResp.append(response[-1]+'_Off')
        goodRespTime.append(responseTime[-1]-timeToSubtract)

        return (goodResp, goodRespTime)
