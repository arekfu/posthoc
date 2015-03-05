# coding: utf-8

from results import XMLResult, TXTResult, Result
import results
from collections import Mapping
import copy
import numpy as np
import re
import logging

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
        add.result += other.result
        return add

    def __iadd__(self, other):
        self.result += other.result
        return self

    def __sub__(self, other):
        sub = copy.deepcopy(self)
        sub -= other
        return sub

    def __isub__(self, other):
        self.result -= other.result
        return self

    def __mul__(self, other):
        mul = copy.deepcopy(self)
        mul *= other
        return mul

    def __imul__(self, other):
        self.result *= other.result
        return self

    def __div__(self, other):
        div = copy.deepcopy(self)
        div /= other
        return div

    def __idiv__(self, other):
        self.result /= other.result
        return self

    def copy(self):
        return copy.deepcopy(self)

    def __getitem__(self, key):
        new = self.copy()
        new.result = new.result[key]
        return new

    def rebin(self, nbins, mean=True):
        self.result = self.result.rebin(nbins, mean)

    def null(self):
        self.result = Result()
        self.xlabel = self.ylabel = self.label = None

def to_datasource(item):
    """Convert the argument into a datasource.

    This function performs some black magic to guess what type of DataSource
    the input should be converted to.
    """

    if isinstance(item, DataSource):
        return item
    else:
        raise Exception('Not implemented yet')


class XMLDataSource(DataSource):
    """Represents a T4 XML output file as a data source."""

    def __init__(self, file_name, score_name, label=None, batch_num='last', divide_by_bin=True, **options):
        """Initialize the data source from an XML file.

        Arguments:
        file_name -- name of the XML file (string).
        score_name -- name of the T4 score (string)

        Keyword arguments:
        label -- a label for the data source
        batch_num -- the number of the batch.
        divide_by_bin -- whether the score result should be divided by the bin
        size.
        options -- any additional options (used for plotting).
        """

        if not isinstance(file_name, basestring) or not isinstance(score_name, basestring):
            raise SourceError('File name and score name for XMLDataSource must be strings.')

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a dictionary-like object')
        else:
            self.kwargs = dict()

        # Here we hope that file_name is a valid, well-formed T4 output file
        try:
            logger.debug('Trying to open %s as an XMLResult', file_name)
            xml_result = XMLResult(file_name)
        except IOError as e:
            logger.error('Fail: could not open %s as an XMLResult: %s', file_name, e.args)
            self.null()
        else:
            logger.debug('Success: opened %s as an XMLResult', file_name)
            self.result = xml_result.mean_result(
                    score_name,
                    batch_num=batch_num,
                    divide_by_bin=divide_by_bin
                    )

            self.xlabel, self.ylabel = xml_result.labels(score_name)

            self.label = label if label else score_name

class TXTDataSource(DataSource):
    """Represents a text file as a data source."""

    def __init__(
            self,
            file_name,
            parser,
            xlabel=None,
            ylabel=None,
            label=None,
            **options):
        """Initialize the data source from a text file.

        Arguments:
        file_name -- name of the CSV file (string)
        parser -- a callable that accepts as an argument a line of the text
        file and returns None (if the line should be ignored) or a tuple of the
        form (x,y[,ey[,ex]]).

        Keyword arguments:
        xlabel -- label for the x-axis
        ylabel -- label for the y-axis
        label -- label for the data source
        options -- any additional options (used for plotting)
        """

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a dictionary-like object')
        else:
            self.kwargs = dict()

        # We create the TXTResult object
        txt_result = TXTResult(
                file_name,
                parser=parser
                )
        try:
            logger.debug('Trying to open %s as a TXTResult', file_name)
            self.result = txt_result.result()
        except IOError as e:
            logger.error('Fail: could not open %s as a TXTResult: %s', file_name, e.args)
            self.null()
        else:
            logger.debug('Success: opened %s as a TXTResult', file_name)
            self.xlabel = xlabel
            self.ylabel = ylabel
            self.label = label

class CSVDataSource(TXTDataSource):
    """Represents a CSV text file as a data source."""

    class CSVParser(object):
        def __init__(self, column_spec, comment_chars, delimiter_chars, dtype=results.dtype):
            self.column_spec = column_spec
            self.comment_chars = comment_chars
            self.delimiter_chars = delimiter_chars
            self.dtype = dtype

            # extract column indices and verify their number
            self.column_indices = [int(field) for field in self.column_spec.split(':')]
            self.n_indices = len(self.column_indices)
            if self.n_indices<2 or self.n_indices>4:
                raise ValueError('column_indices must contain 2, 3 or 4 indices')

        def __call__(self, line):
            # strip leading and trailing whitespace
            stripped = line.strip()

            # the following line assigns to comment_index the index of the
            # first comment character encountered in the splitted string
            comment_index = next(
                    (i for (i, char) in enumerate(stripped) for comment_char in self.comment_chars if char==comment_char),
                    None
                    )
            non_comment = stripped[:comment_index]

            # split the string
            splitted = re.split('[' + self.delimiter_chars + ']+', non_comment)

            # skip blank lines
            if not splitted:
                return None

            try:
                x = self.dtype(splitted[self.column_indices[0]])
                y = self.dtype(splitted[self.column_indices[1]])
                if self.n_indices>=3:
                    ey = self.dtype(splitted[self.column_indices[2]])
                    if self.n_indices==4:
                        ex = self.dtype(splitted[self.column_indices[3]])
                        parsed = (x,y,ey,ex)
                    else:
                        parsed = (x,y,ey)
                else:
                    parsed = (x,y)
            except IndexError as error:
                error.args = ('Column specification out of range. Check your column_spec argument. I choked on this line:\n' + line, )
                raise error

            return parsed

    def __init__(
            self,
            file_name,
            column_spec='0:1',
            comment_chars='#@',
            delimiter_chars=' \t',
            xlabel=None,
            ylabel=None,
            label=None,
            **options):
        """Initialize the data source from a CSV file.

        Arguments:
        file_name -- name of the CSV file (string)

        Keyword arguments:
        column_spec -- column-separated string of (zero-based) column indices
        with the following format: 'x:y[:ey[:ex]]'
        xlabel -- label for the x-axis
        ylabel -- label for the y-axis
        label -- label for the data source
        comment_chars -- list of characters that introduce comments
        delimiter_chars -- list of delimiter characters
        options -- any additional options (used for plotting)
        """

        parser = self.CSVParser(column_spec, comment_chars, delimiter_chars)
        TXTDataSource.__init__(self, file_name, parser, xlabel, ylabel, label, **options)
