"""Simple script to set up and run vision egg in the way that we often need to
do"""

import VisionEgg
from VisionEgg.Core import get_default_screen, Viewport
from VisionEgg.FlowControl import Presentation, FunctionController
from VisionEgg.ResponseControl import KeyboardResponseController
from VisionEgg.DaqKeyboard import KeyboardTriggerInController

#################################
# Set some VisionEgg Defaults:  #
#################################

VisionEgg.start_default_logging()
VisionEgg.watch_exceptions()

VisionEgg.config.VISIONEGG_SCREEN_W = 1024
VisionEgg.config.VISIONEGG_SCREEN_H = 768
VisionEgg.config.VISIONEGG_FULLSCREEN = 1


## Now for our code

RESERVED_WORDS = 'start', 'stop', 'duration', 'log', 'response'

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

    def __init__(self):
        self.screen = get_default_screen()

    def run(self, stimuli, update, pause=None, go_duration=('forever',), trigger=None):
        viewport = Viewport(screen=self.screen, size=self.screen.size, 
                           stimuli=stimuli)

        presentation = Presentation(go_duration=go_duration,
                viewports=[viewport], trigger_go_if_armed=0)
        presentation.add_controller(None, None,
                     FunctionController(during_go_func=update, 
                                        between_go_func=pause) )

        self.keyboard_controller = KeyboardResponseController()
        presentation.add_controller(None, None, self.keyboard_controller)

        if trigger:
            trigger_controller = KeyboardTriggerInController(trigger)
            presentation.add_controller(presentation, 'trigger_go_if_armed',
                                        trigger_controller)

        presentation.go()

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

