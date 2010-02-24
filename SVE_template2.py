#!/usr/bin/env python
# This must be the first line of your program.

"""
This is a template for how to use SimpleVisionEgg and StimController.

It uses a lot of list comprehensions, so make sure you know what those do.
Generally, though, best to avoid fancy python tricks so beginners don't freak
out!

-Dav
"""

# You need to import these in addition to whatever else you do
from StimController import Response, Event, Trial, StimController
from SimpleVisionEgg import *
# If using a buttonbox:
#from parallel import respbox

from pygame import K_SPACE
import random
from VisionEgg.Text import Text
from VisionEgg.MoreStimuli import FilledCircle


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
center = (xlim/2,ylim/2) 
rest = Text(text="Press space to begin.", position=center, anchor='center',
            on=False)
def fixation1():
    Text(text=random.choice("GGGGGGGGNN"), font_size=55, position=center, anchor='center', on=False);
fixation2 = Text(text=random.choice("GGGGGGGGNN"), font_size=55, position=center, anchor='center', 
                on=False)
				
cues = ['G','G','G','G','G','G','G','G','N','N']
fixation = [Text(text=cue, font_size=55, position=center, anchor='center', 
                on=False)
				for cue in cues]


# Note, prior to python3, need a float to avoid integer division
x_positions = [xlim * frac / 6.0 for frac in range(1, 5)]
trial_stims = [FilledCircle(radius=10.0, position=(xpos, ylim/2), on=False)
               for xpos in x_positions]

# Give set_stimuli a list of stimulus objects as well as
# the pygame keypress which you want to begin the trials
# Setting the trigger here seems a little out of place... something to clean up
# at a later date
vision_egg.set_stimuli([rest,fixation]+trial_stims, trigger=K_SPACE)

#############
# Structure #
#############
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
            dont give it a limit if you do this"""

def event_list(stim_num):
    return [Event(random.choice(fixation), start=0, duration=2.0),
            Event(trial_stims[stim_num], start=2, duration=.5,
                  log={'stim.num': stim_num},
                  # Need some way for the Response to dynamically log the
                  # x.position and update it
                  response=Response(label='press',limit=('z','/')) ),
            Event(None, start=2, duration=2.5) ]

# Trials are initialized with an "events" arg which is a list of Event instances
# trial_stims * 4 gives us 20 Trials
trials = [Trial(event_list(stim_num)) 
            for stim_num in range(len(trial_stims)) * 4]
random.shuffle(trials)

# pause_event begins each block after a SPACE press.
# 'rest' is the name of my text stim
stim_control = StimController(trials, vision_egg, pause_event=Event(rest,0,0))

stim_control.run_trials()
stim_control.writelog('example.log')
