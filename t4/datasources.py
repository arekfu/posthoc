# coding: utf-8

from results import XMLResult, TXTResult, Result
import results
from collections import Mapping
import copy
import numpy as np
import re
import logging

try:
    import ROOT
    from results import ROOTResult
    HAS_ROOT = True
except ImportError:
    HAS_ROOT = False

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

xml_result_cache = dict()

class XMLDataSource(DataSource):
    """Represents a T4 XML output file as a data source."""

    def __init__(self, file_name, score_name, label=None, batch_num='last', region_id=1, divide_by_bin=True, **options):
        """Initialize the data source from an XML file.

        Arguments:
        file_name -- name of the XML file (string).
        score_name -- name of the T4 score (string)

        Keyword arguments:
        label -- a label for the data source
        batch_num -- the number of the batch.
        region_id -- the ID of the score region
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
            if file_name in xml_result_cache:
                logger.debug('Using cached XMLResult object for %s', file_name)
                xml_result = xml_result_cache[file_name]
            else:
                logger.debug('Trying to open %s as an XMLResult', file_name)
                xml_result = XMLResult(file_name)
                xml_result_cache[file_name] = xml_result
        except IOError as e:
            logger.error('Fail: could not open %s as an XMLResult: %s', file_name, e.args)
            self.null()
        else:
            logger.debug('Success: opened %s as an XMLResult', file_name)
            self.result = xml_result.mean_result(
                    score_name,
                    batch_num=batch_num,
                    region_id=region_id,
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
            if not any(s for s in splitted):
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

if HAS_ROOT:
    root_result_cache = dict()

    class ROOTDataSource(DataSource):
        """Represents a ROOT output file as a data source."""

        def __init__(self, file_name, histo_name, label=None, **options):
            """Initialize the data source from an XML file.

            Arguments:
            file_name -- name of the .root file (string).
            histo_name -- name of the histogram (string)

            Keyword arguments:
            label -- a label for the data source
            size.
            options -- any additional options (used for plotting).
            """

            if not isinstance(file_name, basestring) or not isinstance(histo_name, basestring):
                raise SourceError('File name and histogram name for ROOTDataSource must be strings.')

            if options:
                if isinstance(options, Mapping):
                    self.kwargs = options.copy()
                else:
                    raise SourceError('The options argument must be a dictionary-like object')
            else:
                self.kwargs = dict()

            # Here we hope that file_name is a valid, well-formed ROOT file
            try:
                logger.debug('Trying to open %s as an ROOTResult', file_name)
                if file_name in root_result_cache:
                    logger.debug('Using cached ROOTResult object for %s', file_name)
                    root_result = root_result_cache[file_name]
                else:
                    logger.debug('Trying to open %s as an ROOTResult', file_name)
                    root_result = ROOTResult(file_name)
                    root_result_cache[file_name] = root_result
            except IOError as e:
                logger.error('Fail: could not open %s as an ROOTResult: %s', file_name, e.args)
                self.null()
            else:
                logger.debug('Success: opened %s as an ROOTResult', file_name)
                self.result = root_result.result(histo_name)

                self.xlabel, self.ylabel = root_result.labels(histo_name)

                self.label = label if label else histo_name

