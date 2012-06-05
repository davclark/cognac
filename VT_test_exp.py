#! /usr/bin/env python

"""
This is a template for how to use the voice trigger module.

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

I've found that values ~800-1024 optimally balance RT sampling rate w/ dropped frames.

-- Geoff.Brookshire@gmail.com (5-24-2012)

"""

#TODO
# Lots more "[Errno Input overflowed] -9981" when using the circle stims

import sys
from cognac.StimController import Response, Event, Trial, StimController
from cognac.SimpleVisionEgg import *
<<<<<<< HEAD
from cognac.VoiceTrigger import VoiceResponse, VoiceTriggerController
=======
import cognac.VoiceTrigger as VoiceTrigger
>>>>>>> fixed faulty VoiceTrigger import in VT_test_exp.py

from pygame import K_SPACE
import random
from VisionEgg.Text import Text
from VisionEgg.MoreStimuli import FilledCircle
from VisionEgg.Textures import Texture, TextureStimulus

class PicStim(TextureStimulus):
    """ Stimulus object for showing a picture.
    """
    stimdir = '/Users/Daniel_Casasanto/Documents/stimuli/faces/color/background/green/'
    def __init__(self, filename):

        texture = Texture(self.stimdir + filename)  # load the picture
        self.type = 'picture'

        TextureStimulus.__init__(self,
                                 texture = texture,
                                 size = (300, 400),
                                 **std_params)

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
    """Here's a trial for this experiment, which you give a FaceStim instance"""
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

################################
# input information at startup #
################################
subject = '0'
exp_type = None
while exp_type not in ['p', 'c', 't', 'all']:
    exp_type = raw_input('Text, Pictures, or Circles? (t/p/c/all): ').lower()

##############
# Initialize #
##############
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

#pic_names = ['01F_HA_C.bmp', '38M_HA_C.bmp', '03F_HA_C.bmp']
#pict_stims = [PicStim(fn) for fn in pic_names]
text_stims = [TextStim(f) for f in (':-)', ':-(', ':-o')]
circ_stims = [CircleStim() for n in range(3)]

if exp_type == 't':
    trial_stims = text_stims
elif exp_type == 'c':
    trial_stims = circ_stims
elif exp_type == 'p':
    print "This won't work if you haven't specified the right filepath for pictures."
    trial_stims = pict_stims
elif exp_type == 'all':
    #trial_stims = pict_stims + circ_stims + text_stims
    trial_stims = circ_stims + text_stims

vision_egg.set_stimuli([rest,fixation,blank]+trial_stims)
### ! Make sure you add the voice controller ! ### 
vision_egg.presentation.add_controller(None, None, voice_controller)

trials = [ExpTrial(s) for s in trial_stims]
random.shuffle(trials)
final_trial = Trial([Event(rest, start = 0, duration = 3)], unlogged = True) 
trials += [final_trial] 

stim_control = StimController(trials, vision_egg, pause_event=Event(rest,0,0))

stim_control.run_trials(len(trials))
stim_control.writelog(stim_control.getOutputFilename(subject, 'VT_test'))


