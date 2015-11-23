# coding: utf-8

import copy
import logging

from ..results.result import Result

# set up logging
logger = logging.getLogger(__name__)


class SourceError(Exception):
    """A customized Exception."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class DataSource(object):
    """Base class for all the DataSource types."""

    def __add__(self, other):
        add = copy.deepcopy(self)
        add += other
        return add

    def __iadd__(self, other):
        if isinstance(other, DataSource):
            self.result += other.result
        else:
            self.result += other
        return self

    def __sub__(self, other):
        sub = copy.deepcopy(self)
        sub -= other
        return sub

    def __isub__(self, other):
        if isinstance(other, DataSource):
            self.result -= other.result
        else:
            self.result -= other
        return self

    def __mul__(self, other):
        mul = copy.deepcopy(self)
        mul *= other
        return mul

    def __imul__(self, other):
        if isinstance(other, DataSource):
            self.result *= other.result
        else:
            self.result *= other
        return self

    def __div__(self, other):
        div = copy.deepcopy(self)
        div /= other
        return div

    def __idiv__(self, other):
        if isinstance(other, DataSource):
            self.result /= other.result
        else:
            self.result /= other
        return self

    def copy(self):
        return copy.deepcopy(self)

    def __getitem__(self, key):
        new = self.copy()
        new.result = new.result[key]
        return new

    def rebin(self, nbins, mean=True):
        self.result.rebin(nbins, mean)

    def rescale_edges(self, factor, rescale_contents=True):
        self.result.rescale_edges(factor, rescale_contents)

    def rescale_errors(self, factor):
        self.result.rescale_errors(factor)

    def null(self):
        self.result = Result()
        self.xlabel = self.ylabel = self.label = None

    def append_bin(self, edge=None, content=0., error=0., xerror=0.):
        self.result.append_bin(edge, content, error, xerror)

    def chop(self, threshold=1e-30):
        self.result.chop(threshold)


def to_datasource(item):
    """Convert the argument into a datasource.

    This function performs some black magic to guess what type of DataSource
    the input should be converted to.
    """

    if isinstance(item, DataSource):
        return item
    else:
        raise Exception('Not implemented yet')
