#! /usr/bin/env python
# This must be the first line of your program.

""" This is a template for how to use SimpleVisionEgg and StimController.
It shows faces and collects RTs on the Z and / keys.
Improve it as you see fit.
See trunk/geoff/hemifield_faces/hemifield_faces.py for a real example.
-geoff"""

# You need to import these in addition to whatever else you do
from StimController import Response, Event, Trial, StimController
from SimpleVisionEgg import *
# If using a buttonbox:
#from parallel import respbox

from pygame import K_SPACE
import random
from VisionEgg.Text import Text
from VisionEgg.MoreStimuli import FilledCircle

positions = [100, 250, 500, 750, 900]

class TargetStim(FilledCircle):
    """A circle that goes on different places on the x axis"""
    def __init__(self, pos):
        self.pos=pos
        
        FilledCircle.__init__(self, radius=10.0,
                              position=(positions[self.pos],240),
                              on=False)

class ExpTrial(Trial):
    """Here's a trial for this experiment, which you give a 
	targetStim instance"""
    def __init__(self, TS):
        events=[Event(fixation, start=0, duration=2.0),
                Event(TS, start=2, duration=.5,
                    log={'pos': TS.pos,
                         'x_position': positions[TS.pos]}),
                Event(blank, start=2, duration=2.5,
                    response = Response(label='press',limit=('z','/')))]

        Trial.__init__(self,events)

"""
Events take:
first, the stim used, a VisionEgg.Stimulus class instance
start, duration, stop -- times in seconds since beginning of Trial
log -- a dict
response - a Response instance
    which take args: label (how the response is named in the csv)
                    limit -- if you give it key values (e.g. ("l","m") accepts only those)
                    buttonbox -- a parallel.respbox.RespBox instance
                        this gives back the integer 2^x, x indexes the finger
                        dont give it a limit if you do this
"""

##############
# Initialize #
##############
vision_egg = SimpleVisionEgg()
screen = vision_egg.screen
screen.parameters.bgcolor = [0,0,0]
xlim, ylim = vision_egg.screen.size # screen size in pixels
#box = respbox.RespBox()

###########
# Stimuli #
###########
std_params = {'anchor': 'center', # for text display objects 
              'position': (xlim/2,ylim/2), 
              'on': False} 

rest = Text(text="Press space to begin.", **std_params)
fixation = Text(text="+", font_size=55, **std_params)
blank = Text(text="", **std_params)


trial_stims = [TargetStim(x) for x in (0, 1, 2, 3, 4)]
trials = [ExpTrial(s) for s in trial_stims]
random.shuffle(trials)
# A list of trials, using a super-pythonic list comprehension
# Trials are initialized with an 'events' arg which is a list of Event instances

vision_egg.set_stimuli([rest,fixation,blank]+trial_stims, trigger=K_SPACE)
# Give set_stimuli a list of stimulus objects as well as
# the pygame keypress which you want to begin the trials
stim_control = StimController(trials, vision_egg, pause_event=Event(rest,0,0))
# pause_event begins each block after a SPACE press.
# 'rest' is the name of my text stim

stim_control.run_trials()
stim_control.writelog('example.log')
