''' 
Classes to register voice-trigger RTs and save wave-files of those resps.

To be sure that your stim timing goes smoothly, ALWAYS try to save your sound
file at a time when nothing else is happening by specifying its duration to not
overlap with other important events. Save sounds from your experiment script using
voice_controller.write_soundfiles(). See VT_test_exp.py for an example.

You sometimes see a few lines of the "[Errno Input overflowed] -9981" upon startup,
but it doesn't seem to affect anything. Fiddle with CHUNK_SIZE to change these --
the optimum value differs from computer to computer. More info in the
VoiceTriggerController docstring.

Make sure python doesn't quit before the final recording is finished!
That will prevent it from being saved.

Records a soundfile more often than for every trial, but includes a line in the
logfile that tells you the filename of the sound file for that trial. Sound files
are saved to the working directory, and are 2 sec long by default.

Records the sound file from the start of the noise, not the start of the trial.

-- Geoff.Brookshire@gmail.com (5-24-2012)

'''

import sys
import cognac.StimController
import VisionEgg.FlowControl as Flow
import VisionEgg.ParameterTypes as ve_types
import pyaudio
import pygame
from pygame.locals import KEYDOWN, K_RIGHT, K_LEFT, K_ESCAPE, K_RETURN
from struct import pack, unpack
from array import array
import time
import wave

# make a user-defined voice-trigger event
VOICE_TRIGGER_EVENT = pygame.USEREVENT + 1

class VoiceResponse(cognac.StimController.Response): 
    ''' 
    Use in place of a normal cognac.StimController.Response instance.
    Logs RTs from an auditory trigger read.
    '''

    def __init__(self, label, audio_controller): 
        cognac.StimController.Response.__init__(self, label) 

        self.response_type = VOICE_TRIGGER_EVENT
        self.controller = audio_controller
        self.unlogged = ('limit', 'label', 'response_type', 'controller', 'unlogged')


    def record_response(self, t):
        ''' 
        Overwrites the normal Response.record_response method to check
        for a voice-trigger response.

        Store a voice-triggered RT and the name that will be used for
        that trial's soundfile.
        '''

        responses = pygame.event.get(self.response_type) # check for voice trigs
        pygame.event.clear()
        if responses:
            self.filename = responses[0].filename
            self.rt = t - self.ref_time
            return True

        return False


class VoiceTriggerController(Flow.Controller):
    ''' VisionEgg.Controller class to check for voice-trigger events
    and post them to the pygame event queue.

    To use, add an instance of this controller to the visionegg presentation using:
    ...presentation.add_controller(None, None, voice_controller_instance)

    Includes a method for setting the trigger threshold (set_threshold_gui).

    This class reads the audio stream at a rate determined by the sampling
    rate and the chunk size. Each call to stream.read will take this much time:
        (1/RATE) * CHUNK_SIZE  [in seconds per sample]
    If RATE = 44100 and CHUNK_SIZE = 256, you can sample at about 172 Hz.
    If RATE = 44100 and CHUNK_SIZE = 512, you sample at about half that: 86 Hz.

    Increasing the chunk size causes the program to wait for that to return,
    which increases the average frame rate drastically. Keep this small! 
    It's important to check that
    the parameters you're using don't cause the Inter-Frame Interval (IFI)
    to increase over your screen refresh time (usually 16.7 ms). Check this with
    the report that VisionEgg gives when it quits (the histogram at terminal)
    and the VisionEgg.log file. 

    Sound files must be saved using voice_controller_instance.write_soundfiles()
    called from your experiment script! Do this at a time when saving files won't
    interfere with the timing of the stims/responses.

    '''

    FORMAT = pyaudio.paInt16

    def __init__(self, rec_duration=2,
                 threshold=1000,
                 chunk_size=800,
                 rate=44100): 

        # initialize a few important variables
        self.THRESHOLD = threshold  # amplitude that triggers a pygame event
        self.CHUNK_SIZE = chunk_size  # no. of samples to read from stream
        self.RATE = rate  # sampling rate of the audio stream
        self.rec_duration = rec_duration  # how long to record for
        self.rec_onset_time = None # time the present recording began
        self.rec_array = array('h')  # holds the temporary audio data
        self.soundfile_path = 0  # number is converted to a string for filenames
        self.recording = False  # is it recording the stream to disk
        self.sounds_to_save = {} # dict - holds filenames and sounds to save

        pa = pyaudio.PyAudio()  # initialize pyaudio and open an audio stream
        self.sample_width = pa.get_sample_size(self.FORMAT) 
        self.stream = pa.open(format=self.FORMAT, channels=1,
                              rate=self.RATE,
                              input=True, output=False,
                              frames_per_buffer = self.CHUNK_SIZE) 

        Flow.Controller.__init__(self,
            return_type = ve_types.get_type(None),
            eval_frequency = Flow.Controller.EVERY_FRAME,
            temporal_variables = Flow.Controller.TIME_SEC_SINCE_GO)


    def set_threshold_gui(self, display_scale=0.03):
        """ Open up a pygame gui to set the threshold for the voice trigger. 
        The line turns red if a pygame event is detected, i.e. if the threshold
        is exceeded. Use the left and right arrows to avoid having this happen. 
        Quits pygame when finished to avoid interfering with VisionEgg.

        display_scale determines how much space is devoted to amplitude (smaller
        numbers mean that ambient noise fills up less of the scale)

        """ 
        from numpy import mean

        msg = """
        
        Set the voice-trigger threshold.
        Use the right- and left-arrows to adjust the threshold.
        This threshold should only be crossed when you want a response logged.
        Press ESC to quit, or ENTER when you're finished.\n\n\n"""
        print msg

        # initialize pygame for the gui, and quit when finished.
        pygame.init()
        screen = pygame.display.set_mode((800, 300))
        pygame.display.set_caption('Set voice-trigger threshold') 
        screen_center = screen.get_rect().centerx, screen.get_rect().centery 

        old_chunk_size = self.CHUNK_SIZE  # read larger chunks for this.
        self.CHUNK_SIZE = 2048

        threshold_color = [250, 250, 250]  # color of the line marking threshold

        while True: 
            audio_resps = pygame.event.get(VOICE_TRIGGER_EVENT)
            key_resps = pygame.event.get(KEYDOWN)
            pygame.event.clear()

            if audio_resps:  # deal with audio triggers
                # draw the threshold line in red
                threshold_color = [255, 0, 0]

            if key_resps:  # deal with key presses
                press = key_resps[0].key
                if press == K_ESCAPE:  # quit the whole script if ESC is pressed
                    sys.exit()
                    break
                elif press == K_RETURN:
                    print "Threshold is set to", self.THRESHOLD
                    break
                elif press == K_RIGHT:
                    self.THRESHOLD += 10
                elif press == K_LEFT:
                    self.THRESHOLD -= 10

            # if keys are held down, keep moving the threshold
            keys_down = pygame.key.get_pressed()
            if keys_down[K_RIGHT]:
                self.THRESHOLD += 20
            elif keys_down[K_LEFT]:
                self.THRESHOLD -= 20

            # read in the audio stream
            stream_data = self.read_stream() 

            # get the lines ready to draw
            if stream_data:
                mean_vol = [mean(stream_data) * display_scale, screen_center[1]]
                max_vol = [max(stream_data) * display_scale, screen_center[1]]
            else:
                mean_vol = [0, screen_center[1]]
                max_vol = [0, screen_center[1]] 

            # make the threshold line fade from red (triggered) back to white
            for i, val in enumerate(threshold_color):
                if val < 255:
                    threshold_color[i] = val + 5

            # draw everything to the screen
            screen.fill((0, 0, 0))
            xpos = self.THRESHOLD * display_scale
            pygame.draw.line(screen, threshold_color,
                             (xpos, screen_center[1] - 100),
                             (xpos, screen_center[1] + 100),
                             5) 
            pygame.draw.line(screen, (0, 250, 0), mean_vol, max_vol, 5) 
            pygame.display.flip() 

        pygame.quit()  # quit this pygame session when the loop ends
        self.CHUNK_SIZE = old_chunk_size # reset the chunk size for pyaudio

    def record_sound(self, sound_chunk): 
        ''' Add data to the temporary sound array while recording.
        When the recording time is finished, close and store the
        sound data in a dict of all the sound data along with the
        filename which it will be saved with.

        It disrupts timing to save files to disk during the exp.
        Instead, save the sounds in RAM until a point when they
        can be saved without jeopardizing timing. Keep a list of the
        sound chunks to be saved, and write them to disk
        with voice_controller_instance.write_soundfiles().

        '''

        self.rec_array.extend(sound_chunk)  # add present chunk to the sound array

        # if the time is up, close the object and save the file
        rec_time = time.time() - self.rec_onset_time  # duration of present rec. 
        if  rec_time > self.rec_duration: 
            self.stream.stop_stream()  # save CPU power until done saving the file
            self.recording = False
            self.rec_onset_time = None

            # close the recording, save it
            sound_data = pack('<' + ('h' * len(self.rec_array)), *self.rec_array)

            filename = str(self.soundfile_path) + '.wav'
            self.sounds_to_save[filename] = sound_data

            self.rec_array = array('h') # re-initialize the recording array
            self.soundfile_path += 1  # increment soundfile name
            self.stream.start_stream()  # start up the stream again

    def write_soundfiles(self):
        ''' Save the sound data in self.sounds_to_save to disk.

        '''
        for fname, s_data in self.sounds_to_save.iteritems():
            wf = wave.open(fname, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.RATE)
            wf.writeframes(s_data)
            wf.close() 


    def read_stream(self):
        """ Read the audio stream, check for voice triggers, handle any errors.
        Return an array containing sound data.
        """
        stream_data = None

        try:
            x = self.stream.read(self.CHUNK_SIZE)
            stream_data = unpack('<' + ('h' * (len(x)/2)), x) # little endian, signed short
            stream_data = array('h', stream_data) 
            if max(stream_data) > self.THRESHOLD:
                vt_event = pygame.event.Event(VOICE_TRIGGER_EVENT,
                                              {'filename': self.soundfile_path})
                pygame.event.post(vt_event) # send the pygame event
                if not self.recording:
                    self.rec_onset_time = time.time() 
                    self.recording = True

        except IOError, e:  # Not sure why this error occurs, but it does often
            if e[1] == pyaudio.paInputOverflowed:
                print e
                x = '\x00'*16*256*2 #value*format*chunk*nb_channels 

        except Exception, inst: # catch and report other errors
            print type(inst), inst

        return stream_data  # return the array of sound data


    def during_go_eval(self):
        ''' Read the audio stream and check for voice triggers!
        ''' 
        pygame.event.clear() 
        stream_data = self.read_stream() 
        if self.recording and stream_data: # record the data
            self.record_sound(stream_data)


    def between_go_eval(self):
        return None


