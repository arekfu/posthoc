# coding: utf-8

from collections import Mapping
import logging

from ..results.t4 import T4XMLResult, T4TXTResult
from .datasource import DataSource, SourceError


# set up logging
LOGGER = logging.getLogger(__name__)


_T4XML_RESULT_CACHE = {}
_T4TXT_RESULT_CACHE = {}


class T4XMLDataSource(DataSource):
    """Represents a T4 XML output file as a data source."""

    def __init__(self, file_name, score_name, label=None, batch_num='last',
                 region_id=1, cell=(0,0,0), time_step=0, divide_by_bin=True,
                 **options):
        """Initialize the data source from an XML file.

        Arguments:
        file_name -- name of the XML file (string).
        score_name -- name of the T4 score (string)

        Keyword arguments:
        label -- a label for the data source
        batch_num -- the number of the batch.
        region_id -- the ID of the score region
        cell -- for extended meshes, a 3-tuple giving x, y and z indices of the
                requested energy distribution.
        time_step -- the index of the requested time step
        divide_by_bin -- whether the score result should be divided by the bin
                         size.
        options -- any additional options (used for plotting).
        """

        if not isinstance(file_name, str) or not isinstance(score_name, str):
            raise SourceError('File name and score name for T4XMLDataSource '
                              'must be strings.')

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a '
                                  'dictionary-like object')
        else:
            self.kwargs = dict()

        # Here we hope that file_name is a valid, well-formed T4 output file
        try:
            if file_name in _T4XML_RESULT_CACHE:
                LOGGER.debug('Using cached T4XMLResult object for %s',
                             file_name)
                t4xml_result = _T4XML_RESULT_CACHE[file_name]
            else:
                LOGGER.debug('Trying to open %s as a T4XMLResult', file_name)
                t4xml_result = T4XMLResult(file_name)
                _T4XML_RESULT_CACHE[file_name] = t4xml_result
        except IOError as e:
            LOGGER.error('Fail: could not open %s as a T4XMLResult: %s',
                         file_name, e.args)
            self.null()
        else:
            LOGGER.debug('Success: opened %s as a T4XMLResult', file_name)
            self.result = t4xml_result.mean_result(
                score_name,
                batch_num=batch_num,
                region_id=region_id,
                cell=cell,
                time_step=time_step,
                divide_by_bin=divide_by_bin
                )
            LOGGER.debug('Parsed XML, result is:')
            LOGGER.debug(self.result)

            self.xlabel, self.ylabel = t4xml_result.labels(score_name)

            self.label = label if label else score_name

class T4XMLBatchDataSource(DataSource):
    """Represents a T4 XML output file as a data source."""

    def __init__(self, file_name, score_name, label=None, batch_num='last',
                 region_id=1, cell=(0,0,0,0), divide_by_bin=True, **options):
        """Initialize the data source from an XML file.

        Arguments:
        file_name -- name of the XML file (string).
        score_name -- name of the T4 score (string)

        Keyword arguments:
        label -- a label for the data source
        batch_num -- the number of the batch.
        region_id -- the ID of the score region
        cell -- for extended meshes, a 3-tuple giving x, y and z indices of the
                requested energy distribution.
        time_step -- the index of the requested time step
        divide_by_bin -- whether the score result should be divided by the bin
                         size.
        options -- any additional options (used for plotting).
        """

        if not isinstance(file_name, str) or not isinstance(score_name, str):
            raise SourceError('File name and score name for T4XMLDataSource '
                              'must be strings.')

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a '
                                  'dictionary-like object')
        else:
            self.kwargs = dict()

        # Here we hope that file_name is a valid, well-formed T4 output file
        try:
            if file_name in _T4XML_RESULT_CACHE:
                LOGGER.debug('Using cached T4XMLResult object for %s',
                             file_name)
                t4xml_result = _T4XML_RESULT_CACHE[file_name]
            else:
                LOGGER.debug('Trying to open %s as a T4XMLResult', file_name)
                t4xml_result = T4XMLResult(file_name)
                _T4XML_RESULT_CACHE[file_name] = t4xml_result
        except IOError as e:
            LOGGER.error('Fail: could not open %s as a T4XMLResult: %s',
                         file_name, e.args)
            self.null()
        else:
            LOGGER.debug('Success: opened %s as a T4XMLResult', file_name)
            self.result = t4xml_result.batch_result(
                score_name,
                batch_num=batch_num,
                region_id=region_id,
                cell=cell,
                time_step=time_step,
                divide_by_bin=divide_by_bin
                )
            LOGGER.debug('Parsed XML, result is:')
            LOGGER.debug(self.result)

            #self.xlabel, self.ylabel = t4xml_result.labels(score_name)

            self.label = label if label else score_name


class T4TXTDataSource(DataSource):
    """Represents a T4 text output file as a data source."""

    def __init__(self, file_name, score, region_rank, label=None,
                 batch_num='last', divide_by_bin=True, **options):
        """Initialize the data source from an XML file.

        Arguments:
        file_name -- name of the result file (string).
        score -- name of the score (string) or its rank as an int
        region_rank -- the rank of the score region

        Keyword arguments:
        label -- a label for the data source
        batch_num -- the number of the batch.
        divide_by_bin -- whether the score result should be divided by the bin
                         size.
        options -- any additional options (used for plotting).
        """

        if not isinstance(file_name, str):
            raise SourceError('File name for T4TXTDataSource '
                              'must be a string.')

        if not isinstance(score, str) and not isinstance(score, int):
            raise SourceError('Score for T4TXTDataSource '
                              'must be a string or an int.')

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a '
                                  'dictionary-like object')
        else:
            self.kwargs = dict()

        # Here we hope that file_name is a valid, well-formed T4 output file
        try:
            if (file_name, batch_num) in _T4TXT_RESULT_CACHE:
                LOGGER.debug('Using cached T4TXTResult object for %s',
                             file_name)
                t4txt_result = _T4TXT_RESULT_CACHE[(file_name, batch_num)]
            else:
                LOGGER.debug('Trying to open %s as a T4TXTResult', file_name)
                t4txt_result = T4TXTResult(file_name, batch_num)
                _T4TXT_RESULT_CACHE[(file_name, batch_num)] = t4txt_result
        except IOError as e:
            LOGGER.error('Fail: could not open %s as a T4TXTResult: %s',
                         file_name, e.args)
            self.null()
        else:
            LOGGER.debug('Success: opened %s as a T4TXTResult', file_name)
            self.result = t4txt_result.result(
                score,
                region_rank,
                divide_by_bin=divide_by_bin
                )
            LOGGER.debug('Parsed TXT, result is:')
            LOGGER.debug(self.result)

            self.label = label if label else score
