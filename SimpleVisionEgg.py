"""Simple script to set up and run vision egg in the way that we often need to
do.  This module serves simply to set things up and keep track of VisionEgg
related values.  It shouldn't really _do_ anything."""

import VisionEgg
from VisionEgg.Core import get_default_screen, Viewport
from VisionEgg.FlowControl import Presentation, FunctionController
from VisionEgg.ResponseControl import KeyboardResponseController
from VisionEgg.DaqKeyboard import KeyboardTriggerInController
from VisionEgg.ParameterTypes import NoneType

#################################
# Set some VisionEgg Defaults:  #
#################################

VisionEgg.start_default_logging()
VisionEgg.watch_exceptions()

# Could set constraints here if you don't want to muck with config files
# VisionEgg.config.VISIONEGG_SCREEN_W = 1026
# VisionEgg.config.VISIONEGG_SCREEN_H = 768
# VisionEgg.config.VISIONEGG_FULLSCREEN = 1


## Now for our code
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

class SimpleVisionEgg:
    keyboard_controller = None
    trigger_controller = None
    screen = None
    presentation = None
    keys = None
    presses = None
    releases = None

    def __init__(self):
        """We break up initialization a bit as we need to go back and forth with
        some information.  In this case, we need screen size before specifying
        the stimuli"""
        self.screen = get_default_screen()
        self.keys = []
        self.presses = []
        self.releases = []

    def set_stimuli(self, stimuli, trigger=None, kb_controller=False):
        """Now that we have our stimuli, we initialize everything we can"""
        viewport = Viewport(screen=self.screen, size=self.screen.size, 
                           stimuli=stimuli)

        self.presentation = Presentation(viewports=[viewport],
                check_events=False)

        if trigger:
            trigger_controller = KeyboardTriggerInController(trigger)
            self.presentation.add_controller(self.presentation, 
                                    'trigger_go_if_armed', trigger_controller)
            self.presentation.set(trigger_go_if_armed=0)

        if kb_controller:
            self.keyboard_controller = KeyboardResponseController()
            self.presentation.add_controller(None, None, self.keyboard_controller)


    def set_functions(self, update=None, pause_update=None):
        """Interface for stim.time.StimulusController or similar"""
        self.presentation.add_controller(None, None,
                     FunctionController(during_go_func=update, 
                                        between_go_func=pause_update,
                                        return_type=NoneType) )


    def go(self, go_duration=('forever',)):
        self.presentation.parameters.go_duration = go_duration
        self.presentation.go()

    def pause(self):
        self.presentation.parameters.go_duration = (0, 'frames')

    def get_new_response(self, t, min_interval=2.0 / 60, releases=False):
        """(key, press) = get_new_response(self, t, min_interval=2.0 / 60)

        DEPRECATED!

        Use this function to get responses from the keyboard controller in real
        time.

        Returns (None, None) if no new response is available.
        Maintains three instance variables - keys, presses and releases, which
        you can also access directly (but they won't be updated during loops
        where you don't call this function)

        This function makes a number of assumptions and is a little brittle
        right now.  By not hard-coding the min_interval and maybe using key
        presses and release events directly, we'd have a much better function.
        But I don't really care right now.

        DJC
        """
        raise DeprecationWarning("please use pygame directly, as in" +
                                 "StimController.Response")
        # Note - this is deprecated anyway, but it'd probably make more sense to
        # use the keyboard_controller.get_responses() to simply get the keys
        # that are down _right_now_
        press_time = self.keyboard_controller.get_time_last_response_since_go()
        key = self.keyboard_controller.get_last_response_since_go()

        # Our first response!
        if len(self.keys) == 0:
            if key:
                self.keys.append(key)
                self.presses.append(press_time)
                self.releases.append(None)

                if releases:
                    return (key, None)
                else:
                    return (key, press_time)

            else:
                return (None, None)

                    
        # We haven't seen a key press for min_interval
        if t >= press_time + min_interval and not self.releases[-1]:
            # This is only approximate!
            self.releases[-1] = t 
            if releases:
                return (self.keys[-1], t)
            else:
                return (None, None)

        # We've seen a release, or we see a new key
        if (self.releases[-1] and press_time > self.releases[-1]) or \
                key != self.keys[-1]:
            if not self.releases[-1]:
                self.releases[-1] = press_time
            self.keys.append(key)
            self.presses.append(press_time)
            self.releases.append(None)

            if releases:
                return (key, None)
            else:
                return (key, press_time)

        return (None, None)

    def get_responses(self, timeToSubtract=0, min_interval=2.0/60):
        """
        Use this function to post-process the results of a KeyboardController

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

