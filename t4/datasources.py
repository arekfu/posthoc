# coding: utf-8

from results import XMLResult, CSVResult
from collections import Mapping

class SourceError(Exception):
    """A customized Exception."""
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class DataSource(object):
    pass

def to_datasource(item):
    if isinstance(item, DataSource):
        return item
    else:
        raise Exception('Not implemented yet')

class XMLDataSource(DataSource):
    """Represents a T4 XML output file as a data source."""

    def __init__(self, file_name, score_name, batch_num='last', divide_by_bin=True, **options):
        """Initialize the data source from an XML file.

        Arguments:
        file_name -- name of the XML file (string).
        score_name -- name of the T4 score (string)

        Keyword arguments:
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

        # Here we assume file_name is a valid, well-formed T4 output file
        xml_result = XMLResult(file_name)
        self.result = xml_result.mean_result(
                score_name,
                batch_num=batch_num,
                divide_by_bin=divide_by_bin
                )

        self.xlabel, self.ylabel = xml_result.labels(score_name)

class CSVDataSource(DataSource):
    """Represents a CSV text file as a data source."""

    def __init__(
            self,
            file_name,
            column_spec='1:2',
            xlabel=None,
            ylabel=None,
            comment_chars = '#@',
            delimiter_chars = ' \t',
            **options):
        """Initialize the data source from a CSV file.

        Arguments:
        file_name -- name of the CSV file (string)

        Keyword arguments:
        column_spec -- column-separated string of (zero-based) column indices
        with the following format: 'x:y[:ey[:ex]]'
        xlabel -- label for the x-axis
        ylabel -- label for the y-axis
        comment_chars -- list of characters that introduce comments
        delimiter_chars -- list of delimiter characters
        options -- any additional options (used for plotting)
        """

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a dictionary-like object')
        else:
            self.kwargs = dict()

        # We create the CSVResult object
        csv_result = CSVResult(
                file_name,
                column_spec=column_spec,
                comment_chars=self.kwargs['comment_chars'],
                delimiter_chars=self.kwargs['delimiter_chars']
                )
        self.result = csv_result.result()

        self.xlabel = xlabel
        self.ylabel = ylabel
