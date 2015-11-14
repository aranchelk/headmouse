# coding=utf8

import logging
logger = logging.getLogger(__name__)
import collections
import time

def prep_gen(func):
    '''
    Decorator taking care of initial next() call to "sending" generators

    From PEP-342
    http://www.python.org/dev/peps/pep-0342/
    '''
    def wrapper(*args,**kw):
        gen = func(*args, **kw)
        next(gen)
        return gen
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__  = func.__doc__
    return wrapper


class Every_n:
    def __init__(self, frequency, inner_function, send_skip_count=False):
        if frequency < 1:
            raise ValueError("Frequencies < 1 don't have meaning in every_n, read as every 1st time, every 2nd time...")

        self.inner_function = inner_function
        self.frequency = frequency
        self.counter = 0
        self.send_skip_count = send_skip_count

    def send(self, *args, **kwargs):
        if self.send_skip_count:
            kwargs['skip_count'] = self.frequency

        if self.counter + 1 >= self.frequency:
            self.counter = 0
            return self.inner_function(*args, **kwargs)
        else:
            self.counter += 1
            return None

    def next(self):
        return self.send()


def simple_fps():
    last_time = None
    fps = None
    frames = 1

    while True:
        current_time = float(time.time())
        if last_time is not None:
            fps = 1.0 / (current_time - last_time)
        else:
            fps = 0.0

        yield fps
        last_time = current_time


class Stats(collections.defaultdict):
    '''
    Collect stats to be logged only every *n* frames
    '''
    @classmethod
    def average(cls, data):
        return sum(data) / len(data)
    @classmethod
    def sum(cls, data):
        return sum(data)
    @classmethod
    def median(cls, data):
        return data[int(len(data) / 2)]
    @classmethod
    def quartiles(cls, data):
        return [min(data), data[int(len(data)/4)], data[int(len(data) / 2)], data[int(3 * len(data) / 4)], max(data)]
    @classmethod
    def average_delta(cls, data):
        return cls.average([a - b for a, b in zip(data[1:], data[:-1])])
    @classmethod
    def inverse_average_delta(cls, data):
        return 1.0 / cls.average([a - b for a, b in zip(data[1:], data[:-1])])
    @classmethod
    def interval_delta(cls, data):
        return data[-1] - data[0]
    @classmethod
    def normalized_interval_delta(cls, data):
        return (data[-1] - data[0]) / len(data)
    @classmethod
    def inverse_normalized_interval_delta(cls, data):
        return float(len(data)) / (data[-1] - data[0])
    def __init__(self, f, msg="{}", interval=10):
        self.interval = interval
        self.data = []
        self.func = f
        self.message = msg
    def push(self, datum):
        self.data.append(datum)
        if len(self.data) == self.interval:
            summary = self.func(self.data)
            summary = [summary] if not hasattr(summary, '__iter__') else summary
            logger.info(self.message.format(*summary))
            self.data = []
