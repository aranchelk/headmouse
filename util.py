# coding=utf8

import logging
import collections

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
            logging.info(self.message.format(*summary))
            self.data = []
