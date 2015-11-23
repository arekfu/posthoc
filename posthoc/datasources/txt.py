# coding: utf-8

from collections import Mapping
import re
import logging

from ..results import result
from ..results.txt import TXTResult
from .datasource import DataSource, SourceError

# set up logging
logger = logging.getLogger(__name__)


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
                raise SourceError('The options argument must be a '
                                  'dictionary-like object')
        else:
            self.kwargs = {}

        # We create the TXTResult object
        txt_result = TXTResult(file_name, parser=parser)
        try:
            logger.debug('Trying to open %s as a TXTResult', file_name)
            self.result = txt_result.result()
        except IOError as e:
            logger.error('Fail: could not open %s as a TXTResult: %s',
                         file_name, e.args)
            self.null()
        else:
            logger.debug('Success: opened %s as a TXTResult', file_name)
            self.xlabel = xlabel
            self.ylabel = ylabel
            self.label = label


class CSVDataSource(TXTDataSource):
    """Represents a CSV text file as a data source."""

    class CSVParser(object):
        def __init__(self, column_spec, comment_chars, delimiter_chars,
                     dtype=result.DTYPE):
            self.column_spec = column_spec
            self.comment_chars = comment_chars
            self.delimiter_chars = delimiter_chars
            self.dtype = dtype

            # extract column indices and verify their number
            self.column_indices = [int(f) for f in self.column_spec.split(':')]
            self.n_indices = len(self.column_indices)
            if self.n_indices < 2 or self.n_indices > 4:
                raise ValueError('column_indices must contain 2, 3 or 4 '
                                 'indices')

        def __call__(self, line):
            # strip leading and trailing whitespace
            stripped = line.strip()

            # the following line assigns to comment_index the index of the
            # first comment character encountered in the splitted string
            comment_index = next(
                (i for (i, char) in enumerate(stripped)
                    for comment_char in self.comment_chars
                    if char == comment_char),
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
                if self.n_indices >= 3:
                    ey = self.dtype(splitted[self.column_indices[2]])
                    if self.n_indices == 4:
                        ex = self.dtype(splitted[self.column_indices[3]])
                        parsed = (x, y, ey, ex)
                    else:
                        parsed = (x, y, ey)
                else:
                    parsed = (x, y)
            except IndexError as error:
                error.args = ('Column specification out of range. Check your '
                              'column_spec argument. I choked on this line:\n'
                              + line,
                              )
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
        TXTDataSource.__init__(self, file_name, parser, xlabel, ylabel, label,
                               **options)
