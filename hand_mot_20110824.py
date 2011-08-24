#! /usr/bin/env python
""" Show pictures of crossed valence (pos/neg) and motivation (app/with).
Take responses with two buttons, one for each hand.
Ss do 2 blocks of trials. In one, they approach things with a left-handed
button press. In the other block, approach things with a right-handed 
button press. Counterbalanced order.
"""
#TODO
# make sure an equal number of stims from each category make it into the 2 blocks
# make run_trials default to running all trials
# Does SimpleVisionEgg have to check screen size to go fullscreen?

STIM_DIRECTORY = '/Users/Daniel_Casasanto/Documents/stimuli/motivation/shrunk/'
SVE_DIRECTORY = '/Users/Daniel_Casasanto/Documents/functions/python/SimpleVisionEgg/SimpleVisionEgg/'

import sys
sys.path.append(SVE_DIRECTORY)  # add the SimpleVisionEgg functions to path
from random import shuffle, randint
from pygame import K_SPACE
from VisionEgg.Text import Text
from VisionEgg.WrappedText import WrappedText
from VisionEgg.Textures import Texture, TextureStimulus
import ExptHelpers as EH
from StimController import Response, Event, Trial, StimController
from SimpleVisionEgg import *

# get information from subject before initializing vision egg
# global variables for experiment condition coding
SUBJECT = raw_input('Participant: ')
HANDEDNESS = EH.subject_info('Condition (S/D): ', ('S', 'D'))
exp_version = EH.subject_info('Expt Version (1/2): ', (1, 2))
if exp_version == 1:
    APPROACH_SIDE_FIRST = 'LEFT'
    WITHDRAW_SIDE_FIRST = 'RIGHT'
elif exp_version == 2:
    APPROACH_SIDE_FIRST = 'RIGHT'
    WITHDRAW_SIDE_FIRST = 'LEFT'

# initialize vision egg
vision_egg = SimpleVisionEgg()
screen = vision_egg.screen
screen.parameters.bgcolor = (0, 0, 0)
xlim, ylim = vision_egg.screen.size # size of the screen in pixels

# a few useful stim objects
std_params = {'anchor': 'center', # for text display objects
              'position': (xlim/2, ylim/2), 'on': False}
fixation = Text(text = "+", font_size = 55, **std_params)
blank = Text(text = "", **std_params)
rest_screen = Text(text = "Press SPACE to continue.", **std_params)

###########################
# A couple useful classes #
###########################
class PicStim(TextureStimulus):
    """ Stimulus object for showing a picture.
    """
    def __init__(self, picname):
        self.picname = picname
        self.motiv = picname[0]
        self.valen = picname[2]

        texture = Texture(STIM_DIRECTORY + picname)  # load the picture

        TextureStimulus.__init__(self,
            texture = texture,
            size = (500, 400), 
            **std_params)

class ExpTrial(Trial):
    """Here's a trial for this experiment.
    It's initialized with a PicStim instance.
    """
    def __init__(self, picstim, approach_hand):
        events=[Event(fixation, start = 0, duration = 2.0),
                Event(picstim, start = 2, duration = 0.5,
                    log={'pic_name': picstim.picname,
                        'motivation': picstim.motiv,
                        'valence': picstim.valen,
                        'subject': SUBJECT,
                        'handed': HANDEDNESS,
                        'app_side_first': APPROACH_SIDE_FIRST,
                        'approach_hand': approach_hand}),
                Event(blank, start = 2, duration = 2.5,
                    response = Response(label = 'press', limit = ('a', "'")))]

        Trial.__init__(self,events)

class InstructTrial(Trial):
    """ make instructions stim and trial given a sentence.
    <InstructTrial instance>.stim has to be passed to vision_egg.set_stimuli.
    """
    stim = None # Holds the VisionEgg stimulus object

    def __init__(self, sentence):
        self.stim = WrappedText(text = sentence, font_size = 50,
            position=(xlim/2, ylim/2), on = False)
        
        events = [Event(blank, start = 0, duration = .3), 
            Event(self.stim, start = .3, duration = 1000, 
                on_keypress = True,  # end the event with a keypress
                response = Response(label = 'instruct', limit = 'space'))]
                #response = Response(label = None, limit = 'space'))]
        Trial.__init__(self, events)

        
#####################
# Set up the trials #
#####################
motiv = ('a', 'w')
valen = ('p', 'n')
conds = [i_m + "_" + i_v for i_m in motiv for i_v in valen]
pic_list = [cond + str(n) + '.jpg' for n in range(1, 2) for cond in conds] 
stim_list = [PicStim(pic) for pic in pic_list]
# set up which hand is used for approach in each block of trials for logging
trials1 = [ExpTrial(p, APPROACH_SIDE_FIRST) for p in stim_list[:len(stim_list)/2]]
trials2 = [ExpTrial(p, WITHDRAW_SIDE_FIRST) for p in stim_list[len(stim_list)/2:]]
shuffle(trials1) #randomize the trial order
shuffle(trials2)
trials = trials1 + trials2 # and put them all together

# and the instructions
instruct_text = ["Welcome to the experiment.\nToday you'll see a lot of pictures.", "If the picture shows something a Nochmani would eat,\npress the %s button to EAT it.\n\nIf the picture shows something a Nochmani would not eat,\npress the %s button to NOT EAT it." % (APPROACH_SIDE_FIRST, WITHDRAW_SIDE_FIRST), "Please press the buttons as quickly as you can.", "Ready to start?"]
instruct_text = [s + "\n\n\nPress SPACE to continue." for s in instruct_text]
instructions = [InstructTrial(s) for s in instruct_text]
switch_text = "That was the first half of the experiment.\n For the next part, you'll do the same thing, but switch hands.\nNow, press the %s button for something a Nochmani would EAT,\nand the %s button for something a Nochmani would NOT EAT.\n\nPlease let the experimenter know when you're ready to go on." % (WITHDRAW_SIDE_FIRST, APPROACH_SIDE_FIRST) 
switch_inst = InstructTrial(switch_text)
# put all the trials together w/ instructions in the right place
all_trials = instructions + trials[:len(trials)/2] + \
    [switch_inst] + trials[len(trials)/2:]

###############
# Run the exp #
###############
exp_stimuli = [rest_screen, fixation, blank, switch_inst.stim] + \
    [s.stim for s in instructions] + stim_list
vision_egg.set_stimuli(exp_stimuli)
#stim_control = StimController(all_trials,
    #vision_egg, pause_event = Event(rest_screen, 0, 0))
stim_control = StimController(all_trials, vision_egg)

stim_control.run_trials(len(all_trials))
stim_control.writelog(stim_control.getOutputFilename(SUBJECT, 'MotivHand'))

print '\n\n\n\n\n\t\tThanks for participating!\n\n\n\n\n'
