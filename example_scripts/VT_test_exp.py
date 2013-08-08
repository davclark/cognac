#! /usr/bin/env python

"""
This is a template for how to use the VoiceTrigger module.

At the beinning, you're prompted to use one of a few types of stims. To
do the demo w/ pictures, just add the correct file paths and uncomment the
lines of code that initialize the pic stims.

See the ExpTrial class def for an example of how to use VoiceTrigger.VoiceResponse.

Sometimes things get confused and you'll see the pyaudio error:
    "[Errno Input overflowed] -9981"
This means pyaudio failed read the audio stream and dropped an audio frame. If
too many of these happen, the RTs won't be registered and the sound files will
be messed up. To reduce these, you have to play with the value of CHUNK_SIZE
in VoiceTrigger.py. Unfortunately, these differ between machines.

Weirdly, there are more "[Errno Input overflowed] -9981" when using the circle stims
than when using text stims.

I've found that values ~800-1024 optimally balance RT sampling rate w/ dropped frames.


-- Geoff.Brookshire@gmail.com (5-24-2012)

"""


import sys
from cognac.StimController import Response, Event, Trial, StimController
from cognac.SimpleVisionEgg import *
from cognac.VoiceTrigger import VoiceResponse, VoiceTriggerController

import random
from VisionEgg.Text import Text
from VisionEgg.MoreStimuli import FilledCircle
from VisionEgg.Textures import Texture, TextureStimulus

#############
# Structure #
############# 

class TextStim(Text):
    """Stimulus object -- accepts string of a dumb emoticon"""
    def __init__(self, text):
        self.text = text 
        self.color = [random.random() for i in (1,2,3)]
        self.type = 'text'
        
        Text.__init__(self, text = text, font_size = 50,
                      color = self.color, **std_params)

class CircleStim(FilledCircle):
    """ Stimulus object.
    Shows a randomly colored circle in the center of the screen.
    """
    def __init__(self):
        self.color = [random.random() for i in (1,2,3)]
        self.type = 'circle'
        
        FilledCircle.__init__(self, color = self.color, radius = 50, **std_params)

class ExpTrial(Trial):
    """Here's a trial for this experiment, which you give a Stimulus instance"""
    def __init__(self, stim):
        voice_resp = VoiceResponse(label = 'speak',
                        audio_controller = voice_controller)

        events=[Event(fixation, start=0, duration=2.0),
                Event(stim, start=2, duration=.5,
                    log={'type': stim.type,
                        'subject': subject,
                        'VT_threshold': voice_controller.THRESHOLD}),
                Event(blank, start=2, duration=2.5,
                    response = voice_resp)]

        Trial.__init__(self,events)

##############
# Initialize #
############## 

subject = '0'
exp_type = None
while exp_type not in ['c', 't', 'both']:
    exp_type = raw_input('Text or Circles? (t/c/both): ').lower()

# Initialize the Controller first
voice_controller = VoiceTriggerController(threshold = 1000, chunk_size = 800)
# dynamically set the trigger threshold
voice_controller.set_threshold_gui(display_scale = 1/20.)

# Then initialize vision egg
vision_egg = SimpleVisionEgg()
screen = vision_egg.screen
screen.parameters.bgcolor = [0,0,0]
xlim, ylim = vision_egg.screen.size # screen size in pixels

###########
# Stimuli #
###########
std_params = {'anchor': 'center',
              'position': (xlim/2,ylim/2), 
              'on': False} 

rest = Text(text = "All done! Wait for soundfiles to save before closing...",
            **std_params)
fixation = Text(text="+", font_size=55, **std_params)
blank = Text(text="", **std_params)

text_stims = [TextStim(f) for f in (':-)', ':-(', ':-o')]
circ_stims = [CircleStim() for n in range(3)]

if exp_type == 't':
    trial_stims = text_stims
elif exp_type == 'c':
    trial_stims = circ_stims
elif exp_type == 'both':
    trial_stims = circ_stims + text_stims

random.shuffle(trial_stims)
trials = [ExpTrial(s) for s in trial_stims]
final_trial = Trial([Event(rest, start = 0, duration = 3)], unlogged = True) 
trials += [final_trial] 

######################
# Run the experiment #
######################

vision_egg.set_stimuli([rest,fixation,blank]+trial_stims)
# Add the voice controller here ### 
vision_egg.presentation.add_controller(None, None, voice_controller) 
stim_control = StimController(trials, vision_egg)

stim_control.run_trials('all')
stim_control.writelog(stim_control.getOutputFilename(subject, 'VT_test'))

# Save the soundfiles during resting points or after the experiment is done.
# This will prevent the hardware access from messing with the stim/response
# timing. Remember to save the soundfiles!
voice_controller.write_soundfiles()

