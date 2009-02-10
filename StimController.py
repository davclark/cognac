"""StimController.py is a simple controller designed to show stimuli at specific
times.  A reference for usage is in luminanceCompression2.py

The intended usage of this class is to present a sequence of fixed stimuli, and
log the timings and keyboard responses to them.  Adaptive experiments should
simply instantiate a new StimulusController for each trial, for example -
adaptive logic would be out of place here.

Now that things have been made a little more general, you could do adaptive
stuff... but its not obvious."""

from datetime import date
import time
from copy import copy
from csv import DictWriter

from SimpleVisionEgg import SimpleVisionEgg
import pygame


class RelTime:
    units = 'seconds'
    ref = 'trial_start'
    offset = 0

    def __init__(self, t):
        if isinstance(t, str):
            vals = t.split('+', 1)
            self.ref = vals[0]
            try:
                self.offset = float(vals[1])
            except IndexError:
                pass
        elif isinstance(t, (int, float)):
            self.offset = t
        elif isinstance(t, (list, tuple)):
            self.ref, self.offset = t

    def add(self, t):
        if not isinstance(t, (int, float)):
            raise TypeError('RelTime.add(%s) takes only int or float' % t)

        retval = RelTime(t)
        retval.ref = self.ref
        retval.offset += self.offset

        return retval


class Response:
    label = None
    expected = None
    limit = None
    ref_time = None
    response = None
    rt = None
    response_type = pygame.KEYDOWN
    buttonbox = None
    timelimit = None

    unlogged = ('limit', 'label', 'response_type')

    # We just use pygame directly now
    # @staticmethod
    # def get_response(t):
    #     '''This should be overridden with a function with the following
    #     signature: (resp, timestamp) = fcn(t) 
    #     This can be done more nicely by inheritence, or more aggressively by
    #     Response.get_response = staticmethod(fcn)
    #     Note that if you override record_response such that it doesn't call this
    #     function, you don't need to worry about it anymore!'''
    #     raise NotImplementedError('Response needs a get_response fcn!')

    def __init__(self, label, expected=None, limit=None, buttonbox=None, timelimit=None):
        '''We're careful here so that our __dict__ will have only entries we've
        actually updated
        buttonbox is an instance of parallel.respbox.Respbox()
        timelimit is the trial length, and stops the buttonbox loop. only needed 
        if buttonboxes are used.'''
        self.label = label
        if expected is not None:
            self.expected = expected
        if limit is not None:
            self.limit = limit
        if buttonbox is not None:
            self.buttonbox = buttonbox
            self.limit = [0,2,4,8,16]
        if timelimit is not None:
            self.timelimit = timelimit

    def record_response(self, t):
        '''This could be overridden to do extended feedback, like data entry
        or updating feedback during response collection'''
        if self.buttonbox and self.timelimit:
            response = 0
            while response == 0 and t <= self.ref_time + self.timelimit:
                response = self.buttonbox.readBox()
            self.rt = t - self.ref_time
            # did i get the logic of this right?
            if response:
                return True
            return False

        else:
            responses = pygame.event.get(self.response_type)
            pygame.event.clear()
            if responses:
                # If you want something more sophisticated - write a subclass!
                first_response = pygame.key.name(responses[0].key)
                if not self.limit or first_response in self.limit:
                    self.response = first_response
                    self.rt = t - self.ref_time
                    return True

            return False

    def response_time(self):
        '''This is trivial, but might not be with other response types'''
        try:
            return self.ref_time + self.rt
        except TypeError:
            return None


class Event:
    '''A thin wrapper around VisionEgg stimuli.  Most of the code is now for
    backwards compatibility with '''

    # Usually a VisionEgg stimulus
    target = None

    # Computed from parms
    start = None
    stop = None
    parms = None
    # Things to log
    log = None
    # Responses to get
    response = None

    @classmethod
    def from_yaml(cls, yaml_event, target_dict=None):
        target, parms = yaml_event.items()[0]
        parms = copy(parms)
        if target_dict:
            target = target_dict[target]

        try: 
            response_yaml = parms['response']
        except KeyError:
            pass
        else:
            try:
                # New way - bombs out if no 'label'
                parms['response'] = Response(**response_yaml)
            except TypeError:
                # Old way - should only be a singleton dict
                label, expected = response_yaml.items()[0]
                parms['response'] = Response(label, expected=expected)

        return cls(target, **parms)

    def __init__(self, target, start, stop=None, duration=None,
                 log=None, response=None, **parms):
        '''Currently doesn't check to see that stop or duration is specified.
        This leads to an error in RelTime.'''
        self.target = target
        self.start = RelTime(start)
        if stop is not None:
            self.stop = RelTime(stop)
        else:
            self.stop = self.start.add(duration)

        parms.setdefault('on', True)
        self.parms = parms
        self.log = log
        self.response = response
        
    def activate(self):
        self.target.set(**self.parms)
        return self

    def deactivate(self):
        self.target.set(on=False)
        return self


class Trial:
    curr_response = None
    events = None # stimuli, etc.
    active_events = None
    # The actual log of responses and stuff
    log = None

    @classmethod
    def from_yaml(cls, yaml_events, event_dict=None):
        return cls([Event.from_yaml(y, event_dict) for y in yaml_events])

    def __init__(self, events):
        '''For now this initializes from a yaml representation.  Ultimately, we
        want to avoid this. Note that this doesn't require the yaml parser -
        just it's output or something equivalent.
        
        events should be a list of 'Event's'''
        self.events = events
        self.active_events = []
        self.log = {}    

    def event_ready(self, event_time, t):
        try:
            ref_time = self.log[event_time.ref]
        except KeyError:
            # The event hasn't even been registered yet!
            return False

        try:
            # Check if this is a class with a response_time, otherwise we assume
            # it's simply a number
            ref_time = ref_time.response_time()
        except AttributeError:
            pass

        if ref_time is None:
            return False
        else:
            return t - ref_time >= event_time.offset

    def activate_events(self, t):
        # We can potentially activate several events if they are all ready
        while self.events:
            if self.event_ready(self.events[0].start,  t):
                event = self.events.pop(0)
                event.activate()
                self.active_events.append(event)

                if event.log:
                    for log_k, log_v in event.log.items():
                        self.log[log_k] = log_v
                if event.response:
                    # Make sure we only get inputs after the start of the
                    # response period
                    pygame.event.clear()

                    event.response.ref_time = t
                    self.log[event.response.label] = event.response
                    self.curr_response = event.response
            else:
                break

    def log_response(self, t):
        if self.curr_response and \
                self.curr_response.record_response(t):
            self.curr_response = None

    def deactivate_events(self, t):
        # We make a copy so we can modify the real list
        for event in copy(self.active_events):
            if self.event_ready(event.stop, t):
                event.deactivate()
                self.active_events.remove(event)

    def done(self):
        return not (self.events or self.active_events)


class StimController:
    # Stimulus related attributes
    trials = None
    pause_event = None

    # SimpleVisionEgg instance
    vision_egg = None

    # Attribs for keeping track of experiment
    go_duration = ('forever', )
    state = None
    trials_to_run = 0 # == run all of them


    def __init__(self, trials, vision_egg, pause_event=None):
        """vision_egg is an instance of SimpleVisionEgg
        pause_event is an Event which will be shown at the beginning of
        every stim_controller.run_trials loop."""
            
        self.trials = trials
        self.vision_egg = vision_egg
        self.pause_event = pause_event

        self.state = self.state_generator()
        self.state.next()

        self.vision_egg.set_functions(update=self.update, 
                                      pause_update=self.pause_update)

    def run_trials(self, num=0):
        self.trials_to_run = num
        self.vision_egg.go()

    def compute_go_duration(self, units='seconds'):
        """This should run through the trials, find the latest stimulus and add
        this info up, putting it in go_duration"""
        go_duration = 0
        for trial in self.trials:
            max_time = 0
            for event in trial.events:
                if self.stop > max_time:
                    max_time = self.stop

            go_duration += max_time

        self.go_duration = (go_duration, units)

    def update(self, t):
        """Wrapper to adapt the state generator into a regular function"""
        self.state.send(t)

    def pause_update(self):
        """Simple function to set the screen displaying some text"""
        if self.pause_event:
            self.pause_event.activate()

    def state_generator(self):
        # Initial yeild to get us into accepting "send" calls
        t = yield

        trial_num = 0
        for trial in self.trials:
            trial_num += 1
            if self.pause_event:
                self.pause_event.deactivate()
            trial.log['trial_start'] = t

            # Note that the order of activates, deactivates and yields is
            # critical for instantaneous stimuli to appear properly (or at all)
            while True:
                trial.deactivate_events(t)
                trial.log_response(t)
                trial.activate_events(t)
                if trial.done():
                    break
                t = yield

            if trial_num == self.trials_to_run:
                trial_num = 0
                self.vision_egg.pause()
                t = yield

        # we're done!
        self.vision_egg.pause()
        yield

    def loglines(self):
        '''Generator that returns the lines of a log file in list format, this
        allows for easy programmatic processing, or otherwise feeding to a
        csv.Writer
        
        This function takes everything and puts it in one big table - padded
        with Nones for missing items.  You may want to use something else if
        your log would be relatively "sparse"'''
        def conv_log(items):
            '''This converts our responses to a flat dict'''
            retval = {} 
            for label, obj in items:
                try:
                    # For greater generality, this could be a method of
                    # Response...
                    for param, param_value in obj.__dict__.items():
                        if param not in obj.unlogged:
                            comp_key = '.'.join((label, param))
                            retval[comp_key] = param_value
                except AttributeError:
                    # It's just a number or string (we hope)
                    retval[label] = obj 

            return retval

        log = []
        header = set()
        for t in self.trials:
            log_line = conv_log(t.log.items())
            log.append(log_line) 
            header.update(log_line)

        header = sorted(header)

        return header, log

    def writelog(self, f):
        '''Write log to f - f can be a filename or a file opened for writing'''
        header, log = self.loglines()
        try:
            dw = DictWriter(f, header)
        except TypeError:
            dw = DictWriter(open(f, 'w'), header)

        dw.writer.writerow(header)
        dw.writerows(log)

    def getOutputFilename(self, subjectName, experimentname):
        # function to avoid overwriting data
        # writes a .datalog file that holds subject and testing date for each block
        # This is altered slightly from john's simpleComplex_OneGo.py  -geoff

        sub_date = '%s: %s\n'%(subjectName,str(date.fromtimestamp(time.time())))
        try:
            datalog = open(experimentname + '.datalog','r')
            dataloglines = datalog.readlines()
            datalog.close()
        except:
            dataloglines = []

        outputFileName = '%s_%d.csv' % \
                (subjectName, 1 + ''.join(dataloglines).count(subjectName))
        datalog = open(experimentname + '.datalog', 'a')
        datalog.write(sub_date)
        datalog.close()

        return outputFileName

